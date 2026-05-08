import socket
import threading
import tkinter as tk
from tkinter import simpledialog, messagebox, ttk

HOST = "127.0.0.1"
PORT = 5050

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

go_signal_received = False

BG_COLOR = "#111827"
CARD_COLOR = "#1F2937"
TEXT_COLOR = "#F9FAFB"
MUTED_TEXT = "#D1D5DB"
ACCENT_COLOR = "#38BDF8"

root = tk.Tk()
root.title("LAN Reaction Game")
root.geometry("760x540")
root.configure(bg=BG_COLOR)

style = ttk.Style()
style.theme_use("clam")

style.configure(
    "ReactReady.TButton",
    font=("Arial", 20, "bold"),
    padding=(40, 20),
    background="#22C55E",
    foreground="white",
    borderwidth=0
)

style.map(
    "ReactReady.TButton",
    background=[("active", "#16A34A")],
    foreground=[("active", "white")]
)

style.configure(
    "ReactEarly.TButton",
    font=("Arial", 20, "bold"),
    padding=(40, 20),
    background="#F97316",
    foreground="white",
    borderwidth=0
)

style.map(
    "ReactEarly.TButton",
    background=[("active", "#EA580C")],
    foreground=[("active", "white")]
)

style.configure(
    "ReactDisabled.TButton",
    font=("Arial", 20, "bold"),
    padding=(40, 20),
    background="#374151",
    foreground="#9CA3AF",
    borderwidth=0
)

title_label = tk.Label(
    root,
    text="LAN Reaction Game",
    font=("Arial", 24, "bold"),
    bg=BG_COLOR,
    fg=TEXT_COLOR
)
title_label.pack(pady=(20, 5))

subtitle_label = tk.Label(
    root,
    text="Real-time TCP client-server reaction battle",
    font=("Arial", 11),
    bg=BG_COLOR,
    fg=MUTED_TEXT
)
subtitle_label.pack(pady=(0, 15))

main_status = tk.Label(
    root,
    text="Waiting for server...",
    font=("Arial", 14, "bold"),
    bg=CARD_COLOR,
    fg=ACCENT_COLOR,
    width=48,
    height=3,
    wraplength=650,
    justify="center"
)
main_status.pack(pady=10)

score_label = tk.Label(
    root,
    text="Score: 0 - 0",
    font=("Arial", 15, "bold"),
    bg=BG_COLOR,
    fg=TEXT_COLOR
)
score_label.pack(pady=8)

status_box = tk.Text(
    root,
    height=10,
    width=80,
    bg=CARD_COLOR,
    fg=TEXT_COLOR,
    insertbackground=TEXT_COLOR,
    font=("Consolas", 10),
    relief=tk.FLAT,
    padx=10,
    pady=10
)
status_box.pack(pady=10)

react_button = ttk.Button(
    root,
    text="WAITING...",
    style="ReactDisabled.TButton",
    state=tk.DISABLED
)
react_button.pack(pady=18)


def add_message(message):
    status_box.insert(tk.END, message + "\n")
    status_box.see(tk.END)


def set_button_waiting():
    react_button.config(text="WAITING...", state=tk.DISABLED, style="ReactDisabled.TButton")


def set_button_early():
    react_button.config(text="DON'T CLICK YET", state=tk.NORMAL, style="ReactEarly.TButton")


def set_button_ready():
    react_button.config(text="REACT!", state=tk.NORMAL, style="ReactReady.TButton")


def update_gui_message(message):
    global go_signal_received

    add_message(message)

    if message == "GO!":
        go_signal_received = True
        main_status.config(text="GO!", fg="#22C55E")
        set_button_ready()

    elif "Get ready" in message:
        go_signal_received = False
        main_status.config(text="Get ready...", fg="#FACC15")
        set_button_early()

    elif "Round" in message and "starting" in message:
        go_signal_received = False
        main_status.config(text=message, fg=ACCENT_COLOR)
        set_button_waiting()

    elif message.startswith("Score:"):
        score_label.config(text=message)

    elif "False start" in message:
        main_status.config(text=message, fg="#F97316")
        set_button_waiting()

    elif "won Round" in message:
        main_status.config(text=message, fg="#22C55E")
        set_button_waiting()

    elif "lost Round" in message:
        main_status.config(text=message, fg="#F87171")
        set_button_waiting()

    elif "Game over" in message:
        main_status.config(text=message, fg="#FACC15")
        set_button_waiting()


def send_reaction():
    global go_signal_received

    if go_signal_received:
        client.send("PRESSED".encode())
        main_status.config(text="Reaction sent!", fg=ACCENT_COLOR)
        add_message("You reacted!")
    else:
        client.send("EARLY".encode())
        main_status.config(text="False start sent!", fg="#F97316")
        add_message("You clicked too early!")

    set_button_waiting()


def listen_to_server():
    while True:
        try:
            message = client.recv(1024).decode()

            if not message:
                break

            update_gui_message(message)

        except:
            break

    client.close()


def connect_to_server():
    name = simpledialog.askstring("Player Name", "Enter your name:")

    if not name:
        messagebox.showerror("Error", "Name is required.")
        root.destroy()
        return

    try:
        client.connect((HOST, PORT))
        client.send(name.encode())
        add_message("Connected to server.")

        thread = threading.Thread(target=listen_to_server, daemon=True)
        thread.start()

    except ConnectionRefusedError:
        messagebox.showerror("Connection Error", "Could not connect to the server.")
        root.destroy()


react_button.config(command=send_reaction)

connect_to_server()

root.mainloop()