# 🛡️ Sistema de Vigilancia Inteligente con NAS Local

Este proyecto es una solución de seguridad avanzada basada en **Edge Computing** que transforma una Raspberry Pi 4 en un sistema de vigilancia profesional. Utiliza inteligencia artificial para la detección de personas, gestiona automáticamente el almacenamiento en un disco NAS y permite el control total a través de una interfaz web y Telegram. 🚀

## 📁 Estado Actual del Proyecto

El sistema ha evolucionado de un script básico de cámara a una infraestructura modular y robusta que incluye:

- **IA Integrada**: Detección de personas mediante MediaPipe para eliminar falsas alarmas.
- **Gestión NAS**: Limpieza automática de disco y políticas de retención de vídeo.
- **Sistema Dual**: Cambia entre modo **Timbre Inteligente** y **Cámara de Seguridad**.
- **Acceso Remoto**: VPN integrada para ver tu casa desde cualquier lugar.
- **Control por Voz**: Reproducción de mensajes enviados desde Telegram.

---

## 🔄 1. Modos de Operación

El sistema permite alternar entre dos configuraciones principales según tus necesidades:

### 🔔 Modo 1: Portero (Doorbell)
Diseñado para ser el corazón de tu entrada.
- **Disparador**: Pulsación física del botón central en el SenseHat.
- **Acciones**:
  - 🔊 Reproduce un sonido de timbre de alta calidad.
  - 📸 **Captura Inteligente**: El sistema espera `TELEGRAM_ALERT_DELAY` y luego analiza ráfagas de imágenes durante 2 segundos para enviar a Telegram la foto donde se vea mejor a la persona.
- **Uso**: Ideal cuando estás en casa y quieres saber quién llama a la puerta desde tu móvil.

### 🎥 Modo 2: Video Vigilancia
Vigilancia activa 24/7 con IA.
- **Disparador**: Detección de movimiento mediante OpenCV.
- **Acciones**:
  - 🔍 **Filtro de IA**: Verifica instantáneamente si hay una persona antes de grabar.
  - 📹 **Grabación Automática**: Guarda clips en formato `.avi` en tu almacenamiento NAS.
  - 🚨 **Alerta de Emergencia**: Envía una notificación con la mejor captura de la persona a Telegram.
  - 🛑 **Parada Inteligente**: Si la persona sale del encuadre, la grabación se detiene tras 2 segundos de ausencia para ahorrar espacio.
- **Uso**: Seguridad perimetral y detección de intrusos.

---

## 🧠 2. Arquitectura del Sistema (Core)

El software está dividido en módulos independientes coordinados por `run.py`:

- **`camera.py`**: Gestiona la lógica de Picamera2, el procesamiento de frames y la detección de movimiento.
- **`detector.py`**: Motor de IA basado en MediaPipe. Utiliza el modelo `efficientdet_lite0.tflite` para reconocer humanos con alta precisión.
- **`storage.py`**: El "limpiador" del NAS. Controla que el disco no se llene siguiendo dos reglas:
    1. **Antigüedad**: Borra vídeos de más de `MAX_DAYS_STORAGE` (por defecto 7 días).
    2. **Capacidad**: Si el disco supera el `MAX_USAGE_PERCENT` (85%), libera espacio borrando los archivos más antiguos.
- **`sensors.py`**: Gestiona el SenseHat (temperatura, humedad, presión) y el monitoreo del botón central del joystick.
- **`telegram_service.py`**: Gestiona la comunicación móvil. Permite recibir alertas y enviar comandos/voz.

---

## 🖥️ 3. Interfaz Web y Control

Accede desde `http://<IP-RASPBERRY>:5000` a un panel de control premium:

- **Live Streaming**: Vídeo en tiempo real con latencia mínima y colores corregidos.
- **Telemetría**: Gráficos y datos en vivo de la CPU y el ambiente (SenseHat).
- **Gestión de Modos**: Cambia entre Portero y Vigilancia con un solo clic.
- **Estado Visual**: Indicadores claros de **VIGILANDO** o **GRABANDO** con cronómetro integrado.

---

## 📂 4. Almacenamiento NAS (Samba)

Tu Raspberry Pi actúa ahora como un servidor de archivos (NAS) para que puedas ver los vídeos directamente desde el explorador de archivos de tu PC o móvil:

- **Configuración rápida**: Ejecuta `bash scripts/setup_samba.sh` una vez.
- **Nombre de red**: `\\raspberrypi.local\Grabaciones` (en Windows) o `smb://raspberrypi.local/Grabaciones` (en Mac/Móvil).
- **Control automático**: Cada vez que ejecutas `run.py`, el sistema verifica que el servidor NAS esté activo.
- **Acceso**: Sin contraseña (puedes navegar las grabaciones libremente dentro de tu red local).

---

## 📱 4. Control por Telegram

El bot de Telegram es tu mando a distancia:

- `/portero`: Activa el Modo 1.
- `/vigilancia`: Activa el Modo 2.
- `/estado`: Reporte detallado de en qué está trabajando el sistema.
- **Mensajes de Voz**: Envía un audio al chat y la Raspberry lo reproducirá por sus altavoces de forma inmediata.

---

---

## 🚀 Instalación y Despliegue

Para instrucciones detalladas sobre cómo instalar dependencias, configurar el servicio en una Raspberry Pi y poner en marcha el sistema, consulta la **[Guía de Despliegue](file:///c:/Users/ferna/Desktop/Raspberry-PI-Project/DEPLOYMENT.md)**.

---
