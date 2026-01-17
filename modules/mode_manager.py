import logging
import threading
import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ModeManager")

class ModeManager:
    """
    Thread-safe mode manager for switching between operation modes.
    Mode 1: Doorbell (button-triggered photo)
    Mode 2: Video Surveillance (motion-based recording)
    """
    def __init__(self, initial_mode=None):
        self.current_mode = initial_mode or config.OPERATION_MODE
        self.lock = threading.Lock()
        self.observers = []  # Callbacks to notify on mode change
        
        logger.info(f"ModeManager initialized with mode {self.current_mode}: {config.MODE_DESCRIPTIONS.get(self.current_mode, 'Unknown')}")
    
    def get_mode(self):
        """Returns the current mode (thread-safe)."""
        with self.lock:
            return self.current_mode
    
    def get_mode_description(self):
        """Returns the description of the current mode."""
        mode = self.get_mode()
        return config.MODE_DESCRIPTIONS.get(mode, "Modo Desconocido")
    
    def set_mode(self, new_mode):
        """
        Sets a new mode and notifies all observers.
        Returns True if mode changed, False if already in that mode.
        """
        if new_mode not in [1, 2]:
            logger.error(f"Invalid mode: {new_mode}. Must be 1 or 2.")
            return False
        
        with self.lock:
            if self.current_mode == new_mode:
                logger.info(f"Already in mode {new_mode}")
                return False
            
            old_mode = self.current_mode
            self.current_mode = new_mode
            logger.info(f"Mode changed: {old_mode} → {new_mode} ({config.MODE_DESCRIPTIONS.get(new_mode, 'Unknown')})")
        
        # Notify observers outside the lock to avoid deadlocks
        self._notify_observers(old_mode, new_mode)
        return True
    
    def register_observer(self, callback):
        """
        Register a callback to be called when mode changes.
        Callback signature: callback(old_mode, new_mode)
        """
        self.observers.append(callback)
        logger.info(f"Observer registered: {callback.__name__ if hasattr(callback, '__name__') else 'anonymous'}")
    
    def _notify_observers(self, old_mode, new_mode):
        """Notify all registered observers of mode change."""
        for observer in self.observers:
            try:
                observer(old_mode, new_mode)
            except Exception as e:
                logger.error(f"Error notifying observer {observer}: {e}")
