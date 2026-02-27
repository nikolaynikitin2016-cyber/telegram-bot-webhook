import os
import logging
from flask import Flask, request
import telegram

TOKEN = "8444088116:AAENC53CGKlDc-DCwrHUbh_UA4NRT0m0rjc"
bot = telegram.Bot(token=TOKEN)
app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/webhook', methods=['POST'])
async def webhook():
    """Обработчик входящих сообщений от Telegram."""
    try:
        # Получаем и разбираем обновление от Telegram
        update = telegram.Update.de_json(request.get_json(force=True), bot)
        chat_id = update.message.chat.id
        user_text = update.message.text
        logger.info(f"Получено сообщение: '{user_text}' от чата {chat_id}")

        # Здесь будет отправка запроса в CaptainAgent
        # Пока просто отправляем эхо-ответ
        await bot.send_message(chat_id=chat_id, text=f"Ты написал: {user_text}")

        return 'OK', 200
    except Exception as e:
        logger.error(f"Ошибка при обработке webhook: {e}", exc_info=True)
        # Важно всегда возвращать 200, даже при ошибке, чтобы Telegram не слал сообщение повторно
        return 'OK', 200

@app.route('/')
def index():
    return "Бот работает"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
