import threading
import socket
from tkinter import END
import customtkinter as ctk

SERVER_HOST = "localhost"
SERVER_PORT = 8080

ctk.set_appearance_mode("dark")  # стартова тема
ctk.set_default_color_theme("blue")  # стартова палітра

class ChatClient(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Simple Chat")
        self.geometry("600x450")

        self.sock = None
        self.running = False
        self.recv_thread = None
        self.nickname = "Anon"

        # --- Екран вибору ніку ---
        self.nickname_frame = ctk.CTkFrame(self)
        self.nickname_frame.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(self.nickname_frame, text="Введіть ваш нік:").pack(pady=10)
        self.nickname_entry = ctk.CTkEntry(self.nickname_frame, width=200, height=40, placeholder_text="Ваш нік...")
        self.nickname_entry.pack(pady=10)
        self.connect_btn = ctk.CTkButton(self.nickname_frame, text="Підключитися", width=150, height=40,
                                         command=self.start_chat)
        self.connect_btn.pack(pady=10)

        # --- Основний інтерфейс чату ---
        self.chat_frame = ctk.CTkFrame(self)

        self.chat_box = ctk.CTkTextbox(self.chat_frame, width=560, height=300)
        self.chat_box.configure(state="disabled")
        self.chat_box.place(x=20, y=20)

        self.entry = ctk.CTkEntry(self.chat_frame, placeholder_text="Напишіть повідомлення...", width=420, height=40)
        self.entry.place(x=20, y=330)

        self.send_btn = ctk.CTkButton(self.chat_frame, text="Відправити", width=120, height=40,
                                      command=self.send_message)
        self.send_btn.place(x=455, y=330)

        # --- Кнопки для зміни теми та кольору ---
        self.theme_light_btn = ctk.CTkButton(self.chat_frame, text="Світла тема", width=100, height=30,
                                             command=lambda: ctk.set_appearance_mode("light"))
        self.theme_light_btn.place(x=20, y=380)

        self.theme_dark_btn = ctk.CTkButton(self.chat_frame, text="Темна тема", width=100, height=30,
                                            command=lambda: ctk.set_appearance_mode("dark"))
        self.theme_dark_btn.place(x=130, y=380)

           # --- Початок чату після введення ніку ---
    def start_chat(self):
        nick = self.nickname_entry.get().strip()
        self.nickname = nick if nick else "Anon"

        self.nickname_frame.place_forget()
        self.chat_frame.place(x=0, y=0, relwidth=1, relheight=1)

        self.append_local("[SYSTEM] Спроба підключення...")
        threading.Thread(target=self.connect_to_server, daemon=True).start()

    # --- Додавання повідомлення у текстове поле ---
    def append_local(self, text):
        self.chat_box.configure(state="normal")
        self.chat_box.insert(END, text + "\n")
        self.chat_box.see("end")
        self.chat_box.configure(state="disabled")

    # --- Підключення до сервера ---
    def connect_to_server(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((SERVER_HOST, SERVER_PORT))
            self.sock = s
            self.running = True
            self.append_local(f"[SYSTEM] Підключено до {SERVER_HOST}:{SERVER_PORT}")
            hello = f"TEXT@{self.nickname}@{self.nickname} приєднався(лась) до чату\n"
            s.sendall(hello.encode("utf-8"))
            self.recv_thread = threading.Thread(target=self.recv_loop, daemon=True)
            self.recv_thread.start()
        except Exception as e:
            self.append_local(f"[ERROR] Не вдалося підключитися: {e}")

    # --- Відправка повідомлення ---
    def send_message(self):
        text = self.entry.get().strip()
        if not text or not self.sock:
            return
        self.append_local(f"{self.nickname}: {text}")
        packet = f"TEXT@{self.nickname}@{text}\n"
        try:
            self.sock.sendall(packet.encode("utf-8"))
        except Exception as e:
            self.append_local(f"[ERROR] Помилка відправки: {e}")
        self.entry.delete(0, END)

    # --- Отримання повідомлень від сервера ---
    def recv_loop(self):
        buffer = ""
        try:
            while self.running:
                chunk = self.sock.recv(4096)
                if not chunk:
                    break
                buffer += chunk.decode("utf-8", errors="ignore")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    self.handle_line(line.strip())
        except Exception as e:
            self.append_local(f"[ERROR] Помилка отримання: {e}")
        finally:
            try:
                self.sock.close()
            except:
                pass
            self.append_local("[SYSTEM] Відключено від сервера")

    # --- Обробка рядка від сервера ---
    def handle_line(self, line):
        if not line:
            return
        parts = line.split("@", 2)
        if parts[0] == "TEXT" and len(parts) >= 3:
            author = parts[1]
            msg = parts[2]
            self.after(0, lambda: self.append_local(f"{author}: {msg}"))
        else:
            self.after(0, lambda: self.append_local(line))

    # --- Закриття вікна ---
    def on_closing(self):
        self.running = False
        try:
            if self.sock:
                self.sock.close()
        except:
            pass
        self.destroy()

if __name__ == "__main__":
    app = ChatClient()
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()