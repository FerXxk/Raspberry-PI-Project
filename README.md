# 🛡️ Sistema de Vigilancia Inteligente con NAS Local

Este proyecto consiste en una solución de seguridad basada en Edge Computing que utiliza una Raspberry Pi 4 para detectar movimiento, grabar clips de vídeo automáticamente y servirlos a través de una red local mediante un almacenamiento NAS.

## 🚀 Estado Actual del Proyecto

Actualmente, el proyecto ha evolucionado a una solución integral que combina visión artificial, gestión automática de almacenamiento y una interfaz web de monitoreo en tiempo real. Utiliza la librería moderna **Picamera2** para máximo rendimiento en Raspberry Pi OS (Bullseye/Bookworm).

### 1. Sistema de Vigilancia (Core - `run.py` & `modules/`)
- **Arquitectura**: Código reestructurado en módulos (`camera.py`, `sensors.py`) orquestados por `run.py`.
- **Motor de Captura**: **Picamera2** basado en `libcamera` para acceso eficiente al hardware.
- **Detección de Movimiento**: Algoritmos de **OpenCV** (Blur, Thresholding, Contornos) para detectar intrusos.
- **Grabación Inteligente**:
    - **Smart Stop**: Detiene la grabación tras **5 segundos** sin movimiento o al llegar a **60 segundos** de duración.
    - **Multihilo**: La captura, el servidor web y el gestor de almacenamiento corren en hilos independientes para asegurar fluidez.

### 2. Interfaz Web de Monitoreo
Sistema accesible desde cualquier navegador en la red local (`http://<IP-RASPBERRY>:5000`).
- **Live Stream**: Visualización en tiempo real de la cámara.
- **Panel de Estado**:
    - Indicador visual de estado (**VIGILANDO** / **GRABANDO**).
    - Cronómetro de duración de grabación activa.
    - Monitor de temperatura de la CPU.
- **Diseño Responsivo**: Adaptado para móviles y escritorio.

### 3. Gestor de Almacenamiento Automático (NAS)
Módulo inteligente (`modules/storage.py`) que asegura que el disco nunca se llene.
- **Políticas de Limpieza**:
    1. **Por Antigüedad**: Borra videos con más de **7 días** de antigüedad.
    2. **Por Espacio**: Si el disco supera el **90% de uso**, borra los videos más antiguos hasta liberar un 5% de espacio.
- **Ciclo de Mantenimiento**: Se ejecuta automáticamente cada 30 minutos.

### 4. Telegram Service
Módulo que permite controlar la cámara a través de Telegram.
- **Funcionalidades**:
    - **Reproducción de Mensajes de Voz**: Permite reproducir mensajes de voz enviados desde Telegram.
    - **Alertas de Movimiento**: Envía alertas de movimiento a través de Telegram.
    - **Reproducción de Audio**: Permite reproducir audio enviados desde Telegram.

## 🌍 Acceso Remoto (VPN)
Para acceder a la cámara desde fuera de casa de forma segura, incluimos un script para configurar **Tailscale**:

1. Ejecuta el script de instalación en la Raspberry Pi:
   ```bash
   sudo bash scripts/setup_tailscale.sh
   ```
2. Sigue el enlace que aparece en pantalla para loguearte con tu cuenta.
3. El script te mostrará una **IP de Tailscale** (ej. `100.x.y.z`).
4. Desde tu móvil/PC (con Tailscale instalado), entra a: `http://100.x.y.z:5000`.

## 🛠️ Stack Tecnológico
- **Hardware**: Raspberry Pi 4, Cámara, Disco USB.
- **Backend de Visión**: Python 3.11+, `picamera2`, `opencv-python`.
- **Backend Web**: `Flask` (Server), `Threading` (Concurrencia).
- **Frontend**: HTML5, CSS3 (Diseño responsivo).
- **Almacenamiento**: Gestión automática con `shutil` y `os`.

## 📂 Configuraciones Clave
El archivo `config.py` centraliza la configuración del sistema:
```python
PATH_NAS = "/mnt/grabaciones_camara/"
MIN_AREA = 5000                # Sensibilidad al movimiento
MAX_DURACION = 60              # Tiempo límite por video
TIEMPO_SIN_MOVIMIENTO = 5      # Tiempo de espera antes de cortar
```

## 🔍 Próximos Pasos
- **Autenticación Web**: Añadir login básico para la interfaz web.
- **Notificaciones**: Integración con Telegram/Email al detectar movimiento.
- **Reproductor Web**: Galería para ver los videos grabados desde el navegador.