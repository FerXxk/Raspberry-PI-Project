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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TelegramService")

# Suppress noisy HTTP logs from telegram libraries
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
            logger.warning("Telegram Token not set. Telegram service will be disabled.")
            return

        try:
            # We use ApplicationBuilder which is the standard for python-telegram-bot v20+
            self.app = ApplicationBuilder().token(self.token).build()
            
            # Add handler for voice messages
            voice_handler = MessageHandler(filters.VOICE, self.handle_voice)
            self.app.add_handler(voice_handler)
            
            # Add command handlers for mode switching
            
            self.app.add_handler(CommandHandler("portero", self.handle_modo1))
            self.app.add_handler(CommandHandler("vigilancia", self.handle_modo2))
            self.app.add_handler(CommandHandler("estado", self.handle_estado))
            
            self.bot = self.app.bot
            
        except Exception as e:
            logger.error(f"Failed to initialize Telegram Service: {e}")

    def start(self):
        if not self.app:
            return

        # Run bot polling in a separate thread with its own asyncio loop
        self.thread = threading.Thread(target=self._run_polling, daemon=True)
        self.thread.start()
        logger.info("Telegram Service started (polling).")

    def _run_polling(self):
        # Create a new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.loop = loop
        
        # Run polling
        try:
            loop.run_until_complete(self.app.run_polling(stop_signals=None)) # Disable signal handling to avoid interfering with Flask
        except Exception as e:
            logger.error(f"Telegram polling error: {e}")
        finally:
            loop.close()

    async def handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            file = await context.bot.get_file(update.message.voice.file_id)
            
            # Define path
            download_path = os.path.join(config.BASE_DIR, "voice_message.ogg")
            await file.download_to_drive(download_path)
            
            logger.info(f"Voice message received and saved to {download_path}")
            
            # Play audio
            # Using os.system with aplay (for wav) or cvlc/mpg123/ffplay for ogg.
            # RPi usually has aplay. OGG might need 'vorbis-tools' (ogg123) or ffmpeg.
            # We'll try a generic command or expect 'ffplay'/'cvlc'.
            # For robustness, let's assume 'cvlc' (VLC) or 'ffplay' is available or 'aplay' if converted.
            # Simplified: just try to play.
            
            # Send acknowledgement
            await context.bot.send_message(chat_id=update.effective_chat.id, text="🔊 Mensaje de voz recibido. Reproduciendo...")
            
            # Play command (Adjust based on installed tools)
            # -nodisp: no display, -autoexit: exit after playing, -volume: set startup volume
            cmd = f"ffplay -nodisp -autoexit -hide_banner -volume {config.VOLUME_LEVEL} \"{download_path}\"" 
            os.system(cmd)
            
            # Cleanup
            if os.path.exists(download_path):
                os.remove(download_path)
                logger.info("Voice message deleted.")
                
        except Exception as e:
            logger.error(f"Error handling voice message: {e}")

    def send_alert(self, image_path, caption="Movimiento detectado"):
        """
        Sends an image to the configured chat_id.
        This method is thread-safe and can be called from Camera thread.
        Uses synchronous requests for simplicity in calling from non-async context,
        or we could schedule it on the loop. For robustness, standard requests is fine for sending.
        """
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
                         logger.error(f"Failed to send Telegram alert: {response.text}")
                    else:
                        logger.info("Telegram alert sent.")
            except Exception as e:
                logger.error(f"Error sending Telegram alert: {e}")

        # Run in a separate thread to not block the Camera loop
        sender_thread = threading.Thread(target=_send)
        sender_thread.start()
    
    async def handle_modo1(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /modo1 command to switch to Doorbell mode."""
        try:
            if self.mode_manager:
                changed = self.mode_manager.set_mode(1)
                if changed:
                    await update.message.reply_text(
                        "✅ Modo cambiado a: Modo 1 - Portero\n"
                        "🔔 El botón del SenseHat ahora funciona como timbre.\n"
                        "📸 Se enviará una foto cuando se presione."
                    )
                else:
                    await update.message.reply_text("ℹ️ Ya estás en Modo 1 - Portero")
            else:
                await update.message.reply_text("❌ Mode manager no disponible")
        except Exception as e:
            logger.error(f"Error handling /modo1: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def handle_modo2(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /modo2 command to switch to Video Surveillance mode."""
        try:
            if self.mode_manager:
                changed = self.mode_manager.set_mode(2)
                if changed:
                    await update.message.reply_text(
                        "✅ Modo cambiado a: Modo 2 - Video Vigilancia\n"
                        "🎥 Detección de movimiento activada.\n"
                        "📹 Se grabará video cuando se detecte movimiento."
                    )
                else:
                    await update.message.reply_text("ℹ️ Ya estás en Modo 2 - Video Vigilancia")
            else:
                await update.message.reply_text("❌ Mode manager no disponible")
        except Exception as e:
            logger.error(f"Error handling /modo2: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
    
    async def handle_estado(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /estado command to report current mode and status."""
        try:
            if self.mode_manager:
                current_mode = self.mode_manager.get_mode()
                mode_desc = self.mode_manager.get_mode_description()
                
                status_msg = f"📊 Estado del Sistema\n\n"
                status_msg += f"🔧 Modo Actual: {current_mode}\n"
                status_msg += f"📝 Descripción: {mode_desc}\n\n"
                
                if current_mode == 1:
                    status_msg += "🔔 Presiona el botón del SenseHat para tomar una foto"
                else:
                    status_msg += "🎥 Sistema vigilando - grabará al detectar movimiento"
                
                await update.message.reply_text(status_msg)
            else:
                await update.message.reply_text("❌ Mode manager no disponible")
        except Exception as e:
            logger.error(f"Error handling /estado: {e}")
            await update.message.reply_text(f"❌ Error: {e}")
