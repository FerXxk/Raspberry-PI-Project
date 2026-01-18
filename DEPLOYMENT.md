# Guía de Despliegue - Raspberry PI Project

Este documento detalla los pasos para desplegar el servicio de vigilancia en una Raspberry Pi.

## 1. Instalación de Dependencias

Primero, asegúrate de tener el sistema actualizado y las dependencias de Python instaladas:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv libgl1 -y
```

Instala las librerías necesarias del proyecto:

```bash
pip install -r config/requirements.txt
```

## 2. Configuración del Servicio (Systemd)

Para que el servicio se inicie automáticamente al arrancar la Raspberry Pi, utilizamos `systemd`.

1. Copia el archivo de servicio a la ruta del sistema (ajusta las rutas internas si es necesario):
   ```bash
   sudo cp config/vigilancia.service /etc/systemd/system/
   ```

2. Recarga el demonio de systemd:
   ```bash
   sudo systemctl daemon-reload
   ```

3. Habilita el servicio para que inicie al arranque:
   ```bash
   sudo systemctl enable vigilancia.service
   ```

4. Inicia el servicio ahora:
   ```bash
   sudo systemctl start vigilancia.service
   ```

## 3. Monitoreo y Logs

Puedes ver el estado del servicio y los logs en tiempo real con:

```bash
sudo systemctl status vigilancia.service
journalctl -u vigilancia.service -f
```

## 4. Estructura de Archivos Importantes

- `run.py`: Punto de entrada del sistema.
- `config/config.py`: Archivo de configuración principal (Tokens de Telegram, Rutas NAS, etc.).
- `app/`: Contiene la interfaz web (Flask).
- `modules/`: Lógica central del sistema (Cámara, Sensores, Almacenamiento).
