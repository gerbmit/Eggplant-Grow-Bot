from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from database import db
import time

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    user = await db.get_user(message.from_user.id)
    if not user:
        await db.add_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username or "",
            first_name=message.from_user.first_name or "Без имени",
            created_at=int(time.time())
        )
    
    if user and user['banned']:
        return await message.answer("❌ Вы заблокированы.")
        
    await message.answer(
        "👋 Добро пожаловать в игру <b>«Вырасти писюн»</b>!\n\n"
        "🍆 Используй команду /grow, чтобы начать.\n"
        "🏆 Соревнуйся с другими игроками и получай достижения!",
        parse_mode="HTML"
    )