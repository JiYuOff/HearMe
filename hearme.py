import tkinter as tk
from tkinter import font
import threading
import queue
import time
import speech_recognition as sr
from faster_whisper import WhisperModel
import argostranslate.package
import argostranslate.translate
from gpiozero import Button


MODEL_SIZE = "small"  
COMPUTE_TYPE = "int8" 
PIN_SRC_LANG = 17
PIN_TGT_LANG = 27
PIN_PAUSE = 22

class VoiceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("RPi 5 Offline Translator")
        self.root.attributes('-fullscreen', True) 
        self.root.configure(bg='black')

        # Язык
        self.is_paused = False
        self.src_lang = "ru" 
        self.tgt_lang = "en" 
        self.queue = queue.Queue()
        
        
        self.setup_ui()
        
        
        self.btn_src = Button(PIN_SRC_LANG, bounce_time=0.3)
        self.btn_tgt = Button(PIN_TGT_LANG, bounce_time=0.3)
        self.btn_pause = Button(PIN_PAUSE, bounce_time=0.3)
        
        self.btn_src.when_pressed = self.toggle_src_lang
        self.btn_tgt.when_pressed = self.toggle_tgt_lang
        self.btn_pause.when_pressed = self.toggle_pause

      
        self.status_label.config(text="Загрузка моделей... (Нужен интернет при 1-м запуске)")
        self.root.update()
        
        threading.Thread(target=self.init_models_and_listen, daemon=True).start()
        
       
        self.process_queue()

    def setup_ui(self):
        
        main_font = font.Font(family='Helvetica', size=24, weight='bold')
        status_font = font.Font(family='Helvetica', size=14)
        
      
        self.top_frame = tk.Frame(self.root, bg='#222')
        self.top_frame.pack(fill=tk.X, side=tk.TOP, pady=5)
        
        self.lang_label = tk.Label(self.top_frame, text=f"IN: {self.src_lang.upper()} -> OUT: {self.tgt_lang.upper()}", 
                                   fg='white', bg='#222', font=status_font)
        self.lang_label.pack(side=tk.LEFT, padx=20)
        
        self.status_label = tk.Label(self.top_frame, text="Инициализация...", fg='#00ff00', bg='#222', font=status_font)
        self.status_label.pack(side=tk.RIGHT, padx=20)

        self.text_area = tk.Text(self.root, bg='black', fg='white', font=main_font, wrap=tk.WORD, borderwidth=0)
        self.text_area.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)
        
        self.text_area.tag_config('src', foreground='#aaaaaa') 
        self.text_area.tag_config('tgt', foreground='#ffffff') 

    def process_queue(self):
        """Проверяет очередь сообщений и обновляет UI"""
        try:
            while True:
                msg_type, content = self.queue.get_nowait()
                if msg_type == "text":
                    original, translated = content
                    self.text_area.insert(tk.END, f"> {original}\n", 'src')
                    self.text_area.insert(tk.END, f"= {translated}\n\n", 'tgt')
                    self.text_area.see(tk.END)
                elif msg_type == "status":
                    color = "#00ff00" if "Слушаю" in content else "#ffaa00"
                    if "Пауза" in content: color = "#ff0000"
                    self.status_label.config(text=content, fg=color)
                elif msg_type == "lang":
                    self.lang_label.config(text=content)
        except queue.Empty:
            pass
        self.root.after(100, self.process_queue)

    def init_models_and_listen(self):
        print("Загрузка Whisper...")
        self.whisper = WhisperModel(MODEL_SIZE, device="cpu", compute_type=COMPUTE_TYPE)
        
        print("Проверка пакетов перевода...")
        self.setup_argos()
        
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 1000  
        self.recognizer.dynamic_energy_threshold = True
        
        self.queue.put(("status", "Готов! Слушаю..."))
        
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source)
            while True:
                if self.is_paused:
                    time.sleep(0.5)
                    continue
                
                try:
                    audio = self.recognizer.listen(source, timeout=None, phrase_time_limit=10)
                    
                    audio_data = audio.get_wav_data()
                    
                    import io
                    virtual_file = io.BytesIO(audio_data)
                    
                    
                    segments, info = self.whisper.transcribe(virtual_file, language=self.src_lang, beam_size=5)
                    
                    full_text = ""
                    for segment in segments:
                        full_text += segment.text
                    
                    if not full_text.strip():
                        continue
                        
                    translated_text = full_text
                    if self.src_lang != self.tgt_lang:
                        translated_text = argostranslate.translate.translate(full_text, self.src_lang, self.tgt_lang)
                    
                    self.queue.put(("text", (full_text, translated_text)))
                    
                except Exception as e:
                    print(f"Error: {e}")

    def setup_argos(self):
        """Устанавливает языковые пакеты ArgosTranslate, если их нет"""
        argostranslate.package.update_package_index()
        available_packages = argostranslate.package.get_available_packages()
        
        pairs_needed = [('ru', 'en'), ('en', 'ru')]
        
        for from_code, to_code in pairs_needed:
            installed = argostranslate.package.get_installed_packages()
            is_installed = any(p.from_code == from_code and p.to_code == to_code for p in installed)
            
            if not is_installed:
                self.queue.put(("status", f"Скачивание перевода {from_code}->{to_code}..."))
                package_to_install = next(
                    filter(
                        lambda x: x.from_code == from_code and x.to_code == to_code,
                        available_packages
                    )
                )
                argostranslate.package.install_from_path(package_to_install.download())

    def toggle_src_lang(self):
        self.src_lang = "en" if self.src_lang == "ru" else "ru"
        self.update_lang_display()

    def toggle_tgt_lang(self):
        self.tgt_lang = "en" if self.tgt_lang == "ru" else "ru"
        self.update_lang_display()

    def update_lang_display(self):
        self.queue.put(("lang", f"IN: {self.src_lang.upper()} -> OUT: {self.tgt_lang.upper()}"))

    def toggle_pause(self):
        self.is_paused = not self.is_paused
        status = "Пауза" if self.is_paused else "Слушаю..."
        self.queue.put(("status", status))

if __name__ == "__main__":
    root = tk.Tk()
    app = VoiceApp(root)
    root.mainloop()
