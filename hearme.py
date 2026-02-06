import os
import queue
import sys
import json
import threading
import customtkinter as ctk
import sounddevice as sd
from vosk import Model, KaldiRecognizer
import argostranslate.translate
import argostranslate.package
from gpiozero import Button

# --- КОНФИГУРАЦИЯ ---
SAMPLE_RATE = 48000  # Оптимально для I2S на Raspberry Pi 5
CLEANUP_DELAY = 15000  # 15 секунд тишины до очистки экрана
MODEL_PATHS = {
    "ru": os.path.expanduser("~/HearMe/model_ru"),
    "en": os.path.expanduser("~/HearMe/model_en")
}
PIN_BTN_IN_LANG = 23
PIN_BTN_OUT_LANG = 24

class DeafAssistApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Настройка окна
        self.attributes('-fullscreen', True)
        self.bind("<Escape>", lambda e: self.close_app())
        self.title("HearMe - Live Translator")
        ctk.set_appearance_mode("Dark")
        
        self.input_lang = "ru"
        self.output_lang = "en"
        self.is_running = False
        self.audio_queue = queue.Queue()
        self.cleanup_timer = None
        
        print("Инициализация системы...")
        try:
            self.models = {
                "ru": Model(MODEL_PATHS["ru"]),
                "en": Model(MODEL_PATHS["en"])
            }
            print("Модели Vosk загружены.")
        except Exception as e:
            print(f"Критическая ошибка загрузки моделей: {e}")
            sys.exit(1)
        
        self.setup_ui()
        self.setup_hardware()

    def setup_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.top_bar = ctk.CTkFrame(self, corner_radius=0, height=80)
        self.top_bar.grid(row=0, column=0, sticky="ew")
        
        self.btn_toggle = ctk.CTkButton(self.top_bar, text="СТАРТ", fg_color="#2ecc71", 
                                        width=150, height=50, font=("Arial", 20, "bold"),
                                        command=self.toggle_service)
        self.btn_toggle.pack(side="left", padx=20, pady=15)

        self.btn_in = ctk.CTkButton(self.top_bar, text=f"Вход: {self.input_lang.upper()}", 
                                    width=140, height=50, command=self.toggle_input_lang)
        self.btn_in.pack(side="left", padx=10)

        self.btn_out = ctk.CTkButton(self.top_bar, text=f"Выход: {self.output_lang.upper()}", 
                                     width=140, height=50, command=self.toggle_output_lang)
        self.btn_out.pack(side="left", padx=10)

        self.btn_exit = ctk.CTkButton(self.top_bar, text="ВЫХОД", fg_color="#e74c3c", 
                                      width=120, height=50, command=self.close_app)
        self.btn_exit.pack(side="right", padx=20)

        self.text_display = ctk.CTkTextbox(self, font=("Arial", 38), wrap="word")
        self.text_display.grid(row=1, column=0, sticky="nsew", padx=20, pady=20)
        self.log_system("Система готова")

    def setup_hardware(self):
        try:
            self.phys_in = Button(PIN_BTN_IN_LANG, bounce_time=0.2)
            self.phys_out = Button(PIN_BTN_OUT_LANG, bounce_time=0.2)
            self.phys_in.when_pressed = self.toggle_input_lang
            self.phys_out.when_pressed = self.toggle_output_lang
        except Exception as e:
            print(f"GPIO не доступен: {e}")

    def reset_display(self):
        self.text_display.configure(state="normal")
        self.text_display.delete("1.0", "end")
        self.text_display.insert("end", "--- ЖДУ РЕЧЬ ---")
        self.text_display.configure(state="disabled")
        self.cleanup_timer = None

    def restart_cleanup_timer(self):
        if self.cleanup_timer:
            self.after_cancel(self.cleanup_timer)
        self.cleanup_timer = self.after(CLEANUP_DELAY, self.reset_display)

    def toggle_input_lang(self):
        was_running = self.is_running
        if was_running: self.stop_recognition()
        self.input_lang = "en" if self.input_lang == "ru" else "ru"
        self.btn_in.configure(text=f"Вход: {self.input_lang.upper()}")
        if was_running: self.start_recognition()

    def toggle_output_lang(self):
        self.output_lang = "en" if self.output_lang == "ru" else "ru"
        self.btn_out.configure(text=f"Выход: {self.output_lang.upper()}")

    def toggle_service(self):
        if not self.is_running: self.start_recognition()
        else: self.stop_recognition()

    def start_recognition(self):
        self.is_running = True
        self.btn_toggle.configure(text="СТОП", fg_color="#e67e22")
        self.text_display.configure(state="normal")
        self.text_display.delete("1.0", "end")
        self.text_display.configure(state="disabled")
        threading.Thread(target=self.recognition_loop, daemon=True).start()

    def stop_recognition(self):
        self.is_running = False
        self.btn_toggle.configure(text="СТАРТ", fg_color="#2ecc71")
        if self.cleanup_timer:
            self.after_cancel(self.cleanup_timer)

    def recognition_loop(self):
        try:
            model = self.models[self.input_lang]
            rec = KaldiRecognizer(model, SAMPLE_RATE)
            
            devices = sd.query_devices()
            dev_id = None
            for i, dev in enumerate(devices):
                if 'googlevoicehat' in dev['name'].lower() or 'i2s' in dev['name'].lower():
                    dev_id = i
                    break
            
            if dev_id is None: dev_id = sd.default.device[0]

            def callback(indata, frames, time, status):
                self.audio_queue.put(bytes(indata))

            with sd.RawInputStream(samplerate=SAMPLE_RATE, blocksize=4000, device=dev_id,
                                   dtype='int16', channels=1, callback=callback):
                while self.is_running:
                    data = self.audio_queue.get()
                    if rec.AcceptWaveform(data):
                        res = json.loads(rec.Result())
                        text = res.get("text", "")
                        if text:
                            self.after(0, lambda t=text: self.process_final_text(t))
                    else:
                        partial = json.loads(rec.PartialResult()).get("partial", "")
                        if partial:
                            self.after(0, lambda p=partial: self.update_live_ui(p))

        except Exception as e:
            self.after(0, lambda m=str(e): self.log_system(f"Ошибка аудио: {m}"))
            self.is_running = False

    def update_live_ui(self, text):
        self.restart_cleanup_timer()
        self.text_display.configure(state="normal")
        content = self.text_display.get("1.0", "end-1c").split('\n')
        if content and content[-1].startswith("..."):
            self.text_display.delete("end-2l", "end-1c")
        self.text_display.insert("end", f"\n... {text}")
        self.text_display.see("end")
        self.text_display.configure(state="disabled")

    def process_final_text(self, text):
        self.restart_cleanup_timer()
        translated = text
        if self.input_lang != self.output_lang:
            try:
                translated = argostranslate.translate.translate(text, self.input_lang, self.output_lang)
            except: pass
        
        self.text_display.configure(state="normal")
        content = self.text_display.get("1.0", "end-1c").split('\n')
        if content and content[-1].startswith("..."):
            self.text_display.delete("end-2l", "end-1c")
            
        self.text_display.insert("end", f"\n{translated.capitalize()}\n")
        self.text_display.see("end")
        self.text_display.configure(state="disabled")

    def log_system(self, message):
        self.text_display.configure(state="normal")
        self.text_display.insert("end", f"\n[{message}]\n")
        self.text_display.configure(state="disabled")

    def close_app(self):
        self.is_running = False
        self.destroy()
        sys.exit(0)

if __name__ == "__main__":
    app = DeafAssistApp()
    app.mainloop()