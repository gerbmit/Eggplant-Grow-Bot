from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from database import db
from config import ADMIN_ID
import random
import logging

router = Router()

@router.message(Command("casino"))
async def cmd_casino(message: Message):
    if not await db.get_setting("module_casino"):
        return await message.answer("❌ Казино временно закрыто администратором.")
        
    user_id = message.from_user.id
    chat_id = message.chat.id
        
    user = await db.get_user(user_id, chat_id)
    if not user:
        return await message.answer("❌ Сначала используй /grow")
    if user['banned']:
        return

    args = message.text.split()
    if len(args) < 2:
        return await message.answer(
            f"{message.from_user.first_name}, ❌ Укажи ставку.\nПример: <code>/casino 10</code> или <code>/casino all</code> (ва-банк)", 
            parse_mode="HTML"
        )

    bet_str = args[1].lower()
    if bet_str == "all":
        bet = user['size']
    elif bet_str.isdigit():
        bet = int(bet_str)
    else:
        return await message.answer(f"{message.from_user.first_name}, ❌ Ставка должна быть числом или словом 'all'.")

    if bet <= 0:
        return await message.answer(f"{message.from_user.first_name}, ❌ Ставка должна быть больше нуля! Иди расти.")

    if user['size'] < bet:
        return await message.answer(f"{message.from_user.first_name}, ❌ Не хватает сантиметров! Твой размер: <b>{user['size']} см</b>", parse_mode="HTML")

    # --- ПРОВЕРКА НА РЕЖИМ БОГА ---
    is_godmode = False
    if user_id == ADMIN_ID:
        is_godmode = await db.get_setting("admin_godmode", default=0)

    # Набор символов для слот-машины
    emojis = ['🍒', '🍋', '🍉', '🔔', '💎', '7️⃣', '🍀', '🍇']
    
    if is_godmode:
        # БОЖЕСТВЕННАЯ ПОДКРУТКА: Всегда выигрыш 3 в ряд!
        if random.random() < 0.30:
            # 30% шанс на Мега Джекпот
            reel1 = reel2 = reel3 = '💎'
        else:
            # 70% шанс на обычные х5
            win_emoji = random.choice(['🍒', '🍋', '🍉', '🔔', '7️⃣', '🍀', '🍇'])
            reel1 = reel2 = reel3 = win_emoji
    else:
        # ОБЫЧНАЯ КРУТКА ДЛЯ СМЕРТНЫХ
        reel1 = random.choice(emojis)
        reel2 = random.choice(emojis)
        reel3 = random.choice(emojis)
    
    reels = [reel1, reel2, reel3]
    counts = {e: reels.count(e) for e in emojis}
    max_matches = max(counts.values())
    
    # Списываем ставку перед начислением выигрыша
    user_size_after_bet = user['size'] - bet
    win_amount = 0
    
    if reel1 == reel2 == reel3 == '💎':
        mult = 20
        win_amount = bet * mult
        msg = f"💎💎💎 <b>МЕГА ДЖЕКПОТ!!!</b> Банк сорван! (x{mult})"
    elif max_matches == 3:
        mult = 5
        win_amount = bet * mult
        msg = f"🔥 <b>ТРИ В РЯД!</b> Отличный куш! (x{mult})"
    elif max_matches == 2:
        mult = 1.5
        win_amount = int(bet * mult)
        msg = f"👍 <b>ДВЕ ОДИНАКОВЫЕ!</b> Небольшой плюс. (x{mult})"
    else:
        mult = 0
        msg = "💀 <b>НИЧЕГО НЕ СОВПАЛО.</b> Ставка сгорает!"

    new_size = user_size_after_bet + win_amount
    
    # Защита от минуса
    if new_size < 0:
        new_size = 0

    text = (
        f"🎰 <b>КАЗИНО «ТРИ ТОПОРА»</b> 🎰\n"
        f"👤 Игрок: <b>{message.from_user.first_name}</b>\n"
        f"📏 Ставка: <b>{bet} см</b>\n\n"
        f"Крутим барабаны...\n"
        f"<b>[ {reel1} | {reel2} | {reel3} ]</b>\n\n"
        f"{msg}\n"
    )
    
    if win_amount > 0:
        text += f"Выигрыш: <b>+{win_amount} см</b>\n"
    else:
        text += f"Потеряно: <b>-{bet} см</b>\n"
        
    text += f"\n📏 Теперь твой размер: <b>{new_size} см</b>"

    await db.update_user(user_id, chat_id, size=new_size)
    
    # Отправляем результат (сообщение больше не удаляется)
    await message.answer(text, parse_mode="HTML")