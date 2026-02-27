import os
import logging
from flask import Flask, request
import telegram

TOKEN = "8444088116:AAENC53CGKlDc-DCwrHUbh_UA4NRT0m0rjc"
bot = telegram.Bot(token=TOKEN)
app = Flask(__name__)

logging.basicConfig(level=logging.INFO)

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        update = telegram.Update.de_json(request.get_json(force=True), bot)
        chat_id = update.message.chat.id
        text = update.message.text
        
        logging.info(f"Получено: {text} от {chat_id}")
        
        if text == '/start':
            bot.send_message(chat_id=chat_id, text="✅ Бот работает!")
        else:
            bot.send_message(chat_id=chat_id, text=f"Ты написал: {text}")
            
        return 'OK', 200
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        return 'OK', 200

@app.route('/')
def index():
    return "Бот запущен"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
