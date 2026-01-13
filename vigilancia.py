import cv2
import time
import datetime
import threading
import os

# --- CONFIGURACIÓN ---
PATH_NAS = "/mnt/nas_videos/"  # La ruta que configuramos en el fstab
MIN_AREA = 5000                # Sensibilidad: área mínima en píxeles para detectar movimiento
DURACION_CLIP = 10             # Cuántos segundos grabar por cada detección
FPS = 20.0                     # Frames por segundo del video de salida

def grabar_video(nombre_archivo, ancho, alto):
    """ Función que se ejecuta en un hilo aparte para grabar el clip """
    print(f"DEBUG: Iniciando hilo de grabación en {nombre_archivo}")
    
    # Definir el codec y crear el objeto VideoWriter
    # 'XVID' genera archivos .avi compatibles con casi todo
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(nombre_archivo, fourcc, FPS, (ancho, alto))
    
    # Captura secundaria para el hilo de grabación
    cap_hilo = cv2.VideoCapture(0)
    
    start_time = time.time()
    while int(time.time() - start_time) < DURACION_CLIP:
        ret, frame = cap_hilo.read()
        if ret:
            out.write(frame)
        else:
            break
            
    cap_hilo.release()
    out.release()
    print(f"DEBUG: Grabación finalizada con éxito.")

# --- INICIO DEL PROGRAMA PRINCIPAL ---
cap = cv2.VideoCapture(0)
time.sleep(2) # Tiempo para que la cámara se ajuste a la luz

fondo = None
esta_grabando = False

print("Sistema NAS de vigilancia activado. Presiona 'q' para salir.")

try:
    while True:
        ret, frame = cap.read()
        if not ret: break

        # 1. Preprocesamiento: Convertir a gris y desenfocar
        # El desenfoque elimina el "ruido" electrónico de la cámara
        gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gris = cv2.GaussianBlur(gris, (21, 21), 0)

        # Si es el primer frame, lo guardamos como referencia del fondo
        if fondo is None:
            fondo = gris
            continue

        # 2. Diferencia entre el fondo estático y el frame actual
        diferencia = cv2.absdiff(fondo, gris)
        umbral = cv2.threshold(diferencia, 25, 255, cv2.THRESH_BINARY)[1]
        umbral = cv2.dilate(umbral, None, iterations=2)

        # 3. Encontrar contornos del movimiento
        contornos, _ = cv2.findContours(umbral.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        movimiento_detectado = False
        for c in contornos:
            if cv2.contourArea(c) < MIN_AREA:
                continue
            movimiento_detectado = True
            break

        # 4. Gestión de grabación por hilos
        if movimiento_detectado and not esta_grabando:
            esta_grabando = True
            
            # Crear nombre de archivo con fecha y hora
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_final = os.path.join(PATH_NAS, f"video_{timestamp}.avi")
            
            # Obtener dimensiones de la cámara
            ancho = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            alto = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            # Lanzar el hilo
            t = threading.Thread(target=grabar_video, args=(nombre_final, ancho, alto))
            t.start()

        # Comprobar si el hilo ha terminado para permitir una nueva grabación
        if esta_grabando and 't' in locals() and not t.is_alive():
            esta_grabando = False
            # Actualizamos el fondo para adaptarnos a cambios de luz ambiental
            fondo = gris

        # 5. Visualización (Opcional, útil para clase)
        cv2.putText(frame, f"Estado: {'Grabando' if esta_grabando else 'Vigilando'}", (10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255) if esta_grabando else (0, 255, 0), 2)
        
        cv2.imshow("Monitor de Vigilancia", frame)
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    cap.release()
    cv2.destroyAllWindows()