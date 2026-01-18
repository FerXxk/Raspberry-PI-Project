#!/bin/bash

# Script para configurar la Raspberry Pi como un servidor NAS (Samba)
# para la carpeta de grabaciones de la cámara.

echo "🎬 Configurando servidor NAS para grabaciones..."

# 1. Instalar Samba si no está presente
sudo apt update
sudo apt install -y samba samba-common-bin

# 2. Definir la ruta de grabaciones (debe coincidir con config.py)
SHARE_PATH="/mnt/grabaciones_camara"

# 3. Crear el directorio si no existe y dar permisos
sudo mkdir -p $SHARE_PATH
sudo chown -R pi:pi $SHARE_PATH
sudo chmod -R 777 $SHARE_PATH

# 4. Backup de la configuración original de Samba
sudo cp /etc/samba/smb.conf /etc/samba/smb.conf.bak

# 5. Añadir la configuración del recurso compartido al final de smb.conf
# Solo si no existe ya una sección [Grabaciones]
if ! grep -q "\[Grabaciones\]" /etc/samba/smb.conf; then
    sudo tee -a /etc/samba/smb.conf <<EOF

[Grabaciones]
   path = $SHARE_PATH
   writeable = yes
   browseable = yes
   public = no
   valid users = pi
   create mask = 0777
   directory mask = 0777
   force user = pi
EOF
    echo "✅ Recurso [Grabaciones] añadido a smb.conf (Acceso privado)"
else
    echo "ℹ️ El recurso [Grabaciones] ya existe en smb.conf"
fi

# 6. Configurar contraseña para el usuario 'pi'
echo "🔐 Configurando contraseña para el acceso al NAS..."
echo "Por favor, introduce la contraseña para el usuario 'pi' en Samba:"
sudo smbpasswd -a pi

# 7. Reiniciar el servicio de Samba
sudo systemctl restart smbd
sudo systemctl enable smbd

echo "🚀 Servidor NAS activado correctamente."
echo "Carpeta compartida: \\\\$(hostname).local\\Grabaciones"
echo "Usuario: pi"
echo "Recuerda usar la contraseña que acabas de configurar."
