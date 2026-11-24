from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database import db
import time
import random

router = Router()

# Таймер бонуса - 16 часов
BONUS_COOLDOWN = 16 * 60 * 60 

# Список возможных наград
REWARDS = [
    {"type": "size", "val": 25, "text": "🔥 Джекпот (+25 см)", "weight": 5},
    {"type": "size", "val": 15, "text": "💰 Солидный куш (+15 см)", "weight": 15},
    {"type": "size", "val": 10, "text": "💵 Обычный плюс (+10 см)", "weight": 20},
    {"type": "size", "val": 5, "text": "🪙 Копейка (+5 см)", "weight": 20},
    {"type": "trap", "val": -5, "text": "🐭 Мышеловка (-5 см)", "weight": 15},
    {"type": "trap", "val": -12, "text": "💣 Капкан (-12 см)", "weight": 5},
    {"type": "buff", "val": "immune", "text": "🛡 Щит", "weight": 10},
    {"type": "buff", "val": "double", "text": "✖️2️⃣ Стероиды", "weight": 10}
]

@router.message(Command("bonus"))
async def cmd_bonus(message: Message):
    # ПРЕДОХРАНИТЕЛЬ: Проверяем, включены ли сундуки в админ-панели
    if not await db.get_setting("module_bonus"):
        return await message.answer("❌ Бонусные сундуки временно отключены администратором.")

    user = await db.get_user(message.from_user.id, message.chat.id)
    if not user:
        return await message.answer("❌ Сначала используй /grow")
    if user['banned']:
        return

    current_time = int(time.time())
    
    # Проверка таймера
    if current_time - user['last_bonus'] < BONUS_COOLDOWN:
        remains = BONUS_COOLDOWN - (current_time - user['last_bonus'])
        hours = remains // 3600
        minutes = (remains % 3600) // 60
        return await message.answer(f"⏳ Сундуки еще в пути! Возвращайся через <b>{hours} ч. {minutes} мин.</b>", parse_mode="HTML")

    # Генерируем клавиатуру с 3 сундуками
    uid = message.from_user.id
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎁 1", callback_data=f"chest_{uid}_1"),
            InlineKeyboardButton(text="🎁 2", callback_data=f"chest_{uid}_2"),
            InlineKeyboardButton(text="🎁 3", callback_data=f"chest_{uid}_3")
        ]
    ])

    await message.answer(
        "🏴‍☠️ <b>Контрабанда прибыла!</b>\n\n"
        "Перед тобой 3 сундука. Внутри могут быть крутые баффы, сантиметры или <b>опасная ловушка</b>.\n\n"
        "<i>Выбирай с умом:</i>", 
        reply_markup=kb, 
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("chest_"))
async def process_chest(callback: CallbackQuery):
    # ПРЕДОХРАНИТЕЛЬ для кнопок: Проверяем, включены ли сундуки
    if not await db.get_setting("module_bonus"):
        return await callback.answer("❌ Бонусные сундуки временно отключены администратором.", show_alert=True)

    data_parts = callback.data.split("_")
    target_uid = int(data_parts[1])
    chosen_chest = int(data_parts[2])
    chat_id = callback.message.chat.id

    # Проверка: тот ли человек кликает?
    if callback.from_user.id != target_uid:
        return await callback.answer("❌ Это не твои сундуки! Напиши /bonus", show_alert=True)

    user = await db.get_user(target_uid, chat_id)
    if not user:
        return await callback.answer("❌ Ошибка профиля.", show_alert=True)

    current_time = int(time.time())

    # ЖЕСТКАЯ ПРОВЕРКА: Если игрок уже нажал на сундук секунду назад - блокируем
    if current_time - user['last_bonus'] < BONUS_COOLDOWN:
        return await callback.answer("❌ Ты уже открыл сундук!", show_alert=True)

    # Генерируем 3 УНИКАЛЬНЫХ содержимых
    available_rewards = list(REWARDS)
    chest_contents = []
    
    for _ in range(3):
        weights = [r['weight'] for r in available_rewards]
        chosen = random.choices(available_rewards, weights=weights, k=1)[0]
        chest_contents.append(chosen)
        available_rewards.remove(chosen)
    
    # Берем приз из того сундука, который выбрал игрок
    won_reward = chest_contents[chosen_chest - 1]
    
    update_data = {"last_bonus": current_time}
    result_text = f"🏴‍☠️ <b>СУНДУКИ ОТКРЫТЫ</b> 🏴‍☠️\n\n"

    if won_reward['type'] == "size":
        new_size = max(0, user['size'] + won_reward['val'])
        update_data['size'] = new_size
        
        if won_reward['val'] > 0:
            result_text += f"🎉 Твой приз: <b>{won_reward['text']}</b>\n"
        else:
            result_text += f"💀 Упс... Твой приз: <b>{won_reward['text']}</b>\n"

    elif won_reward['type'] == "trap":
        # Ловушка просто отнимает см. Мы больше НЕ трогаем Щит (immune).
        new_size = max(0, user['size'] + won_reward['val'])
        update_data['size'] = new_size
        result_text += f"💀 Упс... Твой приз: <b>{won_reward['text']}</b>\n"
        
        # Если у игрока есть щит, просто напоминаем ему об этом
        if user['immune']:
            result_text += "<i>(Твой Щит не потратился на эту мелочь и ждет команды /grow)</i>\n"

    elif won_reward['type'] == "buff":
        if won_reward['val'] == "immune":
            if user['immune']:
                update_data['size'] = user['size'] + 10
                result_text += "🛡 Тебе выпал <b>Иммунитет</b>, но он у тебя уже есть!\n🔄 <i>Компенсация: <b>+10 см</b>.</i>\n"
            else:
                update_data['immune'] = True
                result_text += "🎉 Твой приз: 🛡 <b>Иммунитет от уменьшения!</b>\n"
        elif won_reward['val'] == "double":
            if user['double_bonus']:
                update_data['size'] = user['size'] + 10
                result_text += "✖️2️⃣ Тебе выпали <b>Стероиды</b>, но они у тебя уже есть!\n🔄 <i>Компенсация: <b>+10 см</b>.</i>\n"
            else:
                update_data['double_bonus'] = True
                result_text += "🎉 Твой приз: ✖️2️⃣ <b>Стероиды (Двойной рост)!</b>\n"

    # Обновляем БД
    await db.update_user(target_uid, chat_id, **update_data)

    # Показываем содержимое ВСЕХ сундуков
    result_text += "\n📦 <b>Что было в сундуках:</b>\n"
    for i in range(3):
        pointer = "👉 " if i == (chosen_chest - 1) else "   "
        result_text += f"{pointer}Сундук {i+1}: {chest_contents[i]['text']}\n"

    if 'size' in update_data:
        result_text += f"\n📏 Твой новый размер: <b>{update_data['size']} см</b>"

    await callback.message.edit_text(result_text, parse_mode="HTML")
    await callback.answer("Сундук открыт!")