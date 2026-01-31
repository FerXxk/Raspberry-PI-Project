import logging
import threading
import time
import os
import requests
import asyncio
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from telegram.ext import CommandHandler
import config

# Configuración de logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Telegram")

# Silenciar logs innecesarios de librerías
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.getLogger("telegram.ext").setLevel(logging.WARNING)

class TelegramService:
    def __init__(self, token, chat_id, mode_manager=None):
        self.token = token
        self.chat_id = chat_id
        self.mode_manager = mode_manager
        self.app = None
        self.bot = None
        self.loop = None
        self.thread = None
        
        if self.token == "TU_TOKEN_AQUI":
            logger.warning("Token de Telegram no configurado.")
            return

        try:
            self.app = ApplicationBuilder().token(self.token).build()
            
            # Manejador de mensajes de voz
            voice_handler = MessageHandler(filters.VOICE, self.handle_voice)
            self.app.add_handler(voice_handler)
            
            # Comandos para cambiar de modo
            
            self.app.add_handler(CommandHandler("portero", self.handle_modo1))
            self.app.add_handler(CommandHandler("vigilancia", self.handle_modo2))
            self.app.add_handler(CommandHandler("estado", self.handle_estado))
            
            self.bot = self.app.bot
            
        except Exception as e:
            logger.error(f"Fallo al iniciar el servicio de Telegram: {e}")

    def start(self):
        if not self.app:
            return

        # Ejecutar polling en un hilo separado
        self.thread = threading.Thread(target=self._run_polling, daemon=True)
        self.thread.start()
        logger.info("Servicio Telegram iniciado.")

    def _run_polling(self):
        # Nuevo bucle para este hilo
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.loop = loop
        
        # Iniciar polling (sin señales para no chocar con Flask)
        try:
            loop.run_until_complete(self.app.run_polling(stop_signals=None)) 
        except Exception as e:
            logger.error(f"Telegram polling error: {e}")
        finally:
            loop.close()

    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            file = await context.bot.get_file(update.message.voice.file_id)
            
            # Descargar audio
            download_path = os.path.join(config.BASE_DIR, "voice_message.ogg")
            await file.download_to_drive(download_path)
            
            logger.info(f"Mensaje de voz guardado en {download_path}")
            
            # Reproducción con ffplay
            await context.bot.send_message(chat_id=update.effective_chat.id, text="Mensaje de voz recibido. Reproduciendo...")
            cmd = f"ffplay -nodisp -autoexit -hide_banner -volume {config.VOLUME_LEVEL} \"{download_path}\"" 
            os.system(cmd)
            
            # Limpieza
            if os.path.exists(download_path):
                os.remove(download_path)
                logger.info("Archivo de voz eliminado.")
                
        except Exception as e:
            logger.error(f"Error handling voice message: {e}")

    def send_alert(self, image_path, caption="Movimiento detectado"):
        """Envía una foto al chat configurado."""
        if not self.token or self.chat_id == "TU_CHAT_ID_AQUI":
            return

        def _send():
            try:
                url = f"https://api.telegram.org/bot{self.token}/sendPhoto"
                with open(image_path, 'rb') as photo:
                    files = {'photo': photo}
                    data = {'chat_id': self.chat_id, 'caption': caption}
                    response = requests.post(url, files=files, data=data)
                    if response.status_code != 200:
                         logger.error(f"Error al enviar a Telegram: {response.text}")
                    else:
                        logger.info("Alerta de Telegram enviada.")
            except Exception as e:
                logger.error(f"Error sending Telegram alert: {e}")

        # Hilo separado para no bloquear la cámara
        sender_thread = threading.Thread(target=_send)
        sender_thread.start()
    
    async def handle_modo1(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /portero."""
        try:
            if self.mode_manager:
                changed = self.mode_manager.set_mode(1)
                if changed:
                    await update.message.reply_text(
                        "OK: Modo cambiado a: Modo 1 - Portero\n"
                        "El boton del SenseHat ahora funciona como timbre.\n"
                        "Se enviara una foto cuando se presione."
                    )
                else:
                    await update.message.reply_text("INFO: Ya estás en Modo 1 - Portero")
            else:
                await update.message.reply_text(" Gestor de modos no disponible")
        except Exception as e:
            logger.error(f"Error en /modo1: {e}")
            await update.message.reply_text(f" Error: {e}")
    
    async def handle_modo2(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /vigilancia."""
        try:
            if self.mode_manager:
                changed = self.mode_manager.set_mode(2)
                if changed:
                    await update.message.reply_text(
                        "OK: Modo cambiado a: Modo 2 - Video Vigilancia\n"
                        "Deteccion de movimiento activada.\n"
                        "Se grabara video cuando se detecte movimiento."
                    )
                else:
                    await update.message.reply_text("INFO: Ya estás en Modo 2 - Video Vigilancia")
            else:
                await update.message.reply_text(" Gestor de modos no disponible")
        except Exception as e:
            logger.error(f"Error en /modo2: {e}")
            await update.message.reply_text(f" Error: {e}")
    
    async def handle_estado(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Comando /estado."""
        try:
            if self.mode_manager:
                current_mode = self.mode_manager.get_mode()
                mode_desc = self.mode_manager.get_mode_description()
                
                status_msg = f"ESTADO DEL SISTEMA\n\n"
                status_msg += f"Modo Actual: {current_mode}\n"
                status_msg += f"Descripcion: {mode_desc}\n\n"
                
                if current_mode == 1:
                    status_msg += "Presiona el boton del SenseHat para tomar una foto"
                else:
                    status_msg += "Sistema vigilando - grabara al detectar movimiento"
                
                await update.message.reply_text(status_msg)
            else:
                await update.message.reply_text(" Gestor de modos no disponible")
        except Exception as e:
            logger.error(f"Error en /estado: {e}")
            await update.message.reply_text(f" Error: {e}")
