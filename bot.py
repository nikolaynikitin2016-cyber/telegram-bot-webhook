import os
import logging
from flask import Flask, request, jsonify
import asyncio
import telegram

# ============ НАСТРОЙКИ ============
TOKEN = "8444088116:AAENC53CGKlDc-DCwrHUbh_UA4NRT0m0rjc"
# ===================================

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Создаём приложение Flask и объект бота
app = Flask(__name__)
bot = telegram.Bot(token=TOKEN)

@app.route('/webhook', methods=['POST'])
def webhook():
    """Синхронная обёртка для асинхронной обработки сообщений."""
    try:
        # Получаем данные от Telegram
        update_data = request.get_json(force=True)
        logger.info(f"Получен webhook запрос")

        # Создаём и запускаем асинхронную задачу в новом цикле событий
        # Это самый надёжный способ для Flask + asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(handle_update(update_data))
        loop.close()

        return 'OK', 200
    except Exception as e:
        logger.error(f"Критическая ошибка в webhook: {e}", exc_info=True)
        # Всегда возвращаем 200, чтобы Telegram не слал дубликаты
        return 'OK', 200

async def handle_update(update_data):
    """Асинхронная обработка одного обновления."""
    try:
        # Преобразуем JSON в объект Update
        update = telegram.Update.de_json(update_data, bot)

        # Проверяем, есть ли сообщение
        if not update.message:
            logger.warning("Получен update без message")
            return

        chat_id = update.message.chat.id
        user_text = update.message.text
        logger.info(f"Обработка сообщения '{user_text}' от {chat_id}")

        # Отвечаем пользователю (ОБЯЗАТЕЛЬНО С await)
        await bot.send_message(chat_id=chat_id, text=f"✅ Эхо: {user_text}")

        logger.info(f"Ответ успешно отправлен в чат {chat_id}")

    except Exception as e:
        logger.error(f"Ошибка при обработке update: {e}", exc_info=True)

@app.route('/')
def index():
    """Проверка, что сервер работает."""
    return "🤖 Бот работает! Webhook endpoint: /webhook"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🚀 Запуск сервера на порту {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
