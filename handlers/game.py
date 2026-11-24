from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from database import db
import time
import random
import json
from utils.achievements import check_achievements

router = Router()

GROW_COOLDOWN = 17 * 60 * 60  # Максимальный таймер 17 часов

MINI_EVENTS = [
    {"name": "💊 Волшебная таблетка", "value": 25},
    {"name": "🏥 Визит к врачу", "value": -12},
    {"name": "🏋️ Поход в спортзал", "value": 18},
    {"name": "🔥 Генетический прорыв", "value": 30},
    {"name": "🍄 Съеден подозрительный гриб", "value": -15}
]

GROW_SUCCESS_MESSAGES = [
    "📈 <b>Хороший рост!</b> К твоей мощи добавляется <b>+{amount} см</b>.",
    "🍆 <b>Размер имеет значение!</b> +<b>{amount} см</b>, отличный результат.",
    "🚀 <b>Рывок!</b> Твой питомец вытягивается на <b>{amount} см</b>.",
    "🎉 <b>Святые угодники!</b> Прибавка составила <b>{amount} см</b>.",
    "💪 <b>Качалка не прошла даром!</b> +<b>{amount} см</b> к твоему арсеналу.",
    "😎 <b>Рост как на дрожжах!</b> +<b>{amount} см</b>."
]

GROW_FAIL_MESSAGES = [
    "❄️ <b>Холодновато...</b> Писюн сжимается на <b>{amount} см</b>.",
    "📉 <b>Увы.</b> Гравитация оказалась сильнее. <b>-{amount} см</b>.",
    "🫣 <b>Конфуз!</b> От стресса размер уменьшается на <b>{amount} см</b>.",
    "🥱 <b>Усталость...</b> Писюн решает вздремнуть и теряет <b>{amount} см</b>.",
    "🤔 <b>Показалось?</b> Нет, реально потеряно <b>{amount} см</b>.",
    "⛈ <b>Нелетная погода.</b> Утеряно <b>{amount} см</b> из-за давления.",
    "🤕 <b>Надо меньше нервничать.</b> -<b>{amount} см</b>."
]

@router.message(Command("grow"))
async def cmd_grow(message: Message):
    user = await db.get_user(message.from_user.id, message.chat.id)
    if not user:
        await db.add_user(
            telegram_id=message.from_user.id,
            chat_id=message.chat.id,
            username=message.from_user.username or "",
            first_name=message.from_user.first_name or "Без имени",
            created_at=int(time.time())
        )
        user = await db.get_user(message.from_user.id, message.chat.id)

    if user['banned']:
        return
        
    current_time = int(time.time())
    last_grow = user['last_grow']
    
    if current_time - last_grow < GROW_COOLDOWN:
        remains = GROW_COOLDOWN - (current_time - last_grow)
        hours = remains // 3600
        minutes = (remains % 3600) // 60
        return await message.answer(f"⏳ Следующий рост доступен через <b>{hours} ч. {minutes} мин.</b>", parse_mode="HTML")

    size_change = 0
    event_msg = ""
    immune = user['immune']
    double_bonus = user['double_bonus']
    
    try:
        is_cursed = user['cursed']
    except (KeyError, IndexError):
        is_cursed = False

    # ПРОВЕРКА НА АДМИНСКОЕ ПРОКЛЯТИЕ
    if is_cursed:
        size_change = -200
        event_msg = "⛈ <b>ГНЕВ БОГОВ!</b> На тебя обрушилось древнее проклятие! Твой агрегат почернел и отсох...\n"
        immune = False # Проклятие пробивает любой щит!
        is_cursed = False # Снимаем проклятие после использования
    else:
        # Обычный сценарий
        if random.random() < 0.10: # 10% шанс на мини-событие
            event = random.choice(MINI_EVENTS)
            size_change = event["value"]
            event_msg = f"🎲 <b>Событие:</b> {event['name']}!\n"
        else:
            if random.random() < 0.80: # 80% шанс на рост
                size_change = random.randint(1, 15)
            else: # 20% шанс на уменьшение
                size_change = random.randint(-8, -1)

    if size_change < 0 and immune:
        size_change = 0
        event_msg += "🛡 <b>Сработал иммунитет!</b> Уменьшения не произошло.\n"
        immune = False
    elif size_change > 0 and double_bonus:
        size_change *= 2
        event_msg += "✖️2️⃣ <b>Сработал двойной бонус!</b>\n"
        double_bonus = False

    new_size = user['size'] + size_change
    new_attempts = user['attempts'] + 1
    
    if size_change > 0:
        text = event_msg + random.choice(GROW_SUCCESS_MESSAGES).format(amount=size_change)
    elif size_change < 0:
        text = event_msg + random.choice(GROW_FAIL_MESSAGES).format(amount=abs(size_change))
    else:
        text = f"{event_msg}😐 <b>Ничего не изменилось.</b>"
    
    text += f"\n\n📏 Теперь размер: <b>{new_size} см</b>"
    
    if double_bonus:
        text += "\n\n✨ <i>Бонус 'Двойной рост' все еще активен!</i>"
    if immune:
        text += "\n\n✨ <i>Бонус 'Иммунитет' все еще активен!</i>"

    new_achievements_json, unlocked = check_achievements(user['achievements'], new_size, new_attempts)
    
    if unlocked:
        text += "\n\n🎉 <b>Новые достижения:</b>\n" + "\n".join(unlocked)

    next_cooldown_hours = random.randint(12, 17)
    offset = GROW_COOLDOWN - (next_cooldown_hours * 3600)
    fake_last_grow = current_time - offset
    
    text += f"\n\n⏱ <i>След. попытка через: <b>{next_cooldown_hours} ч.</b></i>"

    await db.update_user(
        telegram_id=user['telegram_id'],
        chat_id=message.chat.id,
        size=new_size,
        attempts=new_attempts,
        last_grow=fake_last_grow,
        immune=immune,
        double_bonus=double_bonus,
        cursed=is_cursed,
        achievements=new_achievements_json
    )
    
    await message.answer(text, parse_mode="HTML")