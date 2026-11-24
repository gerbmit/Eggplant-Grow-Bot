# 🍆 Eggplant Grow Bot

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)
![Telegram](https://img.shields.io/badge/Telegram_Bot-2CA5E0?style=flat-square&logo=telegram&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-003B57?style=flat-square&logo=sqlite&logoColor=white)

Многофункциональный игровой Telegram-бот для групповых чатов. Классическая механика выращивания расширена полноценной экономикой, PvP-сражениями, боссами, мини-играми и системой достижений.

---

## ✨ Возможности

* 🌱 **Основная игра** — регулярный рост, случайные события и прокачка персонажа
* ⚔️ **Дуэли (`duel`)** — PvP-сражения между участниками чата
* 👹 **Боссы (`boss`)** — совместные битвы с боссами и награды за победу
* 🥷 **Кражи (`steal`)** — возможность рискнуть и стащить прогресс у других игроков
* 🎰 **Казино (`casino`)** — мини-игры на внутриигровые ресурсы
* 📦 **Аирдропы (`airdrop`)** — случайные раздачи и ивенты прямо в чате
* 🎁 **Бонусы (`bonus`)** — система регулярных наград
* 🛒 **Магазин и переводы (`shop`, `pay`)** — покупка улучшений и передача ресурсов другим игрокам
* 🏆 **Профиль, достижения и рейтинги (`profile`, `achievements`, `rating`, `global_top`)** — статистика игрока, ачивки, топ чата и глобальный рейтинг
* 🛡️ **Защита и администрирование (`middlewares`, `admin`)** — встроенный антифлуд (throttling), контроль типа чата и расширенная админ-панель

---

## 📁 Структура проекта

```text
Eggplant-Grow-Bot/
├── bot.py                 # Точка входа и запуск бота
├── config.py              # Конфигурация (токен, настройки)
├── database.py            # Работа с базой данных SQLite
├── requirements.txt       # Зависимости проекта
├── handlers/              # Модули игровых команд и механик
│   ├── admin.py           # Админ-панель
│   ├── airdrop.py         # Аирдропы
│   ├── bonus.py           # Бонусы
│   ├── boss.py            # Боссы
│   ├── casino.py          # Казино
│   ├── duel.py            # Дуэли
│   ├── fap.py             # Дополнительные механики
│   ├── game.py            # Основная механика роста
│   ├── global_top.py      # Глобальный рейтинг
│   ├── pay.py             # Переводы между игроками
│   ├── profile.py         # Профиль игрока
│   ├── rating.py          # Рейтинг чата
│   ├── shop.py            # Магазин
│   ├── start.py           # Приветствие и справка
│   └── steal.py           # Кражи
├── middlewares/           # Промежуточные обработчики
│   ├── chat_type.py       # Проверка типа чата
│   └── throttling.py      # Антифлуд / защита от спама
└── utils/                 # Вспомогательные модули
    ├── achievements.py    # Система достижений
    └── filters.py         # Пользовательские фильтры
```

---

## 🚀 Быстрый запуск

### 1. Клонируйте репозиторий
```bash
git clone https://github.com/gerbmit/Eggplant-Grow-Bot.git
cd Eggplant-Grow-Bot
```

### 2. Создайте виртуальное окружение и установите зависимости
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux / macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 3. Настройте конфигурацию
Укажите токен бота (полученный у [@BotFather](https://t.me/BotFather)) и ID администраторов в `config.py` (или в файле `.env`, если используете переменные окружения).

### 4. Запустите бота
```bash
python bot.py
```

---

## 📋 Основные команды

> *(Сюда удобно добавить точный список команд из `handlers/` — например, `/start`, `/top`, `/duel`, `/shop` и т.д.)*

---

## 📬 Контакты

Разработчик: **Dmitry Gerbeev** ([@gerbmit](https://t.me/gerbmit))
