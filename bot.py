import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from database import db
from middlewares.throttling import ThrottlingMiddleware
from middlewares.chat_type import GroupOnlyMiddleware

# Импорт роутеров (добавили boss)
from handlers import start, game, bonus, profile, rating, admin, duel, casino, steal, global_top, shop, boss , airdrop, fap, pay

async def main():
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )

    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage() # Память, чтобы бот не забывал, что ты делаешь рассылку!
    dp = Dispatcher(storage=storage)
    
    await db.init_db()

    # Подключение middlewares
    dp.message.middleware(ThrottlingMiddleware(limit=1.0))
    dp.message.middleware(GroupOnlyMiddleware())

    # Регистрация роутеров
    dp.include_router(admin.router)
    dp.include_router(start.router)
    dp.include_router(game.router)
    dp.include_router(bonus.router) # ВОТ ТУТ МЫ ПОДКЛЮЧИЛИ СУНДУКИ
    dp.include_router(profile.router)
    dp.include_router(rating.router)
    dp.include_router(duel.router)
    dp.include_router(casino.router)
    dp.include_router(steal.router)
    dp.include_router(global_top.router)
    dp.include_router(shop.router)
    dp.include_router(boss.router) # ПОДКЛЮЧИЛИ БОССОВ
    dp.include_router(airdrop.router) 
    dp.include_router(fap.router)
    dp.include_router(pay.router)
    # Установка и запуск поллинга
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен.")