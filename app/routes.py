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
    # Acceso a los módulos compartidos
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
    # Alias para compatibilidad con el frontend 
    response["temp"] = sensor_data["location_temp"] 
    
    return jsonify(response)

def generate_frames(camera):
    while True:
        frame_bytes = camera.get_frame()
        if frame_bytes:
            yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        else:
            # Pausa si no hay frame disponible
            import time
            time.sleep(0.1)

@main_bp.route("/video_feed")
def video_feed():
    camera = current_app.camera
    return Response(generate_frames(camera), mimetype="multipart/x-mixed-replace; boundary=frame")

@main_bp.route("/mode", methods=["GET"])
def get_mode():
    """Obtener el modo actual."""
    mode_manager = current_app.mode_manager
    if mode_manager:
        return jsonify({
            "mode": mode_manager.get_mode(),
            "description": mode_manager.get_mode_description()
        })
    return jsonify({"error": "Mode manager not available"}), 500

@main_bp.route("/mode", methods=["POST"])
def set_mode():
    """Cambiar de modo (Vigilancia / Portero)."""
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
    """Renderiza la galería de videos."""
    return render_template("gallery.html")

@main_bp.route("/api/recordings")
def list_recordings():
    """Listado de grabaciones disponibles en el disco NAS."""
    recordings = []
    if os.path.exists(config.PATH_NAS):
        files = [f for f in os.listdir(config.PATH_NAS) if f.endswith('.mp4')]
        # Ordenar por fecha de creación (más recientes primero)
        files.sort(key=lambda x: os.path.getmtime(os.path.join(config.PATH_NAS, x)), reverse=True)
        
        for f in files:
            path = os.path.join(config.PATH_NAS, f)
            stat = os.stat(path)
            
            # Verificar si existe miniatura (.jpg)
            thumb_name = f.rsplit('.', 1)[0] + ".jpg"
            thumbnail_url = None
            if os.path.exists(os.path.join(config.PATH_NAS, thumb_name)):
                thumbnail_url = f"/thumbnails/{thumb_name}"

            recordings.append({
                "filename": f,
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "date": datetime.datetime.fromtimestamp(stat.st_mtime).strftime('%d/%m/%Y %H:%M:%S'),
                "thumbnail_url": thumbnail_url
            })
    
    return jsonify(recordings)

@main_bp.route("/recordings/<path:filename>")
def serve_video(filename):
    """Sirve el video directamente desde el NAS."""
    return send_from_directory(config.PATH_NAS, filename, mimetype='video/mp4')

@main_bp.route("/thumbnails/<path:filename>")
def serve_thumbnail(filename):
    """Sirve la miniatura de una alerta."""
    return send_from_directory(config.PATH_NAS, filename)
