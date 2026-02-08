cd "$(dirname "$0")"
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "Ошибка: Виртуальное окружение venv не найдено!"
    exit 1
fi
./venv/bin/python3 main.py