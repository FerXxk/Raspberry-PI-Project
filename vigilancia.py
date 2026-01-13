import cv2
import time
import datetime
import threading
import os

# --- CONFIGURACIÓN ---
PATH_NAS = "/mnt/grabaciones_camara/"
MIN_AREA = 5000                
DURACION_CLIP = 10             
FPS = 20.0                     

def grabar_video(nombre_archivo, ancho, alto):
    """ Función para grabar en un hilo aparte """
    print(f"--- [HILO] Iniciando grabación en: {nombre_archivo}")
    
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(nombre_archivo, fourcc, FPS, (ancho, alto))
    
    # IMPORTANTE: El hilo también debe usar el pipeline de libcamera
    pipeline_hilo = "libcamerasrc ! video/x-raw, width=640, height=480 ! videoconvert ! appsink"
    cap_hilo = cv2.VideoCapture(pipeline_hilo, cv2.CAP_GSTREAMER)
    
    start_time = time.time()
    while int(time.time() - start_time) < DURACION_CLIP:
        ret, frame = cap_hilo.read()
        if ret:
            out.write(frame)
        else:
            break
            
    cap_hilo.release()
    out.release()
    print(f"--- [HILO] Grabación finalizada.")

# --- INICIO DEL PROGRAMA PRINCIPAL ---

# Pipeline específico para cámaras Pi Camera en OS modernos (Bullseye/Bookworm)
pipeline = (
    "libcamerasrc ! "
    "video/x-raw, width=640, height=480, framerate=30/1 ! "
    "videoconvert ! "
    "appsink"
)

print("Intentando abrir la cámara...")
cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)

# VERIFICACIÓN DE SEGURIDAD
if not cap.isOpened():
    print("ERROR FATAL: No se pudo conectar con la cámara mediante GStreamer.")
    print("Prueba a ejecutar: 'libcamera-hello' para descartar fallos de hardware.")
    exit()

time.sleep(2) 
fondo = None
esta_grabando = False

print("Sistema NAS de vigilancia activado. Presiona 'q' para salir.")

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Se perdió la señal de la cámara.")
            break

        # 1. Preprocesamiento
        gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gris = cv2.GaussianBlur(gris, (21, 21), 0)

        if fondo is None:
            fondo = gris
            continue

        # 2. Diferencia y Umbral
        diferencia = cv2.absdiff(fondo, gris)
        umbral = cv2.threshold(diferencia, 25, 255, cv2.THRESH_BINARY)[1]
        umbral = cv2.dilate(umbral, None, iterations=2)

        # 3. Detección de movimiento
        contornos, _ = cv2.findContours(umbral.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        movimiento_detectado = False
        for c in contornos:
            if cv2.contourArea(c) < MIN_AREA:
                continue
            movimiento_detectado = True
            break

        # 4. Disparar Hilo de Grabación
        if movimiento_detectado and not esta_grabando:
            esta_grabando = True
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_final = os.path.join(PATH_NAS, f"movimiento_{timestamp}.avi")
            
            ancho = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            alto = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            t = threading.Thread(target=grabar_video, args=(nombre_final, ancho, alto))
            t.start()

        if esta_grabando and 't' in locals() and not t.is_alive():
            esta_grabando = False
            fondo = gris # Actualizar fondo para evitar bucles de detección

        # 5. Visualización
        cv2.imshow("Monitor NAS", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

finally:
    cap.release()
    cv2.destroyAllWindows()