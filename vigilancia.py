import cv2
import time
import datetime
import os
import libcamera
from picamera2 import Picamera2

# --- CONFIGURACIÓN ---
PATH_NAS = "/mnt/grabaciones_camara/"
MIN_AREA = 5000                # Sensibilidad: área mínima en píxeles
DURACION_CLIP = 10             # Segundos a grabar por video
FPS = 10.0                     # FPS de grabación (Picamera2 suele ir más fluido pero ajustamos salida)

# Verificar directorio
if not os.path.exists(PATH_NAS):
    try:
        os.makedirs(PATH_NAS)
    except OSError as e:
        print(f"Error al crear directorio {PATH_NAS}: {e}")
        exit(1)

def main():
    print("Iniciando Sistema de Vigilancia con Picamera2...")

    # 1. Configuración de Picamera2
    try:
        picam2 = Picamera2()
        # Configuración similar a los ejemplos: 640x480 para procesar rápido
        config = picam2.create_preview_configuration(
            main={"size": (640, 480), "format": "RGB888"},
            transform=libcamera.Transform(vflip=True)
        )
        picam2.configure(config)
        picam2.start()
        print("Cámara iniciada correctamente.")
    except Exception as e:
        print(f"Error fatal al iniciar la cámara: {e}")
        return

    # Esperar a que la cámara se estabilice
    time.sleep(2)

    fondo = None
    grabando = False
    tiempo_inicio_grabacion = 0
    out = None

    try:
        while True:
            # 2. Captura de frame
            # capture_array() devuelve un array numpy (BGR o RGB según config)
            # En config pusimos RGB888, pero OpenCV usa BGR.
            # Picamera2 por defecto en capture_array suele dar BGR si no se especifica lo contrario o saca lo que hay.
            # Verificaremos: create_preview_configuration con "format": "RGB888" da RGB. OpenCV necesita BGR.
            # Hacemos conversión o ajustamos config. 
            # Mejor dejar que capture y convertir si es necesario, o capturar BGR.
            # Probaremos capturar y convertir.
            
            frame = picam2.capture_array()
            # Picamera2 devuelve RGB por defecto en configuraciones simples si no se toca, pero aquí forzamos RGB.
            # OpenCV usa BGR.
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            # 3. Procesamiento de imagen
            gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            # Desenfoque para reducir ruido
            gris = cv2.GaussianBlur(gris, (21, 21), 0)

            if fondo is None:
                fondo = gris
                continue

            # Diferencia absoluta
            diferencia = cv2.absdiff(fondo, gris)
            
            # Umbralizar
            _, umbral = cv2.threshold(diferencia, 25, 255, cv2.THRESH_BINARY)
            umbral = cv2.dilate(umbral, None, iterations=2)

            # Contornos
            contornos, _ = cv2.findContours(umbral.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            movimiento = False
            for c in contornos:
                if cv2.contourArea(c) < MIN_AREA:
                    continue
                movimiento = True
                break

            # 4. Lógica de grabación
            if movimiento and not grabando:
                grabando = True
                tiempo_inicio_grabacion = time.time()
                
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = os.path.join(PATH_NAS, f"alerta_{timestamp}.avi")
                
                print(f"Movimiento detectado! Grabando en: {filename}")
                
                # Configurar VideoWriter
                # Usamos MJPG o XVID
                fourcc = cv2.VideoWriter_fourcc(*'XVID')
                # Tamaño debe coincidir con el frame (640x480)
                height, width, _ = frame.shape
                out = cv2.VideoWriter(filename, fourcc, FPS, (width, height))

            if grabando:
                if out is not None:
                    out.write(frame)
                
                # Chequear duración
                if time.time() - tiempo_inicio_grabacion > DURACION_CLIP:
                    grabando = False
                    if out is not None:
                        out.release()
                        out = None
                    print("Grabación finalizada. Volviendo a vigilar.")
                    # Actualizar fondo para evitar falsos positivos residuales
                    fondo = gris

            # 5. Visualización
            estado_texto = "GRABANDO" if grabando else "VIGILANDO"
            color_texto = (0, 0, 255) if grabando else (0, 255, 0)
            
            cv2.putText(frame, f"Estado: {estado_texto}", (10, 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color_texto, 2)
            
            # Dibujar rectángulos en movimiento
            if movimiento:
                 for c in contornos:
                    if cv2.contourArea(c) >= MIN_AREA:
                        (x, y, wa, ha) = cv2.boundingRect(c)
                        cv2.rectangle(frame, (x, y), (x + wa, y + ha), (0, 255, 0), 2)

            cv2.imshow("Monitor PI", frame)

            # Salir con 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        pass
    finally:
        print("Cerrando sistema...")
        if out is not None:
            out.release()
        picam2.stop()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()