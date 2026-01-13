# 🛡️ Sistema de Vigilancia Inteligente con NAS Local

Este proyecto consiste en una solución de seguridad basada en Edge Computing que utiliza una Raspberry Pi 4 para detectar movimiento, grabar clips de vídeo automáticamente y servirlos a través de una red local mediante un almacenamiento NAS.

## 🚀 Estado Actual del Proyecto

Actualmente, el proyecto utiliza la librería moderna **Picamera2** para garantizar compatibilidad con los sistemas operativos Raspberry Pi OS más recientes (Bullseye/Bookworm).

### 1. Infraestructura de Almacenamiento (NAS)
- **Montaje Persistente**: Se ha configurado un disco USB con montaje automático en la ruta **/mnt/grabaciones_camara/**.
- **Servicio Samba**: El sistema comparte dicha carpeta en la red local para facilitar el acceso a los clips.
- **Formato de Archivo**: Los videos se guardan con el formato de fecha `DD-MM-YYYY__HH-MM-SS.avi` para facilitar su ordenación.

### 2. Núcleo de Visión Artificial (Python - `vigilancia.py`)
- **Motor de Captura**: Se utiliza **Picamera2** (basado en `libcamera`) para obtener frames en formato raw de alta eficiencia.
- **Algoritmo de Detección**: Uso de **OpenCV** para realizar sustracción de fondo, suavizado (Gaussian Blur) y detección de contornos.
- **Lógica de Grabación Inteligente**:
    - El sistema opera en un **bucle único de alto rendimiento** (Single-Loop State Machine) para evitar conflictos de hardware con la cámara.
    - **Smart Stop**: La grabación se detiene automáticamente si:
        1.  Pasan **5 segundos** sin detectar movimiento (para ahorrar espacio).
        2.  O se alcanza la duración máxima de **60 segundos** (para evitar archivos corruptos o gigantes).

## 🛠️ Stack Tecnológico
- **Hardware**: Raspberry Pi 4, Raspberry Pi Camera Module, USB Drive.
- **S.O.**: Raspberry Pi OS (64-bit).
- **Lenguaje**: Python 3.11+.
- **Librerías Clave**: 
    - `picamera2`: Control de hardware de cámara.
    - `opencv-python`: Procesamiento de imagen.
    - `numpy`: Operaciones de matrices.

## 📂 Configuraciones Clave
El script `vigilancia.py` permite ajustar variables globales fácilmente:
```python
PATH_NAS = "/mnt/grabaciones_camara/"
MIN_AREA = 5000                # Sensibilidad al movimiento
MAX_DURACION = 60              # Tiempo límite por video
TIEMPO_SIN_MOVIMIENTO = 5      # Tiempo de espera antes de cortar
```

## 🔍 Próximos Pasos
- **Validación de Red**: Resolver posibles bloqueos de visibilidad del NAS en entornos corporativos.
- **Auto-purge**: Script para borrar videos antiguos cuando el disco se llene.
- **Interfaz Web**: Implementar un servidor Flask ligero para ver la cámara en vivo desde el navegador.