import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand 

import config 
from handlers import booking
from handlers import profile

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)

# Создаем объекты бота и диспетчера
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher()

# Подключаем обработчики из папки handlers
dp.include_router(profile.router)
dp.include_router(booking.router)

# Функция для настройки кнопки "Меню" в Telegram
async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Перезапустить бота"),
        BotCommand(command="book", description="Забронировать аудиторию"),
        BotCommand(command="help", description="Справка и примеры"),
        BotCommand(command="profile", description="Изменить ФИО (для календаря)"),
    ]
    await bot.set_my_commands(commands)

# Главная функция запуска
async def main():
    print("Бот запускается...")
    
    # Устанавливаем команды меню
    await set_commands(bot)
    
    # Удаляем вебхуки и запускаем опрос серверов (long-polling)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен вручную.")