import tkinter as tk
from tkinter import filedialog, messagebox
import base64

# Функция для расшифровки base64 с числовым ключом
def decrypt_text_base64(encrypted_text, key):
    key = int(key) % 256
    try:
        encrypted_bytes = base64.b64decode(encrypted_text)
    except Exception:
        return "[Ошибка декодирования]"
    decrypted_chars = [chr((b - key) % 256) for b in encrypted_bytes]
    return ''.join(decrypted_chars)

# GUI
root = tk.Tk()
root.title("Расшифровщик MetaMask фраз")
root.geometry("500x400")
root.configure(bg="#2a2a2a")

selected_file = None

file_label = tk.Label(root, text="Файл не выбран", bg="#2a2a2a", fg="#fff")
file_label.pack(pady=10)

key_label = tk.Label(root, text="Введите числовой ключ:", bg="#2a2a2a", fg="#fff")
key_label.pack()
key_entry = tk.Entry(root, width=60)
key_entry.pack(pady=5)

output_text = tk.Text(root, height=10, width=60, bg="#1e1e1e", fg="#fff")
output_text.pack(pady=10)

def choose_file():
    global selected_file
    selected_file = filedialog.askopenfilename(
        title="Выберите файл с зашифрованными фразами",
        filetypes=(("Text files", "*.txt"), ("All files", "*.*"))
    )
    if selected_file:
        file_label.config(text=selected_file)

def decrypt_file():
    global selected_file
    if not selected_file:
        messagebox.showerror("Ошибка", "Выберите файл для расшифровки")
        return
    key_input = key_entry.get()
    if not key_input.isdigit():
        messagebox.showerror("Ошибка", "Ключ должен быть числом")
        return

    try:
        decrypted_lines = []
        with open(selected_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    decrypted_lines.append(decrypt_text_base64(line, int(key_input)))
        output_text.delete("1.0", tk.END)
        output_text.insert(tk.END, "\n".join(decrypted_lines))
        messagebox.showinfo("Успех", "Фразы успешно расшифрованы!")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось расшифровать: {e}")

choose_btn = tk.Button(root, text="Выбрать файл", command=choose_file, bg="#444", fg="#fff")
choose_btn.pack(pady=5)
decrypt_btn = tk.Button(root, text="Расшифровать", command=decrypt_file, bg="#6c63ff", fg="#fff")
decrypt_btn.pack(pady=5)

root.mainloop()

