# HearMe
Находится в разработке!
Устройство для глухих и слабослышащих, распознающее человеческую речь и переводящее её, для помощи в общении. 

# Компоненты
Для данного устройства я использовал и рекомендую такие компоненты(* - количество):
```
Raspberry pi 5
Охлаждение для Raspberry pi 5
Экран для Raspberry pi 5
Тактовая кнопка *3
Geekworm x1201
Аккумулятор 18650 *2
Провода мама-мама *?
Корпус, напечатанный на 3d принтере(В разработке)
Микрофон INMP441 
```
Можете найти все ссылки на них в файле source.txt на aliexpress.
Также список всех библиотек и моделей для устройства:
```
os
queue
sys
json
threading
customtkinter
sounddevice
vosk
argostranslate
gpiozero
```
# Установка ПО
Всё устройство работает на ОС "Raspberry Pi OS(64-bit)". Также необходимо установить на флешку соедующие файлы:
Модели распознавания (Vosk):
`vosk-model-small-ru-0.22.zip(https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip)`
`vosk-model-small-en-us-0.15.zip(https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip)`
Модели перевода (Argos Translate):
`translate-ru_en-1_9.argosmodel(https://data.argosopentech.com/translate-ru_en-1_9.argosmodel)`
`translate-en_ru-1_9.argosmodel(https://data.argosopentech.com/translate-en_ru-1_9.argosmodel)`

Вставьте флшеку в Raspberry Pi 5. Настройте файл конфига. Введите команду в терминал:
```
sudo nano /boot/firmware/config.txt
```
Добавьте в текст данные строки:
```
dtoverlay=googlevoicehat-soundcard
dtparam=i2s=on
dtparam=fan_temp0=30000,fan_temp0_hyst=7000
```
Сохраните (Ctrl+O, Enter), выйдите (Ctrl+X) и перезагрузите устройство: 
```
sudo reboot
```
После перезагрузки создаём папку проекта:
```
mkdir -p ~/HearMe
cd ~/HearMe
```
Далее создаём и активируем виртуальное окружение:
```
python3 -m venv venv
source venv/bin/activate
```
Обновляем pip и скачиваем библиотеки:
```
sudo apt update && sudo apt install -y libportaudio2
pip install --upgrade pip
pip install -r requirements.txt
```
Следующий ваш шаг - это распаковка моделей с флешки. Введите эти команды для распаковки моделей Vosk(Не забудьте поменять названия Юзера и флшеки):
```
unzip /media/YOUR_USER_NAME/YOUR_NAME_USB/vosk-model-small-ru-0.22.zip -d ~/HearMe/
mv ~/HearMe/vosk-model-small-ru-0.22 ~/HearMe/model_ru
```
```
unzip /media/YOUR_USER_NAME/YOUR_NAME_USB/vosk-model-small-en-us-0.15.zip -d ~/HearMe/
mv ~/HearMe/vosk-model-small-en-us-0.15 ~/HearMe/model_en
```
```
python3 -c "import argostranslate.package; \
argostranslate.package.install_from_path('/media/YOUR_USER_NAME/YOUR_NAME_USB/translate-ru_en-1_9.argosmodel'); \
argostranslate.package.install_from_path('/media/YOUR_USER_NAME/YOUR_NAME_USB/translate-en_ru-1_9.argosmodel')"
```
Остаётся запустить наш проект:
```
cd ~/HearMe
source venv/bin/activate
python hearme.py
```
Также рекомендую поставить файл на автозагрузку, чтобы не запускать его каждый раз самостоятельно:
```
chmod +x ~/HearMe/start.sh
```
Создаём кофигурационный файл:
```
mkdir -p ~/.config/autostart
nano ~/.config/autostart/hearme.desktop
```
Вставьте в него следующие строки:
```
[Desktop Entry]
Type=Application
Name=HearMe
Comment=Start HearMe Translator on Boot
Exec=/home/shannyo/HearMe/start.sh
Terminal=false
X-GNOME-Autostart-enabled=true
```
Сохраняем(Ctrl+O, Enter) и выходим(Ctrl+X) и перезапускаем:
```
sudo reboot
```