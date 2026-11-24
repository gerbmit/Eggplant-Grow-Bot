from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database import db
from aiogram.filters import Command
from utils.filters import IsAdmin
import time
import random
import asyncio

# Смешные универсальные фразы для появления дропа
SPAWN_TEXTS = [
    "🚨 <b>ВНЕЗАПНЫЙ АИРДРОП!</b> 🚨\n\nНа дороге валяются бесхозные <b>{amount} см</b>!\nЖми кнопку быстрее всех!",
    "🚚 <b>АВАРИЯ!</b> На трассе перевернулась фура с баклажанами! В луже плещутся <b>{amount} см</b>!",
    "🛸 <b>СЕКРЕТНЫЕ МАТЕРИАЛЫ!</b> НЛО сбросило инопланетный контейнер. Внутри светится <b>{amount} см</b>!",
    "🍌 <b>НАХОДКА!</b> Кто-то в спешке потерял заначку! Бесхозные <b>{amount} см</b> ищут нового владельца!",
    "🏃 <b>ГОП-СТОП!</b> Местный воришка скинул <b>{amount} см</b>, пока убегал от собак. Забирай, пока никто не видит!"
]

# Гендерно-нейтральные фразы для того, кто забрал (используем настоящее время)
CLAIM_TEXTS = [
    "🏎 <b>{name}</b> на скорости света забирает себе <b>{amount} см</b>!",
    "🥷 <b>{name}</b> расталкивает всех локтями и прячет <b>{amount} см</b> в карман!",
    "🦅 <b>{name}</b> коршуном пикирует на добычу и успешно присваивает <b>{amount} см</b>!",
    "🎩 <b>{name}</b> ловким движением фокусника кладет <b>{amount} см</b> в свою копилку!",
    "🤤 <b>{name}</b> без стеснения поднимает трофей с пола... Зато теперь баланс пополнен на <b>+{amount} см</b>!",
    "👑 <b>{name}</b> празднует победу! Бесхозные <b>{amount} см</b> нашли своего нового владельца!"
]

router = Router()

# ⏱ ИЗМЕНЕНО: Кулдаун между дропами теперь 3 минуты (было 10)
AIRDROP_COOLDOWN = 3 * 60 
last_drops = {} # Хранит время последнего случайного дропа для каждого чата

async def spawn_airdrop(message: Message, amount: int):
    """Функция спавна аирдропа"""
    drop_id = random.randint(10000, 99999)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🎁 Забрать {amount} см!", callback_data=f"airdrop_{amount}_{drop_id}")]
    ])

    # Выбираем случайный текст и подставляем в него размер
    text = random.choice(SPAWN_TEXTS).format(amount=amount)

    await message.answer(
        text,
        reply_markup=kb,
        parse_mode="HTML"
    )

@router.message(Command("forcedrop"), IsAdmin())
async def cmd_forcedrop(message: Message):
    """Секретная команда для админа: глобальный аирдроп во все чаты"""
    chats = await db.get_all_unique_chats()
    if not chats:
        return await message.answer("❌ В базе нет ни одной группы!")
        
    amount = 50
    count = 0
    await message.answer(f"🚀 Вылетаем раскидывать аирдроп ({amount} см) по {len(chats)} группам...")
    
    for chat_id in chats:
        # Генерируем уникальный дроп для каждой группы
        drop_id = random.randint(10000, 99999)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"🎁 Забрать {amount} см!", callback_data=f"airdrop_{amount}_{drop_id}")]
        ])
        text = random.choice(SPAWN_TEXTS).format(amount=amount)
        
        try:
            # Отправляем сообщение напрямую в нужный чат
            await message.bot.send_message(chat_id, text, reply_markup=kb, parse_mode="HTML")
            count += 1
            await asyncio.sleep(0.05) # Пауза, чтобы телеграм не забанил за спам
        except Exception:
            continue # Если бота удалили из группы - просто пропускаем
            
    await message.answer(f"✅ Глобальный аирдроп успешно сброшен в {count} групп(ы)!")

@router.message(F.text & ~F.text.startswith('/'))
async def random_airdrop_handler(message: Message):
    if not await db.get_setting("module_airdrop"):
        return

    """Случайный дроп от обычных сообщений в чате (полный автомат)"""
    chat_id = message.chat.id
    current_time = int(time.time())
    
    # 1. Проверяем кулдаун
    if chat_id in last_drops:
        if current_time - last_drops[chat_id] < AIRDROP_COOLDOWN:
            return # Еще слишком рано
            
    # 2. 🎲 ИЗМЕНЕНО: Шанс 20% на каждое сообщение
    if random.random() > 0.20:
        return
        
    # 3. Спавним аирдроп
    last_drops[chat_id] = current_time
    amount = random.randint(10, 30)
    await spawn_airdrop(message, amount)

@router.callback_query(F.data.startswith("airdrop_"))
async def process_airdrop_claim(callback: CallbackQuery):
    parts = callback.data.split("_")
    amount = int(parts[1])
    chat_id = callback.message.chat.id
    user_id = callback.from_user.id

    user = await db.get_user(user_id, chat_id)
    if not user:
        return await callback.answer("❌ Сначала зарегистрируйся (напиши /grow)", show_alert=True)
    if user['banned']:
        return await callback.answer("❌ Ты в бане!", show_alert=True)

    # 🛑 СЕКРЕТНАЯ ПРОВЕРКА НА БАН АИРДРОПОВ 🛑
    try:
        if user['airdrop_banned']:
            return await callback.answer("🐌 Упс! Шнурки развязались, ты споткнулся и кто-то забрал дроп быстрее...", show_alert=True)
    except KeyError:
        pass

    new_size = user['size'] + amount

    # Выбираем случайный текст для победителя
    claim_msg = random.choice(CLAIM_TEXTS).format(name=callback.from_user.first_name, amount=amount)
    
    text = (
        f"✅ <b>АИРДРОП ЗАБРАН!</b>\n\n"
        f"{claim_msg}\n"
        f"📏 Теперь его размер: <b>{new_size} см</b>"
    )

    try:
        await callback.message.edit_text(text, parse_mode="HTML")
        # Если код дошел сюда, значит этот игрок 100% первый!
        await db.update_user(user_id, chat_id, size=new_size)
        await callback.answer(f"🎉 Ты успешно забрал {amount} см!", show_alert=True)
    except Exception:
        # Ошибка редактирования = кнопка уже была нажата кем-то другим
        await callback.answer("🐌 Упс! Кто-то оказался быстрее тебя...", show_alert=True)