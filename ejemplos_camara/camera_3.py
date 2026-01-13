import cv2
from picamera2 import Picamera2
import libcamera

# Creamos el thread the la ventana de OpenCV
cv2.startWindowThread()
# Creamos el objeto de la RaspiCam
picam2 = Picamera2()
# Modificamos el framrate (fps)
picam2.video_configuration.controls.FrameRate = 25.0

# Configuramos la resolución y formato de la cámara
config = {"format": 'RGB888', "size": (640, 480),}
picam2.configure(
    picam2.create_preview_configuration(
        main=config, 
        transform=libcamera.Transform(vflip=True)))
# Iniciamos la vista previa de la cámara
picam2.start()

while True:
    # Capturamos una imagen (Teóricamente a 24fps)
    im_array = picam2.capture_array()
    # Convertimos la imagen a escala de grises
    grey = cv2.cvtColor(im_array, cv2.COLOR_RGB2GRAY)
    # Mostramos la imagen en una ventana de OpenCV llamada "Camera"
    cv2.imshow("Camera output", grey)
    # Esperamos 1ms para que la ventana de OpenCV no se cierre
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    
# Detenemos la vista previa de la cámara
picam2.stop()
# Cerramos la cámara
picam2.close()
# Cerramos la ventana de OpenCV
cv2.destroyAllWindows()
