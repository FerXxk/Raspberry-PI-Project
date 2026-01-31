# Deployment Guide - Raspberry PI Project

This document details the steps to deploy the surveillance service on a Raspberry Pi.

## 1. System Preparation and Dependencies

Ensure the Raspberry Pi has access to all available storage and the necessary libraries:

1. **Expand Filesystem**:
   ```bash
   sudo raspi-config
   ```
   Go to `Advanced Options` > `Expand Filesystem`. Reboot the Raspberry Pi after this step.

2. **Install System Dependencies**:
   ```bash
   sudo apt update && sudo apt upgrade -y
   sudo apt install -y python3-pip python3-picamera2 python3-opencv ffmpeg python3-sense-hat libgl1
   ```

3. **Install Python Libraries**:
   ```bash
   pip install -r config/requirements.txt
   ```

## 2. Configuration of Additional Services

### Local NAS (Samba)
To access recordings from any device on the local network:
```bash
bash scripts/setup_samba.sh
```
This will configure a password-protected share at `/mnt/grabaciones_camara/`. (user: pi, password: defined in the script)

### Remote Access (Tailscale VPN)
To view the camera from outside your home without opening ports:
```bash
bash scripts/setup_tailscale.sh
```
Follow the link that appears in the terminal to link the Raspberry Pi to your account.

When the Raspberry Pi is linked to your account, you can access the IP assigned to the Raspberry Pi (100.xxx.xxx.xxx) from any device with the Tailscale app.

Therefore, you will be able to access the recordings folder and the streaming website from both your PC and your mobile.

## 3. Service Configuration (Systemd)

To make the system start automatically:

1. Copy the service file:
   ```bash
   sudo cp config/vigilancia.service /etc/systemd/system/
   ```

2. Enable and start the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable vigilancia.service
   sudo systemctl start vigilancia.service
   ```

   This will ensure the system starts automatically when the Raspberry Pi is turned on or after an unexpected shutdown.

## 4. Monitoring and Logs
```bash
journalctl -u vigilancia.service -f
```
You will be able to see the system logs in real-time.

## 5. Final Adjustments

If you want to change the system configuration, you can edit the `config/config.py` file to adjust camera parameters, motion detection, recording, storage, audio, remote access, Telegram, and operation mode.



