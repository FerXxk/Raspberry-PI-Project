import os
import shutil
import time
import logging

class GestorAlmacenamiento:
    def __init__(self, path_videos, max_days=7, max_usage_percent=90):
        self.path = path_videos
        self.max_days = max_days
        self.max_usage_percent = max_usage_percent
        
        # Configurar logging básico si no existe
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - [ALMACENAMIENTO] - %(message)s')
        self.logger = logging.getLogger(__name__)

    def obtener_espacio_usado(self):
        """Devuelve el porcentaje de uso del disco donde está la carpeta."""
        try:
            total, used, free = shutil.disk_usage(self.path)
            percent = (used / total) * 100
            return percent
        except FileNotFoundError:
            self.logger.error(f"Ruta no encontrada: {self.path}")
            return 0

    def obtener_estado_detallado(self):
        """Devuelve un diccionario con info detallada del disco."""
        try:
            total, used, free = shutil.disk_usage(self.path)
            percent = (used / total) * 100
            # Convert bytes to MB
            total_mb = total / (1024 * 1024)
            used_mb = used / (1024 * 1024)
            free_mb = free / (1024 * 1024)
            
            return {
                "total_mb": total_mb,
                "used_mb": used_mb,
                "free_mb": free_mb,
                "percent": percent
            }
        except FileNotFoundError:
            return None

    def limpiar_por_antiguedad(self):
        """Elimina archivos más antiguos que max_days."""
        if not os.path.exists(self.path):
            return

        ahora = time.time()
        limite_segundos = self.max_days * 86400 # días a segundos

        self.logger.info(f"Comprobando archivos antiguos (> {self.max_days} días)...")
        
        archivos_eliminados = 0
        for filename in os.listdir(self.path):
            filepath = os.path.join(self.path, filename)
            
            # Solo procesar archivos (evitar borrar directorios por error)
            if not os.path.isfile(filepath):
                continue
                
            estat = os.stat(filepath)
            edad = ahora - estat.st_mtime
            
            if edad > limite_segundos:
                try:
                    os.remove(filepath)
                    self.logger.info(f"Eliminado por antigüedad: {filename}")
                    archivos_eliminados += 1
                except OSError as e:
                    self.logger.error(f"Error al eliminar {filename}: {e}")
        
        if archivos_eliminados > 0:
            self.logger.info(f"Total eliminados por antigüedad: {archivos_eliminados}")

    def limpiar_por_espacio(self):
        """Si el espacio supera el umbral, borra los videos más antiguos hasta bajar un 5% del límite."""
        uso_actual = self.obtener_espacio_usado()
        
        if uso_actual < self.max_usage_percent:
            return

        self.logger.warning(f"Espacio crítico ({uso_actual:.1f}%). Iniciando limpieza de emergencia...")
        
        # Objetivo: Bajar un 5% por debajo del límite para no estar borrando constantemente
        objetivo_uso = self.max_usage_percent - 5
        
        # Obtener lista de archivos con su fecha de modificación
        archivos = []
        for f in os.listdir(self.path):
            fp = os.path.join(self.path, f)
            if os.path.isfile(fp):
                archivos.append((fp, os.path.getmtime(fp)))
        
        # Ordenar por fecha (más antiguos primero)
        archivos.sort(key=lambda x: x[1])
        
        eliminados = 0
        for filepath, _ in archivos:
            if self.obtener_espacio_usado() <= objetivo_uso:
                break
                
            try:
                os.remove(filepath)
                self.logger.info(f"Eliminado por espacio: {os.path.basename(filepath)}")
                eliminados += 1
            except OSError as e:
                self.logger.error(f"Error al eliminar {filepath}: {e}")
                
        self.logger.info(f"Limpieza de espacio completada. Archivos eliminados: {eliminados}. Uso actual: {self.obtener_espacio_usado():.1f}%")

    def ejecutar_limpieza(self):
        """Ejecuta ambas políticas de limpieza."""
        try:
            self.limpiar_por_antiguedad()
            self.limpiar_por_espacio()
        except Exception as e:
            self.logger.error(f"Error durante el ciclo de limpieza: {e}")
