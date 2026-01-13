from picamera2 import Picamera2, Preview
import gpiozero
from time import sleep
import libcamera

# Creamos un objeto tipo Button 
button = gpiozero.Button("GPIO1", pull_up=True)

# Instanciamos la clase PiCamera2
camera = Picamera2()

# Configuramos la resolución, visualizacion y rotación de la cámara
camera_config = camera.create_still_configuration(
    main={"size": (1920, 1080)}, 
    lores={"size": (640, 480)}, 
    display="lores")
camera_config['transform'] = libcamera.Transform(vflip=True) 
camera.configure(camera_config)
# Iniciamos la camara
camera.start_preview(Preview.QTGL)
camera.start()
# Iniciamos la vista previa de la cámara

for index in range(5):
    
    # Usamos el método wait_for_press() 
    # para esperar a que el botón sea presionado 
    print("Esperando a boton")
    button.wait_for_press() 
    for i in range(5):
        print(i)
        sleep(1) # Esperamos 5 segundos
    camera.capture_file(f'./captura_{index}.jpg') # Capturamos! 
    print("Foto capturada!")

camera.close()        


