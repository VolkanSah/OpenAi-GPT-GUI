# Copyright Volkan Kücükbudak
# source https://github.com/VolkanSah/localGPT
# Under GPLv3
import tkinter as tk
from tkinter import scrolledtext, ttk, filedialog
import json
import requests
import base64
import time

# Load settings
with open("settings.json") as f:
    settings = json.load(f)
cwd = settings.get("working_directory", ".")
api_key = settings.get("openai_api_key")

def create_assistant():
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        data = {
            "name": "Mein GPT Assistent",
            "instructions": "Du bist ein hilfreicher Assistent.",
            "model": model_var.get()
        }
        response = requests.post("https://api.openai.com/v1/assistants", headers=headers, json=data)
        assistant = response.json()
        assistant_id_entry.delete(0, tk.END)
        assistant_id_entry.insert(0, assistant['id'])
        return assistant
    except Exception as e:
        log_output.insert(tk.END, f"Fehler beim Erstellen des Assistenten: {str(e)}\n")
        return None

def create_thread():
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        response = requests.post("https://api.openai.com/v1/threads", headers=headers)
        thread = response.json()
        return thread
    except Exception as e:
        log_output.insert(tk.END, f"Fehler beim Erstellen des Threads: {str(e)}\n")
        return None

def process_gpt_response(response):
    chat_output.insert(tk.END, f"GPT: {response}\n")
    log_output.insert(tk.END, f"Response: {response}\n")

def communicate_with_gpt(message):
    chat_output.insert(tk.END, f"Du: {message}\n")
    log_output.insert(tk.END, f"Sende Nachricht: {message}\n")

    try:
        assistant_id = assistant_id_entry.get()
        if not assistant_id:
            assistant = create_assistant()
            if not assistant:
                return
            assistant_id = assistant['id']

        thread = create_thread()
        if not thread:
            return

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        message_data = {
            "role": "user",
            "content": message
        }
        requests.post(f"https://api.openai.com/v1/threads/{thread['id']}/messages", headers=headers, json=message_data)

        run_data = {
            "assistant_id": assistant_id
        }
        run_response = requests.post(f"https://api.openai.com/v1/threads/{thread['id']}/runs", headers=headers, json=run_data)
        run = run_response.json()

        while True:
            run_status_response = requests.get(f"https://api.openai.com/v1/threads/{thread['id']}/runs/{run['id']}", headers=headers)
            run_status = run_status_response.json()
            if run_status['status'] == 'completed':
                break
            time.sleep(1)

        messages_response = requests.get(f"https://api.openai.com/v1/threads/{thread['id']}/messages", headers=headers)
        messages = messages_response.json()['data']
        
        for msg in messages:
            if msg['role'] == "assistant":
                process_gpt_response(msg['content'][0]['text']['value'])

    except Exception as e:
        chat_output.insert(tk.END, str(e) + '\n')
        log_output.insert(tk.END, str(e) + '\n')

def send_text_message():
    message = chat_input.get("1.0", tk.END).strip()
    if not message:
        chat_output.insert(tk.END, "No message provided\n")
        log_output.insert(tk.END, "No message provided\n")
        return
    chat_input.delete("1.0", tk.END)
    communicate_with_gpt(message)

def clear_chat():
    chat_output.delete("1.0", tk.END)

def clear_logs():
    log_output.delete("1.0", tk.END)

# Create the main window
app = tk.Tk()
app.title("localGPT Version 1.0")
app.geometry("860x640")

# Create frames
settings_frame = tk.Frame(app, bd=2, relief=tk.SUNKEN)
settings_frame.grid(row=0, column=0, sticky="ns")

main_frame = tk.Frame(app, bd=2, relief=tk.SUNKEN)
main_frame.grid(row=0, column=1, sticky="nsew")

app.grid_rowconfigure(0, weight=1)
app.grid_columnconfigure(1, weight=1)

# Create a notebook for tabs
notebook = ttk.Notebook(main_frame)
notebook.grid(row=0, column=0, columnspan=3, sticky="nsew")

# Create chat tab
chat_tab = tk.Frame(notebook)
notebook.add(chat_tab, text="Chat")

# Create log tab
log_tab = tk.Frame(notebook)
notebook.add(log_tab, text="Logs")

main_frame.grid_rowconfigure(0, weight=1)
main_frame.grid_columnconfigure(0, weight=1)

# Settings frame
tk.Label(settings_frame, text="Settings").pack(pady=10)

# GPT model selection
model_label = tk.Label(settings_frame, text="Select GPT Model:")
model_label.pack()
model_var = tk.StringVar(value="gpt-4")
model_menu = ttk.Combobox(settings_frame, textvariable=model_var)
model_menu['values'] = ("gpt-4", "gpt-3.5-turbo", "text-davinci-003", "text-curie-001", "text-babbage-001", "text-ada-001")
model_menu.pack()

# Temperature scale
temp_label = tk.Label(settings_frame, text="Set Temperature:")
temp_label.pack()
temp_scale = tk.Scale(settings_frame, from_=0.0, to=1.0, resolution=0.01, orient=tk.HORIZONTAL)
temp_scale.set(0.7)
temp_scale.pack()

# Token entry
token_label = tk.Label(settings_frame, text="Set Max Tokens:")
token_label.pack()
token_entry = tk.Entry(settings_frame, width=10)
token_entry.insert(0, "150")
token_entry.pack()

# Füge einen Button hinzu, um einen neuen Assistenten zu erstellen
create_assistant_button = tk.Button(settings_frame, text="Neuen Assistenten erstellen", command=create_assistant)
create_assistant_button.pack()

# Füge ein Feld hinzu, um die Assistent-ID anzuzeigen
assistant_id_label = tk.Label(settings_frame, text="Assistent ID:")
assistant_id_label.pack()
assistant_id_entry = tk.Entry(settings_frame, width=36)
assistant_id_entry.pack()

# Chat tab content
chat_output_label = tk.Label(chat_tab, text="Chat Output:")
chat_output_label.grid(row=0, column=0, pady=5)
chat_output = scrolledtext.ScrolledText(chat_tab, width=80, height=20)
chat_output.grid(row=1, column=0, columnspan=2, pady=5, sticky="nsew")

chat_label = tk.Label(chat_tab, text="Chat with GPT:")
chat_label.grid(row=2, column=0, pady=5)
chat_input = scrolledtext.ScrolledText(chat_tab, width=70, height=5)
chat_input.grid(row=3, column=0, columnspan=2, pady=5, sticky="ew")

# Button frame for organized layout
button_frame = tk.Frame(chat_tab)
button_frame.grid(row=4, column=0, columnspan=2, pady=5)

send_button = tk.Button(button_frame, text="Send Message", command=send_text_message)
send_button.pack(side=tk.LEFT, padx=5)
clear_chat_button = tk.Button(button_frame, text="Clear Chat", command=clear_chat)
clear_chat_button.pack(side=tk.LEFT, padx=5)

chat_tab.grid_rowconfigure(1, weight=1)
chat_tab.grid_columnconfigure(0, weight=1)

# Log tab content
log_output_label = tk.Label(log_tab, text="Logs:")
log_output_label.grid(row=0, column=0, pady=5)
log_output = scrolledtext.ScrolledText(log_tab, width=80, height=20)
log_output.grid(row=1, column=0, pady=5, sticky="nsew")

clear_logs_button = tk.Button(log_tab, text="Clear Logs", command=clear_logs)
clear_logs_button.grid(row=2, column=0, pady=5)

log_tab.grid_rowconfigure(1, weight=1)
log_tab.grid_columnconfigure(0, weight=1)

# Run the application
app.mainloop()
