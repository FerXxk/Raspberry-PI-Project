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
config = {"format": 'RGB888', "size": (640, 480)}
picam2.configure(
    picam2.create_preview_configuration(
        main=config, 
        transform=libcamera.Transform(vflip=True)))
# Iniciamos la vista previa de la cámara
picam2.start()

# Variables globals para saber si se ha hecho doble click o si se está dibujando
Final = False
dibuja_flag = False
centro = (0,0)
# Callback para dibujar un círculo en la imagen
def mouse_callback(event, x, y, flags, param):
    global dibuja_flag, centro, Final

    if event == cv2.EVENT_LBUTTONDOWN:
        dibuja_flag = True
        centro = (x,y)
    
    elif event == cv2.EVENT_LBUTTONDBLCLK:
        Final = True
        
        
# Creamos las ventanas de OpenCV
cv2.namedWindow("Frame")
# Asociamos el callback a la ventana "Frame"
cv2.setMouseCallback("Frame", mouse_callback)

while not Final:
    # Capturamos una imagen
    im_array = picam2.capture_array()
    
    # Dibujamos un círculo si se ha hecho click
    if dibuja_flag:
        cv2.circle(im_array, centro, 10, (0,0,255), -1)

    # Mostramos la imagen en la ventana de OpenCV
    cv2.imshow("Frame", im_array)
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
