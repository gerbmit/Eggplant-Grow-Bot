from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from database import db
import asyncio

router = Router()

async def delete_delayed(msg: Message, delay: int):
    """Фоновая задача для удаления мусорных сообщений"""
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except Exception:
        pass

@router.message(Command("pay"))
async def cmd_pay(message: Message):
    # Проверяем, что это ответ на сообщение
    if not message.reply_to_message:
        msg = await message.answer(
            "❌ <b>Как передать сантиметры:</b>\n"
            "Ответь на сообщение получателя командой:\n"
            "<code>/pay 15</code> или <code>/pay all</code>",
            parse_mode="HTML"
        )
        asyncio.create_task(delete_delayed(msg, 7))
        return

    sender_id = message.from_user.id
    target_id = message.reply_to_message.from_user.id
    chat_id = message.chat.id

    if sender_id == target_id:
        msg = await message.answer("❌ Перекладывать из одного кармана в другой нет смысла. Выбери другого игрока!")
        asyncio.create_task(delete_delayed(msg, 7))
        return

    if message.reply_to_message.from_user.is_bot:
        msg = await message.answer("❌ Ботам не нужны твои сантиметры. Они состоят из нулей и единиц!")
        asyncio.create_task(delete_delayed(msg, 7))
        return

    args = message.text.split()
    if len(args) < 2:
        msg = await message.answer("❌ Укажи сумму перевода! Пример: <code>/pay 15</code>", parse_mode="HTML")
        asyncio.create_task(delete_delayed(msg, 7))
        return

    sender = await db.get_user(sender_id, chat_id)
    target = await db.get_user(target_id, chat_id)

    if not sender or sender['banned']:
        msg = await message.answer("❌ Сначала зарегистрируйся в игре (напиши /grow).")
        asyncio.create_task(delete_delayed(msg, 7))
        return
        
    if not target:
        msg = await message.answer(f"❌ <b>{message.reply_to_message.from_user.first_name}</b> еще не играет в Лигу Писюнов.", parse_mode="HTML")
        asyncio.create_task(delete_delayed(msg, 7))
        return

    amount_str = args[1].lower()
    if amount_str == "all":
        amount = sender['size']
    elif amount_str.isdigit():
        amount = int(amount_str)
    else:
        msg = await message.answer("❌ Сумма должна быть числом или словом 'all'.")
        asyncio.create_task(delete_delayed(msg, 7))
        return

    if amount <= 0:
        msg = await message.answer("❌ Сумма должна быть больше нуля!")
        asyncio.create_task(delete_delayed(msg, 7))
        return

    if sender['size'] < amount:
        msg = await message.answer(f"❌ Не хватает см! На твоем счету всего: <b>{sender['size']} см</b>.", parse_mode="HTML")
        asyncio.create_task(delete_delayed(msg, 7))
        return

    new_sender_size = sender['size'] - amount
    new_target_size = target['size'] + amount

    await db.update_user(sender_id, chat_id, size=new_sender_size)
    await db.update_user(target_id, chat_id, size=new_target_size)

    text = (
        f"💸 <b>УСПЕШНЫЙ ПЕРЕВОД!</b> 💸\n\n"
        f"👤 <b>{sender['first_name']}</b> благородно отрезает от себя и передает <b>{target['first_name']}</b> ровно <b>{amount} см</b>!\n\n"
        f"📊 <b>Новые размеры:</b>\n"
        f"👉 {sender['first_name']}: <b>{new_sender_size} см</b>\n"
        f"👉 {target['first_name']}: <b>{new_target_size} см</b>"
    )
    
    await message.answer(text, parse_mode="HTML")