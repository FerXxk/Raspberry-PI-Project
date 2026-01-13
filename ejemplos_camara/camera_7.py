import cv2
import numpy as np
import libcamera
# Creamos el thread the la ventana de OpenCV
from picamera2 import Picamera2
import time
import cv2
 
# Creamos el thread the la ventana de OpenCV
cv2.startWindowThread()
# Creamos el objeto de la RaspiCam
picam2 = Picamera2()
# Modificamos el framrate (fps)
picam2.video_configuration.controls.FrameRate = 24.0
# Configuramos la resolución y formato de la cámara
config = {"format": 'RGB888', "size": (640, 480)}
picam2.configure(
    picam2.create_preview_configuration(
        main=config, 
        transform=libcamera.Transform(vflip=True)))
# Iniciamos la vista previa de la cámara
picam2.start()

# Creamos una ventana de OpenCV llamada "Camera"
cv2.namedWindow("Raw")
cv2.namedWindow("Motion Mask")

last_frame = None
frames = []
t = 0
N = 3
THRESH = 50

while True:
    
    # Capturamos una imagen (Teóricamente a 24fps)
    im_array = picam2.capture_array()
    im_array_byn = cv2.cvtColor(im_array, cv2.COLOR_BGR2GRAY)
    
    frames.append(im_array_byn.copy())
        
    if len(frames) == N:
        # V(t) = || I(t-N) - I(t) ||
        diff = cv2.absdiff(frames[N-1], frames[0])
        diff = cv2.medianBlur(diff, 5) # Aplicamos un filtro de mediana de radio 5
        # Tomamos la mascara de movimiento con un umbral
        threshold_method = cv2.THRESH_BINARY
        ret, motion_mask = cv2.threshold(diff, THRESH, 255, threshold_method)
        #Display the Motion Mask
        cv2.imshow('Motion Mask', motion_mask)
        # Eliminamos el frame más antiguo
        frames.pop(0)
        # Calculamos el bounding box de la máscara de movimiento
        x, y, w, h = cv2.boundingRect(motion_mask)
        # Dibujamos el bounding box en la imagen original
        cv2.rectangle(im_array, (x, y), (x+w, y+h), (0, 255, 0), 4)
        cv2.putText(im_array, 
                    "Movimiento detectado!", 
                    (x, y-10), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
        # Mostramos la imagen en una ventana de OpenCV llamada "Camera"
        cv2.imshow("Raw", im_array)
        
    # Esperamos 1ms para que la ventana de OpenCV no se cierre
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    
# Liberamos la cámara y cerramos la ventana
picam2.stop()
cv2.destroyAllWindows()