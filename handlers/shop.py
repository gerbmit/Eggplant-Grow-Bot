from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database import db
import time
import random

router = Router()

GROW_COOLDOWN = 17 * 60 * 60

ITEMS = {
    "immune": {
        "name": "🛡 Бронетрусы",
        "desc": "Защита от уменьшения или урона босса.",
        "price": 30,
        "type": "buff",
        "db_field": "immune"
    },
    "double": {
        "name": "💊 Стероиды",
        "desc": "Умножает следующий удачный /grow на х2.",
        "price": 50,
        "type": "buff",
        "db_field": "double_bonus"
    },
    "trap": {
        "name": "🪤 Капкан на вора",
        "desc": "Спрячь его в штаны. Если кто-то решит тебя ограбить — вор лишится 30 см, а кража сорвется!",
        "price": 40,
        "type": "buff",
        "db_field": "has_trap"
    },
    "energy": {
        "name": "☕️ Энергетик",
        "desc": "Сбрасывает таймер команды /grow.",
        "price": 75,
        "type": "action"
    },
    "box": {
        "name": "📦 Черный Ящик",
        "desc": "Кот в мешке. Можно уйти в минус, а можно сорвать куш!",
        "price": 40,
        "type": "random"
    },
    "bait": {
        "name": "🥩 Приманка для Босса",
        "desc": "Мгновенно призывает монстра в чат, даже если у него кулдаун. Идеально для рейдов!",
        "price": 150,
        "type": "action"
    }
}

@router.message(Command("shop"))
async def cmd_shop(message: Message):
    user = await db.get_user(message.from_user.id, message.chat.id)
    
    if not user or user['banned']:
        return await message.answer("❌ Тебя нет в списках живых. Напиши /grow.")
        
    if user['size'] <= 0:
        return await message.answer(
            "🛑 <b>Фейсконтроль не пройден!</b>\n\n"
            "Охранник смотрит на твои 0 см, громко смеется и вышвыривает тебя из магазина. Возвращайся, когда хоть немного подрастешь!",
            parse_mode="HTML"
        )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=f"🛡 Щит ({ITEMS['immune']['price']})", callback_data="shop_buy_immune"),
            InlineKeyboardButton(text=f"💊 Стероиды ({ITEMS['double']['price']})", callback_data="shop_buy_double")
        ],
        [
            InlineKeyboardButton(text=f"🪤 Капкан ({ITEMS['trap']['price']})", callback_data="shop_buy_trap"),
            InlineKeyboardButton(text=f"🥩 Приманка ({ITEMS['bait']['price']})", callback_data="shop_buy_bait")
        ],
        [
            InlineKeyboardButton(text=f"☕️ Энергетик ({ITEMS['energy']['price']})", callback_data="shop_buy_energy"),
            InlineKeyboardButton(text=f"📦 Ящик ({ITEMS['box']['price']})", callback_data="shop_buy_box")
        ]
    ])

    text = (
        f"🏴‍☠️ <b>ТЕНЕВОЙ РЫНОК</b> 🏴‍☠️\n"
        f"💳 Твой баланс: <b>{user['size']} см</b>\n\n"
        f"<b>1. {ITEMS['immune']['name']}</b> ({ITEMS['immune']['price']} см)\n"
        f"📝 <i>{ITEMS['immune']['desc']}</i>\n\n"
        f"<b>2. {ITEMS['double']['name']}</b> ({ITEMS['double']['price']} см)\n"
        f"📝 <i>{ITEMS['double']['desc']}</i>\n\n"
        f"<b>3. {ITEMS['trap']['name']}</b> ({ITEMS['trap']['price']} см)\n"
        f"📝 <i>{ITEMS['trap']['desc']}</i>\n\n"
        f"<b>4. {ITEMS['bait']['name']}</b> ({ITEMS['bait']['price']} см)\n"
        f"📝 <i>{ITEMS['bait']['desc']}</i>\n\n"
        f"<b>5. {ITEMS['energy']['name']}</b> ({ITEMS['energy']['price']} см)\n"
        f"📝 <i>{ITEMS['energy']['desc']}</i>\n\n"
        f"<b>6. {ITEMS['box']['name']}</b> ({ITEMS['box']['price']} см)\n"
        f"📝 <i>{ITEMS['box']['desc']}</i>\n"
    )

    await message.answer(text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data.startswith("shop_buy_"))
async def process_buy(callback: CallbackQuery):
    item_key = callback.data.split("_")[2]
    item = ITEMS.get(item_key)
    chat_id = callback.message.chat.id
    user_id = callback.from_user.id

    if not item:
        return await callback.answer("❌ Товар не найден!", show_alert=True)

    user = await db.get_user(user_id, chat_id)
    if not user:
        return await callback.answer("❌ Ошибка профиля.", show_alert=True)

    if item['type'] == 'buff' and user[item['db_field']]:
        return await callback.answer(f"❌ У тебя уже куплен этот предмет!", show_alert=True)

    if item['type'] == 'action' and item_key == 'energy':
        current_time = int(time.time())
        if current_time - user['last_grow'] >= GROW_COOLDOWN:
            return await callback.answer("❌ Твой питомец и так отдохнул! Иди пиши /grow.", show_alert=True)

    # Проверка на вызов босса
    if item_key == 'bait':
        boss = await db.get_boss(chat_id)
        if boss and boss['hp'] > 0:
            return await callback.answer("❌ Босс УЖЕ в чате! Куда тебе еще одного?!", show_alert=True)

    if user['size'] < item['price']:
        return await callback.answer(f"❌ Нищеброд! Нужно {item['price']} см, а у тебя {user['size']}.", show_alert=True)

    new_size = user['size'] - item['price']
    update_data = {"size": new_size}
    result_text = f"🛒 <b>ТЕНЕВОЙ РЫНОК</b>\n\n✅ Успешно куплено: <b>{item['name']}</b>\n"

    if item['type'] == 'buff':
        update_data[item['db_field']] = True
        result_text += f"<i>Предмет спрятан в штаны и сработает автоматически!</i>"

    elif item['type'] == 'action' and item_key == 'energy':
        update_data['last_grow'] = 0 
        result_text += f"⚡️ <b>Таймер сброшен!</b> Пиши <code>/grow</code> прямо сейчас!"

    elif item_key == 'bait':
        # Спавним босса прямо отсюда!
        boss_names = ["🦖 Писюнозавр Рекс", "🦍 Кинг-Донг", "👽 Инопланетный Заглот", "👾 Мутант-Кастратор", "✂️ Безумный Парикмахер", "🥒 Огуречный Потрошитель"]
        name = random.choice(boss_names)
        max_hp = random.randint(500, 2000)
        
        await db.summon_boss(chat_id, name, max_hp, max_hp, int(time.time()))
        result_text += f"🥩 <b>Приманка брошена!</b> В чат уже бежит монстр!"
        
        # Оповещаем весь чат
        await callback.message.bot.send_message(
            chat_id,
            f"⚠️ <b>ВНИМАНИЕ! ТРЕВОГА!</b> ⚠️\n\n"
            f"Игрок <b>{user['first_name']}</b> бросил кусок приманки, и на запах прибежал <b>{name}</b>!\n"
            f"❤️ ХП: <b>{max_hp}</b>\n\n"
            f"Хватайте свои агрегаты и бейте его командой <code>/hit</code>!",
            parse_mode="HTML"
        )

    elif item['type'] == 'random' and item_key == 'box':
        box_outcomes = [
            {"val": -20, "text": "🤬 В боксе сидел голодный хомяк и откусил тебе кусок!", "weight": 15},
            {"val": 5, "text": "😐 В боксе лежали какие-то крохи...", "weight": 25},
            {"val": 30, "text": "👍 Неплохо, часть стоимости отбита.", "weight": 35},
            {"val": 70, "text": "🎉 Ого! Отличный навар!", "weight": 15},
            {"val": 150, "text": "💎 ДЖЕКПОТ! Внутри оказался секретный чертеж гигантизма!", "weight": 10}
        ]
        weights = [r['weight'] for r in box_outcomes]
        outcome = random.choices(box_outcomes, weights=weights, k=1)[0]
        
        final_size = max(0, new_size + outcome['val'])
        update_data['size'] = final_size
        result_text = f"📦 <b>СЕКРЕТНЫЙ БОКС ОТКРЫТ!</b>\n\n{outcome['text']} (<b>{'+' if outcome['val'] > 0 else ''}{outcome['val']} см</b>)\n"

    await db.update_user(user_id, chat_id, **update_data)
    
    if 'size' in update_data:
        result_text += f"\n📏 Твой остаток: <b>{update_data['size']} см</b>"

    await callback.message.edit_text(result_text, parse_mode="HTML")
    await callback.answer("Покупка прошла успешно!")