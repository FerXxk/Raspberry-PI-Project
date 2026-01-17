#!/bin/bash

# Script de instalación y configuración de Tailscale VPN para Raspberry Pi
# Ejecutar con: sudo bash setup_tailscale.sh

echo "=========================================="
echo "    INSTALACIÓN DE TAILSCALE VPN"
echo "=========================================="

# 1. Instalar Tailscale
if ! command -v tailscale &> /dev/null; then
    echo "[Info] Instalando Tailscale..."
    curl -fsSL https://tailscale.com/install.sh | sh
else
    echo "[Info] Tailscale ya está instalado."
fi

# 2. Habilitar IP Forwarding (necesario para usar la RPi como subnet router si se desea)
echo "[Info] Habilitando IP Forwarding..."
echo 'net.ipv4.ip_forward = 1' | sudo tee -a /etc/sysctl.d/99-tailscale.conf
echo 'net.ipv6.conf.all.forwarding = 1' | sudo tee -a /etc/sysctl.d/99-tailscale.conf
sudo sysctl -p /etc/sysctl.d/99-tailscale.conf

# 3. Iniciar Tailscale
echo "=========================================="
echo "    AUTENTICACIÓN REQUERIDA"
echo "=========================================="
echo "Se iniciará Tailscale. Por favor, copia el enlace que aparecerá a continuación"
echo "y ábrelo en tu navegador para autorizar este dispositivo en tu red."
echo ""
sudo tailscale up

echo ""
echo "=========================================="
echo "    ESTADO DE LA CONEXIÓN"
echo "=========================================="
tailscale ip -4
echo ""
echo "¡Listo! Ahora puedes acceder a esta Raspberry Pi usando la IP de arriba"
echo "desde cualquier dispositivo conectado a tu red Tailscale."
echo ""
echo "Para acceder a la web de vigilancia, visita: http://<IP-TAILSCALE>:5000"
