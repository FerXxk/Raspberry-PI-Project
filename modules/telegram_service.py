import logging
import threading
import time
import os
import requests
import asyncio
from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TelegramService")

class TelegramService:
    def __init__(self, token, chat_id):
        self.token = token
        self.chat_id = chat_id
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
            # -nodisp: no display, -autoexit: exit after playing
            cmd = f"ffplay -nodisp -autoexit -hide_banner \"{download_path}\"" 
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
