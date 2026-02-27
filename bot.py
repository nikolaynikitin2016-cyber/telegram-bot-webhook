import os
import logging
import requests
from flask import Flask, request, jsonify
import telegram
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import asyncio

# ============ НАСТРОЙКИ ============
TOKEN = "8444088116:AAENC53CGKlDc-DCwrHUbh_UA4NRT0m0rjc"
CAPTAIN_API_URL = "https://captain-agent.onrender.com/analyze"
# ===================================

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
bot = telegram.Bot(token=TOKEN)
application = None

async def init_application():
    global application
    if application is None:
        logger.info("🔄 Инициализация...")
        application = Application.builder().token(TOKEN).build()
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        await application.initialize()
        logger.info("✅ Инициализировано")
    return application

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚀 Бот работает! Токен новый, webhook ок.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🆘 Напиши что-нибудь — я отвечу.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"✅ Получено: {update.message.text}")

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        logger.info("📥 Webhook запрос")
        update_data = request.get_json(force=True)
        update = Update.de_json(update_data, bot)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def process():
            app = await init_application()
            await app.process_update(update)
        
        loop.run_until_complete(process())
        loop.close()
        
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        return jsonify({"status": "error"}), 200

@app.route('/')
def index():
    return "🤖 Бот работает! /webhook — для Telegram"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
