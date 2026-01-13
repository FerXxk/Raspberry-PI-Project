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

# Creamos una ventana de OpenCV llamada "Camera"
cv2.namedWindow("Sin filtrar")
cv2.namedWindow("Filtrado")
# Creamos una ventana para los deslizadores
cv2.namedWindow("Deslizadores")

# Callback para cambiar el valor de los deslizadores
def nothing(x):
    pass

# Creamos los deslizadores
cv2.createTrackbar("Hue Min", "Deslizadores", 0, 255, nothing)
cv2.createTrackbar("Hue Max", "Deslizadores", 255, 255, nothing)
cv2.createTrackbar("Sat Min", "Deslizadores", 0, 255, nothing)
cv2.createTrackbar("Sat Max", "Deslizadores", 255, 255, nothing)
cv2.createTrackbar("Val Min", "Deslizadores", 0, 255, nothing)
cv2.createTrackbar("Val Max", "Deslizadores", 255, 255, nothing)

while True:
    
    # Capturamos una imagen (Teóricamente a 24fps)
    im_array = picam2.capture_array()
    # Convertimos la imagen a espacio de color HSV
    hsv = cv2.cvtColor(im_array, cv2.COLOR_BGR2HSV)
    
    # Obtenemos los valores de los deslizadores
    h_min = cv2.getTrackbarPos("Hue Min", "Deslizadores")
    h_max = cv2.getTrackbarPos("Hue Max", "Deslizadores")
    s_min = cv2.getTrackbarPos("Sat Min", "Deslizadores")
    s_max = cv2.getTrackbarPos("Sat Max", "Deslizadores")
    v_min = cv2.getTrackbarPos("Val Min", "Deslizadores")
    v_max = cv2.getTrackbarPos("Val Max", "Deslizadores")
    
    # Creamos una máscara para los valores de H, S y V
    mask = cv2.inRange(hsv, (h_min, s_min, v_min), (h_max, s_max, v_max))
    
    # Aplicamos la máscara a la imagen original
    res = cv2.bitwise_and(im_array, im_array, mask=mask)
    
    # Mostramos la imagen en una ventana de OpenCV llamada "Camera"
    cv2.imshow("Sin filtrar", im_array)
    cv2.imshow("Filtrado", res)
    # Esperamos 1ms para que la ventana de OpenCV no se cierre
    key = cv2.waitKey(100) & 0xFF
    if key == ord('q'):
        break

# Liberamos la cámara y cerramos la ventana
picam2.stop()
cv2.destroyAllWindows()