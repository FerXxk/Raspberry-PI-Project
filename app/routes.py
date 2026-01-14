from flask import Blueprint, render_template, Response, jsonify, current_app

main_bp = Blueprint('main', __name__)

@main_bp.route("/")
def index():
    return render_template("index.html")

@main_bp.route("/status")
def status():
    # Access modules attached to app
    camera = current_app.camera
    sensors = current_app.sensors
    
    status_text, duration = camera.get_status()
    sensor_data = sensors.get_readings()
    
    response = {
        "status": status_text,
        "duration": duration,
        "location_temp": sensor_data["location_temp"],
        "cpu_temp": sensor_data["cpu_temp"],
        "humidity": sensor_data["humidity"],
        "pressure": sensor_data["pressure"]
    }
    # Backward compatibility for 'temp' if JS expects it (it does for 'temp-val' fallback?)
    # JS checks 'temp' for CPU or ambient? 
    # Current JS: 
    # if (cpuVal && data.cpu_temp) cpuVal.innerText = data.cpu_temp;
    # if (ambVal && data.location_temp) ambVal.innerText = data.location_temp;
    # But it also had: if (tempVal && data.temp) tempVal.innerText = data.temp;
    # (The replacement removed tempVal usage mostly, but let's provide 'temp' as generic alias to cpu_temp or location_temp just in case)
    response["temp"] = sensor_data["location_temp"] 
    
    return jsonify(response)

def generate_frames(camera):
    while True:
        frame_bytes = camera.get_frame()
        if frame_bytes:
            yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        else:
            # Yield nothing or wait if no frame is available yet
            import time
            time.sleep(0.1)

@main_bp.route("/video_feed")
def video_feed():
    camera = current_app.camera
    return Response(generate_frames(camera), mimetype="multipart/x-mixed-replace; boundary=frame")
