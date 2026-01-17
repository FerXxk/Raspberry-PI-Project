import os
import subprocess
import logging

logger = logging.getLogger("Samba")

def ensure_samba_started():
    """
    Checks if the samba service (smbd) is running.
    If not, it tries to start it. This assumes setup_samba.sh has been run once.
    """
    try:
        # Check status
        result = subprocess.run(['systemctl', 'is-active', 'smbd'], capture_output=True, text=True)
        if result.stdout.strip() == 'active':
            logger.info("El servicio Samba (NAS) está activo.")
            return True
        
        logger.info("Samba no está activo. Intentando iniciar...")
        # Try to start it
        subprocess.run(['sudo', 'systemctl', 'start', 'smbd'], check=True)
        logger.info("Samba iniciado correctamente.")
        return True
    except Exception as e:
        logger.error(f"Error al verificar/iniciar Samba: {e}")
        logger.warning("Asegúrate de haber ejecutado 'bash scripts/setup_samba.sh' primero.")
        return False
