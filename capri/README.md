# Capri — Python Edition

Портативное desktop-приложение (Windows) с персонажем Капри из Cyberpunk: Edgerunners 2.

## Стек
- **Python 3.11+** + **PyQt6** (окно, анимации, звуки)
- **PyInstaller** (portable-сборка)
- Rule-based диалоги (без ИИ/LLM)
- Полностью автономное

## Установка
```
pip install -r requirements.txt
```

## Запуск
```
python main.py
```

## Сборка (portable)
```
build.bat
```
Или вручную:
```
pyinstaller --noconfirm --windowed --name Capri --add-data "assets;assets" main.py
```

## Структура
```
capri/
├── main.py              # точка входа
├── core/                # состояние + шина событий
├── overlay/             # прозрачное окно (PyQt6)
├── audio/               # звуки (pygame)
├── events/              # отслеживание окон и бездействия
├── dialogue/            # фразы из JSON
├── files/               # работа с файлами
├── assets/              # спрайты, звуки, фразы
├── build.bat            # сборка
└── requirements.txt
```

## Перетаскивание окна
Зажми левую кнопку мыши на аватаре Капри и тащи — окно переместится.

## Фразы
Все реплики в `assets/phrases.json`. Категории: greeting, idle, browser, work, error, file_create, file_open, night, morning, window_change.