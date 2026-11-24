from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from database import db

router = Router()

@router.message(Command("globaltop"))
async def cmd_global_top(message: Message):
    top_users = await db.get_global_top(10)
    if not top_users:
        return await message.answer("🌍 Глобальный рейтинг пока пуст.")

    text = "🌍 <b>ГЛОБАЛЬНЫЙ ТОП-10 ИГРОКОВ (По всем чатам)</b>\n\n"
    for idx, user in enumerate(top_users, 1):
        medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else "🔸"
        # Используем max_size, так как запрос возвращает именно его
        text += f"{medal} <b>{idx}. {user['first_name']}</b> — {user['max_size']} см\n"

    await message.answer(text, parse_mode="HTML")