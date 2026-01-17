import os
import subprocess
import logging
import config

logger = logging.getLogger("VPNService")

def check_vpn_status():
    """Checks if Tailscale is up and running."""
    try:
        # Check if tailscale is installed
        subprocess.run(["tailscale", "--version"], capture_output=True, check=True)
        
        # Check status
        result = subprocess.run(["tailscale", "status"], capture_output=True, text=True)
        if "Tailscale is stopped" in result.stdout or result.returncode != 0:
            return False
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def start_vpn():
    """Starts Tailscale VPN if enabled and not running."""
    if not config.AUTO_START_VPN:
        return

    logger.info("Checking VPN status...")
    if check_vpn_status():
        logger.info("VPN is already running.")
    else:
        logger.info("VPN is not running. Attempting to start Tailscale...")
        try:
            # We use 'tailscale up' which is safe if already authenticated.
            # If not authenticated, it might print a login URL.
            subprocess.Popen(["sudo", "tailscale", "up"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            logger.info("Tailscale 'up' command sent.")
        except Exception as e:
            logger.error(f"Failed to start VPN: {e}")
