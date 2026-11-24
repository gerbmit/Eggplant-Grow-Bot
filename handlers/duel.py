from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from database import db
import random
import asyncio

router = Router()

async def delete_delayed(msg: Message, delay: int):
    """Фоновая задача для удаления сообщений"""
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except Exception:
        pass

@router.message(Command("duel"))
async def cmd_duel(message: Message):
    if not await db.get_setting("module_duel"):
        m = await message.answer("❌ Дуэли временно отключены администратором.")
        asyncio.create_task(delete_delayed(m, 7))
        return

    # Удаляем саму команду, чтобы не мусорить
    try:
        await message.delete()
    except Exception:
        pass

    # Проверяем, что это ответ на сообщение
    if not message.reply_to_message:
        m = await message.answer(
            "❌ <b>Как вызвать на дуэль:</b>\n"
            "Ответь на сообщение противника командой:\n"
            "<code>/duel 10</code> или <code>/duel all</code> (ва-банк)", 
            parse_mode="HTML"
        )
        asyncio.create_task(delete_delayed(m, 10))
        return

    target_user_id = message.reply_to_message.from_user.id
    challenger_id = message.from_user.id
    chat_id = message.chat.id

    if target_user_id == challenger_id:
        m = await message.answer("❌ С шизофренией к врачу, а не на дуэль. Драться с собой нельзя!")
        asyncio.create_task(delete_delayed(m, 7))
        return

    if message.reply_to_message.from_user.is_bot:
        m = await message.answer("❌ Боты не чувствуют боли. Ищи живого противника!")
        asyncio.create_task(delete_delayed(m, 7))
        return

    args = message.text.split()
    if len(args) < 2:
        m = await message.answer("❌ Укажи ставку! Пример: <code>/duel 15</code>", parse_mode="HTML")
        asyncio.create_task(delete_delayed(m, 7))
        return

    # Получаем обоих игроков из базы
    challenger = await db.get_user(challenger_id, chat_id)
    target = await db.get_user(target_user_id, chat_id)
    
    if not challenger:
        m = await message.answer("❌ Сначала вырасти свой агрегат (/grow).")
        asyncio.create_task(delete_delayed(m, 7))
        return
    if not target:
        m = await message.answer("❌ Твой противник еще не играет в Лигу Писюнов.")
        asyncio.create_task(delete_delayed(m, 7))
        return

    bet_str = args[1].lower()
    if bet_str == "all":
        bet = challenger['size']
    elif bet_str.isdigit():
        bet = int(bet_str)
    else:
        m = await message.answer("❌ Ставка должна быть числом или словом 'all'.")
        asyncio.create_task(delete_delayed(m, 7))
        return

    if bet <= 0:
        m = await message.answer("❌ Ставка должна быть больше нуля!")
        asyncio.create_task(delete_delayed(m, 7))
        return

    if challenger['size'] < bet:
        m = await message.answer(f"❌ Не хватает см! Твой предел: <b>{challenger['size']} см</b>.", parse_mode="HTML")
        asyncio.create_task(delete_delayed(m, 7))
        return
    
    if target['size'] < bet:
        m = await message.answer(f"❌ У противника нет столько см! Его размер: <b>{target['size']} см</b>.", parse_mode="HTML")
        asyncio.create_task(delete_delayed(m, 7))
        return

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⚔️ Принять бой", callback_data=f"duel_yes_{challenger_id}_{target_user_id}_{bet}"),
            InlineKeyboardButton(text="🏃‍♂️ Сбежать", callback_data=f"duel_no_{challenger_id}_{target_user_id}_{bet}")
        ]
    ])

    target_name = message.reply_to_message.from_user.first_name
    challenger_name = message.from_user.first_name

    sent_msg = await message.answer(
        f"🥊 <b>ВЫЗОВ НА ДУЭЛЬ!</b> 🥊\n\n"
        f"👤 <b>{challenger_name}</b> ({challenger['size']} см) бросает вызов <b>{target_name}</b> ({target['size']} см)!\n"
        f"📏 Ставка: <b>{bet} см</b>\n\n"
        f"<i>⚠️ Размер влияет на шансы, но удача может всё изменить!</i>",
        reply_markup=kb,
        parse_mode="HTML"
    )
    # Если на дуэль не ответят за 2 минуты - она удалится сама
    asyncio.create_task(delete_delayed(sent_msg, 120))


@router.callback_query(F.data.startswith("duel_"))
async def process_duel_callback(callback: CallbackQuery):
    data = callback.data.split("_")
    action = data[1] # yes / no
    challenger_id = int(data[2])
    target_id = int(data[3])
    bet = int(data[4])
    chat_id = callback.message.chat.id

    if callback.from_user.id != target_id:
        return await callback.answer("❌ Эта перчатка брошена не тебе!", show_alert=True)

    if action == "no":
        await callback.message.edit_text(f"🐔 <b>{callback.from_user.first_name}</b> испугался и сбежал с дуэли.", parse_mode="HTML")
        asyncio.create_task(delete_delayed(callback.message, 15))
        return

    # Проверяем размеры еще раз (вдруг они успели сыграть /grow)
    challenger = await db.get_user(challenger_id, chat_id)
    target = await db.get_user(target_id, chat_id)

    if not challenger or challenger['size'] < bet or not target or target['size'] < bet:
        await callback.message.edit_text("❌ Дуэль отменена: у одного из бойцов изменился баланс.")
        asyncio.create_task(delete_delayed(callback.message, 10))
        return

    # Базовый шанс 50%. Максимальный сдвиг баланса +/- 20%
    diff = challenger['size'] - target['size']
    max_size = max(challenger['size'], target['size'])
    
    if max_size == 0:
        chance_offset = 0
    else:
        # Чем больше разница, тем ближе шанс к +20% или -20%
        chance_offset = (diff / max_size) * 0.20 

    challenger_chance = 0.50 + chance_offset
    
    # Кидаем кубик (от 0.0 до 1.0)
    roll = random.random()
    
    if roll <= challenger_chance:
        winner, loser = challenger, target
        winner_is_challenger = True
    else:
        winner, loser = target, challenger
        winner_is_challenger = False

    new_winner_size = winner['size'] + bet
    new_loser_size = loser['size'] - bet

    if abs(diff) < 20:
        flavor = "⚔️ <b>РАВНЫЙ БОЙ!</b> Битва шла на равных, но удача выбрала победителя!"
    elif (winner_is_challenger and chance_offset < -0.10) or (not winner_is_challenger and chance_offset > 0.10):
        flavor = "💥 <b>ЭПИЧНЫЙ АПСЕТ!</b> Давид сокрушил Голиафа! Маленький размер не приговор!"
    else:
        flavor = "🪨 <b>ИЗБИЕНИЕ МЛАДЕНЦА!</b> Гигант ожидаемо раздавил своего мелкого соперника."

    # Сохраняем результаты
    await db.update_user(winner['telegram_id'], chat_id, size=new_winner_size)
    await db.update_user(loser['telegram_id'], chat_id, size=new_loser_size)

    text = (
        f"🥊 <b>ДУЭЛЬ ЗАВЕРШЕНА!</b> 🥊\n\n"
        f"{flavor}\n\n"
        f"👑 <b>Победитель: {winner['first_name']}</b> (+{bet} см)\n"
        f"💀 <b>Проигравший: {loser['first_name']}</b> (-{bet} см)\n\n"
        f"📊 <b>Новые размеры:</b>\n"
        f"👉 {winner['first_name']}: <b>{new_winner_size} см</b>\n"
        f"👉 {loser['first_name']}: <b>{new_loser_size} см</b>\n\n"
        f"<i>⏳ Сообщение исчезнет через 20 секунд...</i>"
    )

    await callback.message.edit_text(text, parse_mode="HTML")
    # Удаляем сообщение с результатом боя через 20 секунд
    asyncio.create_task(delete_delayed(callback.message, 20))