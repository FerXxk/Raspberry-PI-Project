from picamera2 import Picamera2
import time
import cv2
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

# calentamiento de la cámara
time.sleep(0.1)
print("Saca la primera foto pulsando a")
# capturamos los frames
while True:
    
    image = picam2.capture_array()

    cv2.imshow("Frame", image)
    key = cv2.waitKey(1) & 0xFF
 	
    if key == ord("a"): # tomamos la primera foto
          imagen1=image
          cv2.imshow("A",imagen1)
          time.sleep(3)
          print("Saca la segunda foto pulsando b")
         
    if key == ord("b"): # tomamos la segunda foto
          imagen2=image
          cv2.imshow("B",imagen2)
          time.sleep(3)
          print("Para mezclarlas, pulsa m")
         
    if key == ord("m"): # mezclamos las fotos

          try:
               alfa = input("Introduzca porcentaje de mezcla (0.0 - 100.0%):\n")
               alfa_f = float(alfa)/100.0
               beta = 1.0 - alfa_f
               dst = cv2.addWeighted(imagen1, alfa_f, imagen2, beta, 0)
               cv2.imshow("BLEND", dst)
               print("Mezcla al %s" %alfa)
               time.sleep(3)
               print("Para salir, pulsa q")
          except:
               print("Error")
               break
         
    if key == ord("q"): # para salir 
        break
         
picam2.close()
cv2.destroyAllWindows()