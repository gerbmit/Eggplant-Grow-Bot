from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from database import db
import json
from datetime import datetime
from utils.achievements import ACHIEVEMENTS_MAP

router = Router()

# Настраиваем пороги званий (мин, макс, название)
TITLES = [
    (0, 10, "🥒 Корнишон"),
    (11, 20, "👷‍♂️ Обычный работяга"),
    (21, 50, "📏 Пикабушник"),
    (51, 100, "🦍 Гигант"),
    (101, 499, "☢️ Мутант"),
    (500, 999, "💍 Властелин колец"),
    (1000, 999999, "💣 Оружие массового поражения")
]

def get_title_info(size: int):
    if size < 0:
        return "🕳 Черная дыра", 0, 0
    for min_s, max_s, title in TITLES:
        if min_s <= size <= max_s:
            return title, min_s, max_s
    return "💣 Оружие массового поражения", 1000, 1000

def generate_progress_bar(size: int, min_s: int, max_s: int) -> str:
    if max_s >= 999999 or size >= 1000:
        return "██████████ (MAX)"
    if size < 0:
        return "░░░░░░░░░░ (0%)"
        
    range_size = max_s - min_s
    if range_size == 0: 
        range_size = 1
        
    current_progress = size - min_s
    percent = current_progress / range_size
    
    # Ограничиваем от 0 до 1
    percent = max(0.0, min(1.0, percent)) 
    
    filled = int(percent * 10)
    empty = 10 - filled
    return f"{'█' * filled}{'░' * empty} ({int(percent * 100)}%)"

@router.message(Command("profile"))
async def cmd_profile(message: Message):
    user = await db.get_user(message.from_user.id, message.chat.id)
    if not user or user['banned']:
        return await message.answer("❌ Сначала используй /grow, чтобы зарегистрироваться.")
        
    rank = await db.get_rank(message.from_user.id, message.chat.id)
    reg_date = datetime.fromtimestamp(user['created_at']).strftime('%d.%m.%Y')
    
    achievements = json.loads(user['achievements'])
    achievements_text = "\n".join([f"🔸 {ACHIEVEMENTS_MAP.get(a, '')}" for a in achievements]) or "<i>Пока нет</i>"
    
    title, min_s, max_s = get_title_info(user['size'])
    progress_bar = generate_progress_bar(user['size'], min_s, max_s)
    
    # Вычисляем средний рост (удачу)
    avg_growth = round(user['size'] / user['attempts'], 1) if user['attempts'] > 0 else 0
    if avg_growth > 0:
        avg_text = f"+{avg_growth}"
    else:
        avg_text = str(avg_growth)

    # Проверяем активные баффы
    active_buffs = []
    if user['immune']:
        active_buffs.append("🛡 Щит (Иммунитет)")
    if user['double_bonus']:
        active_buffs.append("✖️2️⃣ Стероиды (Двойной рост)")
    
    buffs_str = "\n".join([f"🔹 {b}" for b in active_buffs]) if active_buffs else "<i>Пусто (загляни в /shop или /bonus)</i>"

    text = (
        f"👤 <b>ДОСЬЕ ИГРОКА</b>\n"
        f"Имя: <b>{user['first_name']}</b>\n"
        f"Звание: <b>{title}</b>\n"
        f"Прогресс до следующего ранга:\n"
        f"<code>[{progress_bar}]</code>\n\n"
        
        f"📊 <b>СТАТИСТИКА:</b>\n"
        f"📏 Размер: <b>{user['size']} см</b>\n"
        f"🏆 Место в топе: <b>#{rank}</b>\n"
        f"🎲 Попыток роста: <b>{user['attempts']}</b>\n"
        f"📈 Средний рост: <b>{avg_text} см/раз</b>\n\n"
        
        f"🎒 <b>АКТИВНЫЕ ЭФФЕКТЫ:</b>\n"
        f"{buffs_str}\n\n"
        
        f"🏅 <b>ДОСТИЖЕНИЯ:</b>\n"
        f"{achievements_text}\n\n"
        
        f"📅 <i>В игре с: {reg_date}</i>"
    )
    
    await message.answer(text, parse_mode="HTML")