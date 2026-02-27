import os
import logging
import requests
from flask import Flask, request, jsonify
import asyncio
import telegram

# ============ НАСТРОЙКИ ============
TOKEN = "8444088116:AAENC53CGKlDc-DCwrHUbh_UA4NRT0m0rjc"
CAPTAIN_API_URL = "https://captain-agent.onrender.com/analyze"  # CaptainAgent
# ===================================

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
bot = telegram.Bot(token=TOKEN)

@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        update_data = request.get_json(force=True)
        logger.info("📥 Получен webhook запрос")
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(handle_update(update_data))
        loop.close()
        
        return 'OK', 200
    except Exception as e:
        logger.error(f"❌ Ошибка: {e}", exc_info=True)
        return 'OK', 200

async def handle_update(update_data):
    try:
        update = telegram.Update.de_json(update_data, bot)
        if not update.message:
            return
        
        chat_id = update.message.chat.id
        user_text = update.message.text
        
        logger.info(f"📝 Запрос: {user_text[:50]}...")
        
        # Отправляем в CaptainAgent
        try:
            response = requests.post(
                CAPTAIN_API_URL,
                json={"task": user_text},
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                result = data.get('result', 'Нет результата')
                await bot.send_message(chat_id=chat_id, text=f"📊 {result}")
            else:
                await bot.send_message(chat_id=chat_id, text=f"❌ Ошибка CaptainAgent: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            logger.error("CaptainAgent недоступен")
            await bot.send_message(chat_id=chat_id, text="⚠️ CaptainAgent временно недоступен, но бот работает!")
            await bot.send_message(chat_id=chat_id, text=f"✅ Эхо: {user_text}")
        except Exception as e:
            logger.error(f"Ошибка при запросе к CaptainAgent: {e}")
            await bot.send_message(chat_id=chat_id, text=f"❌ Ошибка: {str(e)}")
            
    except Exception as e:
        logger.error(f"Ошибка обработки: {e}", exc_info=True)

@app.route('/')
def index():
    return "🚀 Бот работает и связан с CaptainAgent!"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
