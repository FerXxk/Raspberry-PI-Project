import time

from picamera2 import Picamera2, Preview
from picamera2.encoders import Encoder, H264Encoder, Quality
import gpiozero

# Creamos el botón conectado al GPIO1 con pull-up
button = gpiozero.Button("GPIO1", pull_up=True)
# Instanciamos la clase PiCamera2
picam2 = Picamera2()
video_config = picam2.create_video_configuration(
    main={"size": (1920, 1080)}, 
    lores={"size": (640, 480)}, 
    display="lores")

# Ajustamos la resolución y el framerate
picam2.configure(video_config)

# Iniciamos la vista previa de la cámara
picam2.start_preview(Preview.QTGL)
picam2.start()

# Si queremos grabar en formato RAW
# encoder = Encoder()
# Creamos un objeto tipo H264Encoder (compresor de video)
encoder = H264Encoder(10000000)

# Iniciamos la grabación de video
button.wait_for_press() # Esperamos a que el botón sea presionado
print("Grabando video")
picam2.start_recording(encoder, './video.h264', quality=Quality.HIGH)
time.sleep(2)
button.wait_for_press() # Esperamos a que el botón sea presionado
print("Deteniendo grabación")
picam2.stop_recording()
