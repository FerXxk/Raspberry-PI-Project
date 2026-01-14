import cv2
import time
import datetime
import os
import libcamera
from picamera2 import Picamera2
from flask import Flask, Response, render_template, jsonify
import threading
from gestor_almacenamiento import GestorAlmacenamiento
from sense_hat import SenseHat

# --- GLOBAL VARS FOR FLASK ---
outputFrame = None
global_status = "INICIANDO"
lock = threading.Lock()
sense = None

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/status")
def status():
    global global_status, tiempo_inicio_grabacion, sense
    
    # Calcular duración si está grabando
    duracion = 0
    if global_status == "GRABANDO":
        duracion = int(time.time() - tiempo_inicio_grabacion)
    
    # Leer sensores del Sense HAT
    temp_ambiente = "--°C"
    humidity = "--%"
    pressure = "-- hPa"
    try:
        if sense:
            temp_value = sense.get_temperature()
            temp_ambiente = f"{temp_value:.1f}°C"
            humidity_value = sense.get_humidity()
            humidity = f"{humidity_value:.1f}%"
            pressure_value = sense.get_pressure()
            pressure = f"{pressure_value:.1f} hPa"
    except Exception as e:
        print(f"Error al leer sensores del Sense HAT: {e}")

    # Leer temperatura CPU
    temp_cpu = "--°C"
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp_cpu = f"{int(f.read()) / 1000:.1f}°C"
    except:
        pass
    
    return jsonify({
        "status": global_status,
        "duration": duracion,
        "location_temp": temp_ambiente,
        "cpu_temp": temp_cpu,
        "humidity": humidity,
        "pressure": pressure
    })

def generate():
    global outputFrame, lock
    while True:
        with lock:
            if outputFrame is None:
                continue
            (flag, encodedImage) = cv2.imencode(".jpg", outputFrame)
            if not flag:
                continue
        yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encodedImage) + b'\r\n')

@app.route("/video_feed")
def video_feed():
    return Response(generate(), mimetype="multipart/x-mixed-replace; boundary=frame")

def start_flask():
    # Ejecutar Flask en modo accesible desde la red local
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)

# --- CONFIGURACIÓN ---
PATH_NAS = "/mnt/grabaciones_camara/"
MIN_AREA = 5000                # Sensibilidad: área mínima en píxeles
FPS = 10.0                     # FPS de grabación

# Configuración de Tiempos
MAX_DURACION = 60              # Duración máxima de un clip (segundos)
TIEMPO_SIN_MOVIMIENTO = 5      # Segundos a esperar tras dejar de detectar movimiento

# Verificar directorio
if not os.path.exists(PATH_NAS):
    try:
        os.makedirs(PATH_NAS)
    except OSError as e:
        print(f"Error al crear directorio {PATH_NAS}: {e}")
        exit(1)

def start_storage_manager():
    gestor = GestorAlmacenamiento(PATH_NAS, max_days=7, max_usage_percent=90)
    while True:
        gestor.ejecutar_limpieza()
        # Verificar cada 30 minutos (1800 segundos)
        time.sleep(1800)

def main():
    global outputFrame, lock, global_status, tiempo_inicio_grabacion
    print("Iniciando Sistema de Vigilancia con Picamera2...")
    print(f"Configuración: Máx {MAX_DURACION}s por clip, Stop tras {TIEMPO_SIN_MOVIMIENTO}s sin movimiento.")

    # 0. Iniciar Flask en un hilo separado
    t_flask = threading.Thread(target=start_flask)
    t_flask.daemon = True
    t_flask.start()

    # 0.1 Iniciar Gestor de Almacenamiento en hilo separado
    t_storage = threading.Thread(target=start_storage_manager)
    t_storage.daemon = True
    t_storage.start()

    # Inicializar Sense HAT
    global sense
    sense = SenseHat()
    print("Sense HAT inicializado.")

    # 1. Configuración de Picamera2
    try:
        picam2 = Picamera2()
        config = picam2.create_preview_configuration(
            main={"size": (640, 480), "format": "RGB888"},
            transform=libcamera.Transform(vflip=True)
        )
        picam2.configure(config)
        picam2.start()
        print("Cámara iniciada correctamente.")
    except Exception as e:
        print(f"Error fatal al iniciar la cámara: {e}")
        return

    time.sleep(2)

    fondo = None
    grabando = False
    tiempo_inicio_grabacion = 0
    ultimo_movimiento_time = 0
    out = None

    try:
        while True:
            # 2. Captura y Conversión
            frame = picam2.capture_array()
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            # 3. Procesamiento
            gris = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gris = cv2.GaussianBlur(gris, (21, 21), 0)

            if fondo is None:
                fondo = gris
                continue

            diferencia = cv2.absdiff(fondo, gris)
            _, umbral = cv2.threshold(diferencia, 25, 255, cv2.THRESH_BINARY)
            umbral = cv2.dilate(umbral, None, iterations=2)

            contornos, _ = cv2.findContours(umbral.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            movimiento_actual = False
            for c in contornos:
                if cv2.contourArea(c) < MIN_AREA:
                    continue
                movimiento_actual = True
                break

            ahora = time.time()

            # Si hay movimiento, actualizamos el temporizador de "último visto"
            if movimiento_actual:
                ultimo_movimiento_time = ahora

            # 4. Lógica de grabación
            if movimiento_actual and not grabando:
                # INICIAR GRABACIÓN
                grabando = True
                tiempo_inicio_grabacion = ahora
                
                # Timestamp bonito: DD-MM-YYYY__HH-MM-SS
                timestamp = datetime.datetime.now().strftime("%d-%m-%Y__%H-%M-%S")
                filename = os.path.join(PATH_NAS, f"alerta_{timestamp}.avi")
                
                print(f"[REC] Inicio: {filename}")
                
                fourcc = cv2.VideoWriter_fourcc(*'XVID')
                height, width, _ = frame.shape
                out = cv2.VideoWriter(filename, fourcc, FPS, (width, height))

            if grabando:
                if out is not None:
                    out.write(frame)
                
                # CONDICIONES DE PARADA
                duracion_actual = ahora - tiempo_inicio_grabacion
                tiempo_quieto = ahora - ultimo_movimiento_time
                
                razon_parada = ""
                if duracion_actual > MAX_DURACION:
                    razon_parada = "Tiempo máximo excedido"
                elif not movimiento_actual and tiempo_quieto > TIEMPO_SIN_MOVIMIENTO:
                    # Solo paramos si ha pasado X tiempo desde el último movimiento
                    razon_parada = "Sin movimiento"
                
                if razon_parada:
                    grabando = False
                    if out is not None:
                        out.release()
                        out = None
                    print(f"[STOP] {razon_parada}. Volviendo a vigilar.")
                    fondo = gris

            # 5. Visualización
            if grabando:
                global_status = "GRABANDO"
            else:
                global_status = "VIGILANDO"
            
            if movimiento_actual:
                 for c in contornos:
                    if cv2.contourArea(c) >= MIN_AREA:
                        (x, y, wa, ha) = cv2.boundingRect(c)
                        cv2.rectangle(frame, (x, y), (x + wa, y + ha), (0, 255, 0), 2)

            # Actualizar frame para Flask
            with lock:
                outputFrame = frame.copy()

            cv2.imshow("Monitor PI", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except KeyboardInterrupt:
        pass
    finally:
        print("Cerrando sistema...")
        if out is not None:
            out.release()
        picam2.stop()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()