import os
import logging
from flask import Flask, request, jsonify
import telegram
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import asyncio

# ============ НАСТРОЙКИ ============
TOKEN = "8512903035:AAGaNTmKbfbzdYlXajySUoGv2smiBnTyAhg"
# ===================================

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Создаем Flask приложение
app = Flask(__name__)

# Глобальные переменные для бота
bot = telegram.Bot(token=TOKEN)
application = None

# Функция инициализации приложения
async def init_application():
    global application
    if application is None:
        logger.info("🔄 Инициализация Telegram приложения...")
        application = Application.builder().token(TOKEN).build()
        
        # Добавляем обработчики
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        await application.initialize()
        logger.info("✅ Telegram приложение инициализировано")
    return application

# ----- ОБРАБОТЧИКИ КОМАНД -----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    await update.message.reply_text(
        "🚀 **Бот работает через Webhook!**\n\n"
        "Конфликтов больше не будет.",
        parse_mode="HTML"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    await update.message.reply_text(
        "🆘 **Помощь**\n\n"
        "Просто отправь любое сообщение, и я отвечу.",
        parse_mode="HTML"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик всех текстовых сообщений"""
    user_text = update.message.text
    user_name = update.effective_user.first_name
    
    logger.info(f"Получено сообщение от {user_name}: {user_text[:50]}...")
    
    await update.message.reply_text(
        f"✅ Привет, {user_name}!\n\n"
        f"Ты написал: {user_text}\n\n"
        f"Сообщение обработано через webhook."
    )

# ----- WEBHOOK ENDPOINT -----
@app.route('/webhook', methods=['POST'])
def webhook():
    """Принимает обновления от Telegram"""
    try:
        logger.info("📥 Получен webhook запрос")
        
        # Получаем данные от Telegram
        update_data = request.get_json(force=True)
        logger.debug(f"Данные: {update_data}")
        
        # Создаем объект Update из JSON
        update = Update.de_json(update_data, bot)
        
        # Запускаем обработку в новом event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def process():
            app = await init_application()
            await app.process_update(update)
        
        loop.run_until_complete(process())
        loop.close()
        
        logger.info("✅ Обновление обработано")
        return jsonify({"status": "ok"}), 200
        
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}", exc_info=True)
        # Всегда возвращаем 200, чтобы Telegram не слал повторно
        return jsonify({"status": "error"}), 200

# ----- ТЕСТОВЫЙ ЭНДПОИНТ -----
@app.route('/')
def index():
    """Проверка, что сервер работает"""
    return "🤖 Telegram Bot работает! Webhook endpoint: /webhook"

@app.route('/health')
def health():
    """Health check для Render"""
    return jsonify({"status": "healthy"}), 200

# ----- ЗАПУСК -----
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"🚀 Запуск сервера на порту {port}")
    app.run(host='0.0.0.0', port=port)
