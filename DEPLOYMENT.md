# Guía de Despliegue - Raspberry PI Project

Este documento detalla los pasos para desplegar el servicio de vigilancia en una Raspberry Pi.

## 1. Preparación del Sistema y Dependencias

Asegúrate de que la Raspberry Pi tenga acceso a todo el almacenamiento disponible y las librerías necesarias:

1. **Expandir Sistema de Archivos**:
   ```bash
   sudo raspi-config
   ```
   Ve a `Advanced Options` > `Expand Filesystem`. Reinicia la Raspberry Pi después de este paso.

2. **Instalar Dependencias del Sistema**:
   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo apt install -y python3-pip python3-picamera2 python3-opencv ffmpeg python3-sense-hat libgl1
   ```

3. **Instalar Librerías de Python**:
   ```bash
   pip install -r config/requirements.txt
   ```

## 2. Configuración de Servicios Adicionales

### NAS Local (Samba)
Para acceder a las grabaciones desde cualquier dispositivo de la red local:
```bash
bash scripts/setup_samba.sh
```
Esto configurará un recurso compartido con contraseña en `/mnt/grabaciones_camara/`. (usuario: pi contraseña: se define en el script)

### Acceso Remoto (Tailscale VPN)
Para ver la cámara desde fuera de casa sin abrir puertos:
```bash
bash scripts/setup_tailscale.sh
```
Sigue el enlace que aparecerá en la terminal para vincular la Raspberry Pi a tu cuenta.

Cuando la Raspberry Pi se vincule a tu cuenta, puedes acceder a la IP que se le asigna a la Raspberry Pi (100.xxx.xxx.xxx) desde cualquier dispositivo con la app de Tailscale.

Por lo que podrás acceder a la carpeta de grabaciones y a la web de streaming desde tu PC y desde tu móvil.

## 3. Configuración del Servicio (Systemd)

Para que el sistema se inicie automáticamente:

1. Copia el archivo de servicio:
   ```bash
   sudo cp config/vigilancia.service /etc/systemd/system/
   ```

2. Activa e inicia el servicio:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable vigilancia.service
   sudo systemctl start vigilancia.service
   ```

   Esto hará que el sistema se inicie automáticamente al encender la Raspberry Pi o ante un cierre inesperado.

## 4. Monitoreo y Logs
```bash
journalctl -u vigilancia.service -f
```
Podrás ver los logs del sistema en tiempo real.

## 5. Ajustes finales

Si quieres cambiar la configuración del sistema, puedes editar el archivo `config/config.py` para ajustar los parámetros de la cámara, la detección de movimiento, la grabación, el almacenamiento, el audio, el acceso remoto, el Telegram y el modo de operación.



