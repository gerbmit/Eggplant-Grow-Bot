from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from database import db
import time
import random
import asyncio

router = Router()

FAP_COOLDOWN = 9 * 60  # 9 минут
GROW_COOLDOWN = 17 * 60 * 60 # 17 часов (нужно для расчетов таймера)

# Храним кулдауны прямо в памяти бота
last_fap_times = {}

FAP_PHRASES = [
    "💦 Быстро, резко, как пуля дерзко! Дело сделано.",
    "🧘‍♂️ Дзен-мастурбация. Полное погружение в астрал. Умиротворение достигнуто.",
    "🔥 Скорость трения превысила звуковой барьер! Из-под одеяла пошел дым.",
    "💪 Отличная тренировка предплечья. Теперь ты можешь открывать банки с огурцами одной левой.",
    "📱 Ты случайно свайпнул маме фотографию в процессе. Инфаркт обеспечен, но назад пути нет.",
    "🧻 Ты опустошил половину рулона туалетной бумаги. Экологи плачут, природа в шоке.",
    "👀 В самый ответственный момент в комнату зашел кот и очень осуждающе посмотрел на тебя.",
    "🎸 Ты сыграл на своем инструменте такое соло, что позавидовал бы Джими Хендрикс!",
    "🔬 Пришлось использовать пинцет и лупу, но упорство и труд всё перетрут!",
    "🏆 Поздравляем! Ты побил свой личный рекорд по скорострельности.",
    "🚑 Чуть не вывихнул кисть, но оно того стоило."
]

TARGET_INTROS = [
    "👤 <b>{u}</b> расчехлил агрегат, не отрывая взгляда от <b>{t}</b>...",
    "👤 <b>{u}</b> посвятил этот яростный сеанс <b>{t}</b>...",
    "👤 <b>{u}</b> сохранил фотку <b>{t}</b> и ушел в астрал..."
]

@router.message(Command("fap"))
async def cmd_fap(message: Message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    user = await db.get_user(user_id, chat_id)
    if not user or user['banned']:
        msg = await message.answer("❌ Сначала нужно вырастить агрегат (/grow), чтобы было что тренировать!")
        asyncio.create_task(delete_delayed(msg, 5))
        try:
            await message.delete()
        except: pass
        return

    current_time = int(time.time())
    key = f"{user_id}_{chat_id}"
    last_time = last_fap_times.get(key, 0)
    
    # 1. Проверка кулдауна на сам /fap
    if current_time - last_time < FAP_COOLDOWN:
        remains = FAP_COOLDOWN - (current_time - last_time)
        m = remains // 60
        s = remains % 60
        msg = await message.answer(f"⏳ Стер до мозолей! Дай руке отдохнуть еще <b>{m} мин. {s} сек.</b>", parse_mode="HTML")
        asyncio.create_task(delete_delayed(msg, 7))
        return
        
    # Обновляем таймер
    last_fap_times[key] = current_time

    # 2. Определение цели
    target_name = None
    if message.reply_to_message:
        target_name = message.reply_to_message.from_user.first_name

    duration = random.choice([
        f"{random.randint(3, 59)} секунд",
        f"{random.randint(1, 5)} минут",
        "целых 12 минут",
        "полтора часа",
        "0.5 секунд"
    ])
    rpm = random.randint(120, 950)
    phrase = random.choice(FAP_PHRASES)
    
    if target_name:
        if message.reply_to_message.from_user.id == message.from_user.id:
            intro = f"👤 <b>{user['first_name']}</b> встал перед зеркалом и решил передернуть на самого себя..."
        elif message.reply_to_message.from_user.is_bot:
            intro = f"👤 <b>{user['first_name']}</b> решил передернуть на железного бота. Киберпанк, который мы заслужили..."
        else:
            intro = random.choice(TARGET_INTROS).format(u=user['first_name'], t=target_name)
    else:
        intro = f"👤 <b>{user['first_name']}</b> уединился и приступил к делу..."

    # 3. ИГРОВАЯ МЕХАНИКА: Влияние на таймер /grow (Теперь это рулетка!)
    grow_remains = GROW_COOLDOWN - (current_time - user['last_grow'])
    bonus_text = ""
    
    if grow_remains > 0:
        roll = random.random()
        
        if roll < 0.35: # 35% Усталость (Штраф по времени)
            penalty = random.randint(20, 60)
            new_last_grow = user['last_grow'] + (penalty * 60)
            bonus_text = f"😴 <b>Усталость взяла своё...</b> Сил на настоящий рост не осталось.\nТаймер /grow <b>УВЕЛИЧЕН</b> на {penalty} минут."
            await db.update_user(user_id, chat_id, last_grow=new_last_grow)
            
        elif roll < 0.65: # 30% Релакс (Бонус)
            reduction = random.randint(15, 30)
            new_last_grow = user['last_grow'] - (reduction * 60)
            bonus_text = f"🧘‍♂️ <b>Стресс снят!</b> Организм расслабился.\nТаймер /grow <b>УМЕНЬШЕН</b> на {reduction} минут."
            await db.update_user(user_id, chat_id, last_grow=new_last_grow)
            
        elif roll < 0.85: # 20% Ничего
            bonus_text = f"🚬 <i>Просто хорошо провел время. На организм это никак не повлияло.</i>"
            
        elif roll < 0.95: # 10% ТРАВМА (Минус см!)
            dmg = random.randint(1, 3)
            new_size = max(0, user['size'] - dmg)
            bonus_text = f"🚑 <b>ТРАВМА!</b> Слишком увлекся и стер агрегат до мозолей!\nПотеряно <b>{dmg} см</b>. <i>(Теперь: {new_size} см)</i>"
            await db.update_user(user_id, chat_id, size=new_size)
            
        else: # 5% Просветление
            reduction = random.randint(60, 120)
            new_last_grow = user['last_grow'] - (reduction * 60)
            bonus_text = f"🤯 <b>ПОСТ-ИРОНИЧНАЯ ЯСНОСТЬ!</b> Мозг заработал на 200%.\nТаймер /grow <b>УМЕНЬШЕН</b> на {reduction} минут!"
            await db.update_user(user_id, chat_id, last_grow=new_last_grow)
    else:
        bonus_text = "✨ <i>Организм и так готов к росту, иди скорее пиши /grow!</i>"

    # Формируем и отправляем текст
    text = (
        f"{intro}\n"
        f"⏱ <b>{duration}</b> | 🔥 <b>{rpm} об/мин</b>\n\n"
        f"<i>{phrase}</i>\n\n"
        f"{bonus_text}"
    )
    
    await message.answer(text, parse_mode="HTML")
    
    try:
        await message.delete()
    except:
        pass

async def delete_delayed(msg: Message, delay: int):
    """Вспомогательная функция для удаления сообщений"""
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except:
        pass