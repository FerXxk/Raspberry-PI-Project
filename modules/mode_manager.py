import logging
import threading
import config

# Configuración de logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Modos")

class ModeManager:
    """Gestor de modos: 1 = Portero, 2 = Vigilancia."""
    def __init__(self, initial_mode=None):
        self.current_mode = initial_mode or config.OPERATION_MODE
        self.lock = threading.Lock()
        self.observers = []  # Callbacks para avisar de cambios de modo
        
        logger.info(f"ModeManager initialized with mode {self.current_mode}: {config.MODE_DESCRIPTIONS.get(self.current_mode, 'Unknown')}")
    
    def get_mode(self):
        """Modo actual."""
        with self.lock:
            return self.current_mode
    
    def get_mode_description(self):
        """Descripción del modo activo."""
        mode = self.get_mode()
        return config.MODE_DESCRIPTIONS.get(mode, "Modo Desconocido")
    
    def set_mode(self, new_mode):
        """Cambia el modo y avisa a los observadores."""
        if new_mode not in [1, 2]:
            logger.error(f"Modo inválido: {new_mode}. Debe ser 1 o 2.")
            return False
        
        with self.lock:
            if self.current_mode == new_mode:
                logger.info(f"Ya se encuentra en modo {new_mode}")
                return False
            
            old_mode = self.current_mode
            self.current_mode = new_mode
            logger.info(f"Mode changed: {old_mode} → {new_mode} ({config.MODE_DESCRIPTIONS.get(new_mode, 'Unknown')})")
        
        # Avisar a los observadores fuera del lock para evitar bloqueos
        self._notify_observers(old_mode, new_mode)
        return True
    
    def register_observer(self, callback):
        """Registrar callback para cambios de modo."""
        self.observers.append(callback)
        logger.info(f"Observador registrado: {callback.__name__ if hasattr(callback, '__name__') else 'anónimo'}")
    
    def _notify_observers(self, old_mode, new_mode):
        """Notificar a todos los observadores."""
        for observer in self.observers:
            try:
                observer(old_mode, new_mode)
            except Exception as e:
                logger.error(f"Error notifying observer {observer}: {e}")
