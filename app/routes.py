from flask import Blueprint, render_template, Response, jsonify, current_app, request, send_from_directory
import os
import datetime
import config

main_bp = Blueprint('main', __name__)

@main_bp.route("/")
def index():
    return render_template("index.html")

@main_bp.route("/status")
def status():
    # Access modules attached to app
    camera = current_app.camera
    sensors = current_app.sensors
    mode_manager = current_app.mode_manager
    
    status_text, duration = camera.get_status()
    sensor_data = sensors.get_readings()
    
    response = {
        "status": status_text,
        "duration": duration,
        "location_temp": sensor_data["location_temp"],
        "cpu_temp": sensor_data["cpu_temp"],
        "humidity": sensor_data["humidity"],
        "pressure": sensor_data["pressure"],
        "mode": mode_manager.get_mode() if mode_manager else 2,
        "mode_description": mode_manager.get_mode_description() if mode_manager else "Unknown"
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

@main_bp.route("/mode", methods=["GET"])
def get_mode():
    """Get current operation mode."""
    mode_manager = current_app.mode_manager
    if mode_manager:
        return jsonify({
            "mode": mode_manager.get_mode(),
            "description": mode_manager.get_mode_description()
        })
    return jsonify({"error": "Mode manager not available"}), 500

@main_bp.route("/mode", methods=["POST"])
def set_mode():
    """Switch operation mode."""
    mode_manager = current_app.mode_manager
    if not mode_manager:
        return jsonify({"error": "Mode manager not available"}), 500
    
    data = request.get_json()
    new_mode = data.get("mode")
    
    if new_mode not in [1, 2]:
        return jsonify({"error": "Invalid mode. Must be 1 or 2"}), 400
    
    changed = mode_manager.set_mode(new_mode)
    
    return jsonify({
        "success": True,
        "changed": changed,
        "mode": mode_manager.get_mode(),
        "description": mode_manager.get_mode_description()
    })

@main_bp.route("/gallery")
def gallery():
    """Render the video gallery page."""
    return render_template("gallery.html")

@main_bp.route("/api/recordings")
def list_recordings():
    """Return a list of recordings from the NAS directory."""
    recordings = []
    if os.path.exists(config.PATH_NAS):
        files = [f for f in os.listdir(config.PATH_NAS) if f.endswith('.avi')]
        # Sort by modification time (newest first)
        files.sort(key=lambda x: os.path.getmtime(os.path.join(config.PATH_NAS, x)), reverse=True)
        
        for f in files:
            path = os.path.join(config.PATH_NAS, f)
            stat = os.stat(path)
            recordings.append({
                "filename": f,
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "date": datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%d/%m/%Y %H:%M:%S')
            })
    
    return jsonify(recordings)

@main_bp.route("/recordings/<path:filename>")
def serve_video(filename):
    """Serve a video file from the NAS directory."""
    return send_from_directory(config.PATH_NAS, filename)
