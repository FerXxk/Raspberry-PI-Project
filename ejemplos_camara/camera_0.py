from picamera2 import Picamera2, Preview
from time import sleep
import libcamera

# Instanciamos la clase PiCamera2
camera = Picamera2()

# Configuramos la resolución, visualizacion y rotación de la cámara
camera_config = camera.create_still_configuration(
    main={"size": (1920, 1080)}, 
    lores={"size": (640, 480)}, 
    display="lores")
camera_config['transform'] = libcamera.Transform(vflip=True) 
camera.configure(camera_config)

# Iniciamos la vista previa de la cámara
camera.start_preview(Preview.QTGL)
camera.start()

for i in range(1,4):
    print(4-i)
    sleep(1)
    
# Capturamos una imagen
camera.capture_file('./imagen.jpg')
# Detenemos la vista previa y cerramos la cámara
camera.stop_preview()
# Cerramos la cámara
camera.close()
