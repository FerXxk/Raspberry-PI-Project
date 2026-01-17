# 🛡️ Sistema de Vigilancia Inteligente con NAS Local

Este proyecto consiste en una solución de seguridad basada en Edge Computing que utiliza una Raspberry Pi 4 para detectar movimiento, grabar clips de vídeo automáticamente y servirlos a través de una red local mediante un almacenamiento NAS.

## 🚀 Estado Actual del Proyecto

Actualmente, el proyecto ha evolucionado a una solución integral que combina visión artificial, gestión automática de almacenamiento, una interfaz web de monitoreo en tiempo real y **sistema dual de operación** (Portero/Vigilancia). Utiliza la librería moderna **Picamera2** para máximo rendimiento en Raspberry Pi OS (Bullseye/Bookworm).

### 1. Sistema Dual de Operación

El sistema cuenta con **dos modos de funcionamiento**:

#### 🔔 Modo 1: Portero (Doorbell)
- **Activación**: Presionar el botón central del joystick del SenseHat
- **Funcionamiento**:
  - Reproduce un sonido de timbre por los altavoces
  - Captura una foto instantánea
  - Envía la foto por Telegram con notificación 🔔
  - No graba video
- **Ideal para**: Usar la Raspberry como timbre inteligente

#### 🎥 Modo 2: Video Vigilancia
- **Activación**: Detección automática de movimiento
- **Funcionamiento**:
  - Detecta movimiento mediante algoritmos de OpenCV
  - Graba video automáticamente
  - Envía alerta por Telegram con foto
  - Detiene grabación tras 5s sin movimiento o 60s máximo
- **Ideal para**: Vigilancia continua y automática

**Cambio de Modo**:
- 🌐 **Interfaz Web**: Botón "Cambiar a modo portero/vigilancia"
- 📱 **Telegram**: Comandos `/portero` y `/vigilancia`
- 📊 **Estado**: Comando `/estado` para ver el modo actual

### 2. Sistema de Vigilancia (Core - `run.py` & `modules/`)
- **Arquitectura**: Código reestructurado en módulos (`camera.py`, `sensors.py`, `mode_manager.py`) orquestados por `run.py`.
- **Motor de Captura**: **Picamera2** basado en `libcamera` para acceso eficiente al hardware.
- **Detección de Movimiento**: Algoritmos de **OpenCV** (Blur, Thresholding, Contornos) para detectar intrusos.
- **Grabación Inteligente**:
    - **Smart Stop**: Detiene la grabación tras **5 segundos** sin movimiento o al llegar a **60 segundos** de duración.
    - **Multihilo**: La captura, el servidor web y el gestor de almacenamiento corren en hilos independientes para asegurar fluidez.
- **Monitoreo de Botón**: Thread dedicado para detectar pulsaciones del joystick del SenseHat.

### 3. Interfaz Web de Monitoreo
Sistema accesible desde cualquier navegador en la red local (`http://<IP-RASPBERRY>:5000`).
- **Live Stream**: Visualización en tiempo real de la cámara.
- **Panel de Estado**:
    - Indicador visual de estado (**VIGILANDO** / **GRABANDO** / **MODO PORTERO**).
    - Cronómetro de duración de grabación activa.
    - Monitor de temperatura de la CPU y ambiente.
    - Humedad y presión atmosférica.
- **Control de Modo**: Botón para cambiar entre modo Portero y Vigilancia.
- **Diseño Responsivo**: Adaptado para móviles y escritorio.

### 4. Gestor de Almacenamiento Automático (NAS)
Módulo inteligente (`modules/storage.py`) que asegura que el disco nunca se llene.
- **Políticas de Limpieza**:
    1. **Por Antigüedad**: Borra videos con más de **7 días** de antigüedad.
    2. **Por Espacio**: Si el disco supera el **85% de uso**, borra los videos más antiguos hasta liberar un 5% de espacio.
- **Ciclo de Mantenimiento**: Se ejecuta automáticamente cada 30 minutos.

### 5. Telegram Service
Módulo que permite controlar la cámara a través de Telegram.
- **Comandos Disponibles**:
    - `/portero` - Cambia a Modo 1 (Portero/Timbre)
    - `/vigilancia` - Cambia a Modo 2 (Video Vigilancia)
    - `/estado` - Muestra el modo actual y estado del sistema
- **Funcionalidades**:
    - **Reproducción de Mensajes de Voz**: Permite reproducir mensajes de voz enviados desde Telegram.
    - **Alertas de Movimiento**: Envía alertas con foto cuando se detecta movimiento (Modo 2).
    - **Alertas de Timbre**: Envía foto cuando se presiona el botón (Modo 1).

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
- **Hardware**: Raspberry Pi 4, Cámara Pi, SenseHat, Disco USB.
- **Backend de Visión**: Python 3.11+, `picamera2`, `opencv-python`.
- **Backend Web**: `Flask` (Server), `Threading` (Concurrencia).
- **Frontend**: HTML5, CSS3 (Diseño responsivo).
- **Almacenamiento**: Gestión automática con `shutil` y `os`.
- **Comunicación**: `python-telegram-bot` para integración con Telegram.
- **Audio**: `ffplay` (ffmpeg) para reproducción de sonidos.

## 📂 Configuraciones Clave
El archivo `config.py` centraliza la configuración del sistema:
```python
# Rutas
PATH_NAS = "/mnt/grabaciones_camara/"

# Detección de movimiento
MIN_AREA = 5000                # Sensibilidad al movimiento
MAX_DURACION = 60              # Tiempo límite por video
TIEMPO_SIN_MOVIMIENTO = 5      # Tiempo de espera antes de cortar

# Almacenamiento
MAX_USAGE_PERCENT = 85         # Porcentaje máximo de uso del disco
STORAGE_CLEANUP_PERCENT = 5    # Porcentaje a liberar en limpieza

# Modos de operación
OPERATION_MODE = 2             # Modo por defecto: 1=Portero, 2=Vigilancia

# Telegram
TELEGRAM_TOKEN = "TU_TOKEN_AQUI"
TELEGRAM_CHAT_ID = "TU_CHAT_ID"

# Sonido de timbre
DOORBELL_SOUND_PATH = os.path.join(BASE_DIR, "doorbell.mp3")
DOORBELL_SOUND_VOLUME = 100    # Volumen (0-100)
```

## 🔧 Configuración Inicial de la Raspberry Pi

### Expandir el Sistema de Archivos
Después de instalar Raspberry Pi OS en la tarjeta SD, es importante expandir la partición para usar todo el espacio disponible:

1. Abre la herramienta de configuración:
   ```bash
   sudo raspi-config
   ```

2. Navega a la opción **6 Advanced Options**

3. Selecciona **A1 Expand Filesystem**

4. El sistema te indicará que la partición se expandirá al reiniciar. Presiona **Ok**

5. Sal de la configuración y reinicia:
   ```bash
   sudo reboot
   ```

6. Después del reinicio, verifica el espacio disponible:
   ```bash
   df -h
   ```

### Instalación de Dependencias

```bash
# Actualizar el sistema
sudo apt-get update
sudo apt-get upgrade -y

# Instalar dependencias del sistema
sudo apt-get install -y python3-pip python3-picamera2 python3-opencv ffmpeg

# Instalar dependencias de Python
pip3 install -r requirements.txt
```


## 🚀 Ejecución

```bash
cd Raspberry-PI-Project
python3 run.py
```

El sistema iniciará:
- ✅ Servidor web en `http://<IP>:5000`
- ✅ Detección de movimiento (si está en Modo 2)
- ✅ Monitoreo del botón del SenseHat (para Modo 1)
- ✅ Bot de Telegram
- ✅ Gestor de almacenamiento automático

## 📱 Uso del Sistema

### Desde la Interfaz Web
1. Abre `http://<IP-RASPBERRY>:5000` en tu navegador
2. Visualiza el stream en vivo de la cámara
3. Observa el estado actual en las tarjetas superiores
4. Usa el botón "Cambiar a modo portero/vigilancia" para alternar modos

### Desde Telegram
1. Envía `/estado` para ver el modo actual
2. Envía `/portero` para activar el modo timbre
3. Envía `/vigilancia` para activar el modo vigilancia
4. Envía mensajes de voz para reproducirlos en la Raspberry

### Modo Portero
1. Asegúrate de estar en Modo Portero (vía web o `/portero`)
2. Presiona el botón central del joystick del SenseHat
3. Escucharás el sonido del timbre
4. Recibirás una foto por Telegram

### Modo Vigilancia
1. Asegúrate de estar en Modo Vigilancia (vía web o `/vigilancia`)
2. El sistema detectará movimiento automáticamente
3. Grabará video y enviará alerta por Telegram
4. Los videos se guardan en `/mnt/grabaciones_camara/`

## 🔍 Próximos Pasos
- **Reproductor Web**: Galería para ver los videos grabados desde el navegador.
- **Detección de Personas**: Integrar modelos de ML para distinguir personas de mascotas/objetos.
- **Zonas de Detección**: Configurar áreas específicas para ignorar movimiento.