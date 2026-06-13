import os
from dotenv import load_dotenv

# Загружаем переменные из файла .env
load_dotenv()

# Получаем токен. Если его нет в .env, бот выдаст ошибку
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Переменная BOT_TOKEN не найдена в .env файле!")

CALENDAR_ID = os.getenv("CALENDAR_ID")
if not CALENDAR_ID:
    raise ValueError("Переменная CALENDAR_ID не найдена в .env файле!")

ADMIN_IDS = os.getenv("ADMIN_IDS")
if not ADMIN_IDS:
    raise ValueError("Переменная ADMIN_IDS не найдена в .env файле!")