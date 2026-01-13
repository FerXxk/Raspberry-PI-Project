# Uso de HAAR cascades para detección de rostros
# Uso de la cámara

import cv2
import numpy as np
from picamera2 import Picamera2
import libcamera

# Creamos el thread the la ventana de OpenCV
cv2.startWindowThread()
# Creamos el objeto de la RaspiCam
picam2 = Picamera2()
# Modificamos el framrate (fps)
picam2.video_configuration.controls.FrameRate = 25.0
# Configuramos la resolución y formato de la cámara
config = {"format": 'RGB888', "size": (640, 480)}
picam2.configure(
    picam2.create_preview_configuration(
        main=config, 
        transform=libcamera.Transform(vflip=True)))
# Iniciamos la vista previa de la cámara
picam2.start()

# Cargamos el clasificador de Haar
frontal_cascade = cv2.CascadeClassifier('haar_filters/haarcascade_frontalface_default.xml')

while True:
    # Capturamos un frame
    frame = picam2.capture_array()
    
    # Convertimos a escala de grises
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # Detectamos rostros
    caras_frontales = frontal_cascade.detectMultiScale(gray, 1.3, 5)

    # Dibujamos un rectángulo alrededor de los rostros
    for (x,y,w,h) in caras_frontales:
        cv2.rectangle(frame, (x,y), (x+w,y+h), (255,0,0), 2)
    
    # Mostramos el frame
    cv2.imshow('frame', frame)
    
    # Salimos con 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
    
# Liberamos la cámara y cerramos la ventana
picam2.stop()
cv2.destroyAllWindows()
