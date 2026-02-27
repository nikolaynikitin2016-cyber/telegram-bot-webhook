import os
import logging
import requests
from flask import Flask, request, jsonify
import telegram
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import asyncio

# ============ НАСТРОЙКИ ============
TOKEN = "8512903035:AAGaNTmKbfbzdYlXajySUoGv2smiBnTyAhg"
CAPTAIN_API_URL = "https://captain-agent.onrender.com/analyze"  # URL CaptainAgent (когда запустишь)
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
        application.add_handler(CommandHandler("status", status_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        await application.initialize()
        logger.info("✅ Telegram приложение инициализировано")
    return application

# ----- ОБРАБОТЧИКИ КОМАНД -----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    await update.message.reply_text(
        "🚀 **CaptainAgent Bot готов!**\n\n"
        "Я связываю тебя с командой ИИ-аналитиков.\n\n"
        "📌 **Команды:**\n"
        "/help - помощь\n"
        "/status - статус CaptainAgent\n\n"
        "🔍 **Пример запроса:**\n"
        "• Проанализируй Bitcoin на сегодня",
        parse_mode="HTML"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    await update.message.reply_text(
        "🆘 **Помощь**\n\n"
        "Просто отправь запрос, и я передам его CaptainAgent.\n\n"
        "Примеры:\n"
        "• Проанализируй Ethereum\n"
        "• Дай прогноз по Bitcoin\n"
        "• Что с рынком акций?\n\n"
        "⏱ Время ответа: до 5 минут",
        parse_mode="HTML"
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Проверка статуса CaptainAgent"""
    waiting = await update.message.reply_text("🔍 Проверяю статус CaptainAgent...")
    
    try:
        # Пробуем достучаться до CaptainAgent
        response = requests.get(
            CAPTAIN_API_URL.replace('/analyze', '/health'),
            timeout=5
        )
        
        if response.status_code == 200:
            await waiting.edit_text("✅ **CaptainAgent работает!**\n\nМожно отправлять запросы.")
        else:
            await waiting.edit_text("⚠️ **CaptainAgent отвечает, но с ошибкой**\n\nПроверь логи на Render.")
    except:
        await waiting.edit_text(
            "❌ **CaptainAgent не запущен**\n\n"
            "Сначала запусти CaptainAgent на Render, потом укажи его URL в настройках."
        )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик всех текстовых сообщений"""
    user_text = update.message.text
    user_name = update.effective_user.first_name
    
    logger.info(f"📥 Запрос от {user_name}: {user_text[:50]}...")
    
    # Отправляем сообщение "печатает..."
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    
    waiting = await update.message.reply_text("⏳ Анализирую через CaptainAgent... (до 5 минут)")
    
    try:
        # Отправляем запрос в CaptainAgent
        response = requests.post(
            CAPTAIN_API_URL,
            json={"task": user_text},
            timeout=300  # 5 минут
        )
        
        if response.status_code == 200:
            data = response.json()
            result = data.get('result') or data.get('response') or str(data)
            
            # Ограничиваем длину
            if len(result) > 4000:
                result = result[:4000] + "...\n\n*(сообщение обрезано)*"
            
            await waiting.edit_text(f"✅ **Результат анализа:**\n\n{result}")
        else:
            await waiting.edit_text(f"❌ Ошибка CaptainAgent: код {response.status_code}")
            
    except requests.exceptions.Timeout:
        await waiting.edit_text("❌ Превышено время ожидания (5 минут)")
    except requests.exceptions.ConnectionError:
        await waiting.edit_text(
            "❌ CaptainAgent недоступен\n\n"
            "Проверь, запущен ли он на Render. Если нет — просто игнорируй, я отвечу сам."
        )
        # Запасной ответ
        await update.message.reply_text(f"✅ Получен запрос: {user_text}")
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        await waiting.edit_text(f"❌ Ошибка: {str(e)}")

# ----- WEBHOOK ENDPOINT -----
@app.route('/webhook', methods=['POST'])
def webhook():
    """Принимает обновления от Telegram"""
    try:
        logger.info("📥 Получен webhook запрос")
        update_data = request.get_json(force=True)
        
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
        return jsonify({"status": "error"}), 200

# ----- ТЕСТОВЫЙ ЭНДПОИНТ -----
@app.route('/')
def index():
    return "🤖 Telegram Bot работает! Webhook endpoint: /webhook"

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

# ----- ЗАПУСК -----
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"🚀 Запуск сервера на порту {port}")
    app.run(host='0.0.0.0', port=port)
