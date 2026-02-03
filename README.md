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
Корпус, напечатанный на 3d принтере
```
Можете найти все ссылки на них в файле source.txt на aliexpress.
Также список всех библиотек и моделей для устройства:
```
tkinter
queue
threading
time
argostranslate
speech_recognition
faster_whisper
gpiozero
```
# Установка обеспечения
Разархивируйте данный репозиторий. Введите следующие команды в bash(для первого запуска необходимо соединение Wi-Fi для скачивания всех файлов):
```
sudo apt update
sudo apt install python3-pip python3-venv portaudio19-dev python3-tk libatlas-base-dev
```
```
mkdir rpi_translator
cd rpi_translator
python3 -m venv venv
source venv/bin/activate
```
Используйте файл requirements.txt в созданной нами среде.
```
pip install -r requirements.txt
```
Если всё удачно установилось, то запускаем файл hearme.py и наслаждаемся нашим устройством. 
```
python3 hearme.py
```
