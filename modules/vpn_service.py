import os
import subprocess
import logging
import config

logger = logging.getLogger("VPNService")

def check_vpn_status():
    """Verifica si Tailscale está activo."""
    try:
        # Verificar si tailscale está instalado
        subprocess.run(["tailscale", "--version"], capture_output=True, check=True)
        
        # Comprobar estado
        result = subprocess.run(["tailscale", "status"], capture_output=True, text=True)
        if "Tailscale is stopped" in result.stdout or result.returncode != 0:
            return False
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def start_vpn():
    """Inicia Tailscale si está habilitado."""
    if not config.AUTO_START_VPN:
        return

    logger.info("Verificando VPN...")
    if check_vpn_status():
        logger.info("La VPN ya está activa.")
    else:
        logger.info("La VPN no está activa. Intentando iniciar Tailscale...")
        try:
            # Intento de conexión
            subprocess.Popen(["sudo", "tailscale", "up"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            logger.info("Comando 'tailscale up' enviado.")
        except Exception as e:
            logger.error(f"Fallo al iniciar VPN: {e}")
