from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from database import db

router = Router()

@router.message(Command("top"))
async def cmd_top(message: Message):
    top_users = await db.get_top(message.chat.id, 10)
    if not top_users:
        return await message.answer("Рейтинг пока пуст.")

    text = "🏆 <b>ТОП-10 игроков</b>\n\n"
    for idx, user in enumerate(top_users, 1):
        medal = "🥇" if idx == 1 else "🥈" if idx == 2 else "🥉" if idx == 3 else "🔸"
        text += f"{medal} <b>{idx}. {user['first_name']}</b> — {user['size']} см\n"

    await message.answer(text, parse_mode="HTML")

@router.message(Command("me"))
async def cmd_me(message: Message):
    rank = await db.get_rank(message.from_user.id, message.chat.id)
    if rank == 0:
        return await message.answer("Ты еще не зарегистрирован. Нажми /grow")
    
    await message.answer(f"📍 Твое место в рейтинге этого чата: <b>#{rank}</b>", parse_mode="HTML")

@router.message(Command("stats"))
async def cmd_stats(message: Message):
    stats = await db.get_stats(message.chat.id)
    if not stats or stats['total'] == 0:
        return await message.answer("Статистика пуста.")

    text = (
        f"📊 <b>Статистика бота</b>\n\n"
        f"👥 Всего игроков: <b>{stats['total']}</b>\n"
        f"📏 Средний размер: <b>{int(stats['avg_size'] or 0)} см</b>\n"
        f"📈 Максимальный: <b>{stats['max_size'] or 0} см</b>\n"
        f"📉 Минимальный: <b>{stats['min_size'] or 0} см</b>"
    )
    await message.answer(text, parse_mode="HTML")