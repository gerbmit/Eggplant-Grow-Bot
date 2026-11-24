from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from database import db
from config import ADMIN_ID
import time
import random

router = Router()

# Кулдаун на кражу (Снижено с 6 до 2 часов!)
STEAL_COOLDOWN = 2 * 60 * 60  

# Лимиты
MIN_SIZE_TO_STEAL = 30 # Минимум см у вора и у жертвы, чтобы можно было воровать

SUCCESS_MESSAGES = [
    "🥷 <b>Бесшумный вор!</b> Ловкий маневр, и у <b>{target}</b> пропадает <b>{amount} см</b>. Теперь они твои!",
    "✂️ <b>Чик-чик!</b> Пропажа <b>{amount} см</b> прошла незаметно для <b>{target}</b>. Отличный улов!",
    "😎 <b>Идеальное ограбление!</b> Удается развести <b>{target}</b> на <b>{amount} см</b>.",
    "🏴‍☠️ <b>Пиратская доля!</b> Успешный абордаж! В карман отправляется <b>{amount} см</b>, украденные у <b>{target}</b>.",
    "🎩 <b>Иллюзионист!</b> Фокус с монеткой отвлекает <b>{target}</b>, и <b>{amount} см</b> меняют владельца.",
    "🏃‍♂️ <b>Гоп-стоп!</b> Успешный наезд на <b>{target}</b>, отжато <b>{amount} см</b>.",
    "🧲 <b>Магнитная аномалия!</b> Каким-то чудом удается примагнитить к себе <b>{amount} см</b> от <b>{target}</b>.",
    "🧛‍♂️ <b>Ночной кровосос!</b> Из <b>{target}</b> успешно высасывается <b>{amount} см</b> жизненной энергии.",
    "💼 <b>Рейдерский захват!</b> Юристы доказали, что <b>{amount} см</b> имущества <b>{target}</b> должны принадлежать тебе.",
    "🪚 <b>Техасская резня!</b> Жестко, но эффективно: у <b>{target}</b> отпиливается <b>{amount} см</b>."
]

FAIL_MESSAGES = [
    "🚨 <b>Сработала сигналка!</b> Кража не удалась, поимка с поличным! В наказание <b>{target}</b> получает <b>{amount} см</b> компенсации.",
    "🐕 <b>Злая собака!</b> При попытке ограбить <b>{target}</b>, сторожевой пес откусывает <b>{amount} см</b>. Трофей достается противнику!",
    "💥 <b>Эпичный провал!</b> Улов падает на пол, и <b>{target}</b> с радостью подбирает эти <b>{amount} см</b>.",
    "🥊 <b>Жесткий отпор!</b> <b>{target}</b> дает мощный отпор. Приходится извиняться и платить штраф: <b>{amount} см</b>.",
    "🤡 <b>Позорище!</b> Громкий чих в самый ответственный момент. <b>{target}</b> смеется и забирает <b>{amount} см</b> за моральный ущерб.",
    "👮‍♂️ <b>Полиция нравов!</b> Задержание при попытке кражи. Суд постановил выплатить в пользу <b>{target}</b> компенсацию: <b>{amount} см</b>.",
    "🪤 <b>Ловушка Джокера!</b> В штанах у <b>{target}</b> был спрятан капкан. Потеряно <b>{amount} см</b>.",
    "🕊 <b>Карма в действии!</b> Птичка гадит на голову, секундное отвлечение, и <b>{target}</b> ловко срезает <b>{amount} см</b>.",
    "🧱 <b>Головой об стену!</b> Встреча со столбом при побеге от <b>{target}</b>. От удара отваливается <b>{amount} см</b>.",
    "🤺 <b>Не на того напал!</b> У <b>{target}</b> оказался джедайский меч, которым отсекается <b>{amount} см</b>."
]

@router.message(Command("steal"))
async def cmd_steal(message: Message):
    # ПРЕДОХРАНИТЕЛЬ: Проверяем, включены ли кражи в админ-панели
    if not await db.get_setting("module_steal"):
        return await message.answer("❌ Кражи временно отключены администратором.")

    # 1. Проверяем, что команда отправлена реплаем (в ответ на чье-то сообщение)
    if not message.reply_to_message:
        return await message.answer(
            "❌ <b>Как грабить:</b>\n"
            "Ответь на сообщение человека, которого хочешь ограбить, командой <code>/steal</code>", 
            parse_mode="HTML"
        )

    target_user_id = message.reply_to_message.from_user.id
    target_name = message.reply_to_message.from_user.first_name
    thief_id = message.from_user.id
    chat_id = message.chat.id

    if target_user_id == thief_id:
        return await message.answer("❌ Пытаешься украсть сам у себя? Забавно, но нет.")

    if message.reply_to_message.from_user.is_bot:
        return await message.answer("❌ У ботов ничего нет. Отстань от железяки!")

    # 2. Получаем обоих юзеров из базы
    thief = await db.get_user(thief_id, chat_id)
    target = await db.get_user(target_user_id, chat_id)

    if not thief:
        return await message.answer("❌ Сначала зарегистрируйся (напиши /grow).")
    if thief['banned']:
        return
    if not target:
        return await message.answer(f"❌ <b>{target_name}</b> еще не играет в Лигу Писюнов.")

    current_time = int(time.time())
    
    # --- ПРОВЕРКА НА РЕЖИМ БОГА ---
    is_godmode = False
    if thief_id == ADMIN_ID:
        is_godmode = await db.get_setting("admin_godmode", default=0)
    
    # 3. Проверяем кулдаун вора (Только для смертных)
    if not is_godmode:
        if current_time - thief['last_steal'] < STEAL_COOLDOWN:
            remains = STEAL_COOLDOWN - (current_time - thief['last_steal'])
            hours = remains // 3600
            minutes = (remains % 3600) // 60
            return await message.answer(f"⏳ Полиция еще ищет тебя. Залечь на дно придется еще <b>{hours} ч. {minutes} мин.</b>", parse_mode="HTML")

    # 4. Проверяем минимальные требования (Только для смертных)
    if not is_godmode:
        if thief['size'] < MIN_SIZE_TO_STEAL:
            return await message.answer(f"❌ Твой размер всего {thief['size']} см. Куда ты лезешь грабить? Вырасти хотя бы до {MIN_SIZE_TO_STEAL} см!")
            
        if target['size'] < MIN_SIZE_TO_STEAL:
            return await message.answer(f"❌ У <b>{target_name}</b> размер меньше {MIN_SIZE_TO_STEAL} см. Не трогай новичка, имей совесть!", parse_mode="HTML")

    # Обновляем таймер кражи сразу, чтобы нельзя было спамить
    await db.update_user(thief_id, chat_id, last_steal=current_time)

    # 🛑 ЛОГИКА КАПКАНА 🛑
    try:
        has_trap = target['has_trap']
    except (IndexError, KeyError):
        has_trap = False

    if has_trap:
        if is_godmode:
            # Режим Бога просто ломает капкан в пыль и игнорирует его
            await db.update_user(target_user_id, chat_id, has_trap=False)
        else:
            # Смертный вор лишается 30 см (или падает до 0), а капкан ломается
            new_thief_size = max(0, thief['size'] - 30)
            await db.update_user(thief_id, chat_id, size=new_thief_size)
            await db.update_user(target_user_id, chat_id, has_trap=False)
            
            return await message.answer(
                f"🚨 <b>КРАЖА ПРОВАЛЕНА!</b>\n\n"
                f"🪤 В штанах у <b>{target_name}</b> был спрятан <b>КАПКАН</b>!\n"
                f"Вор <b>{thief['first_name']}</b> сунул туда руку и с криком лишился <b>30 см</b>!\n\n"
                f"<i>(Капкан жертвы сломан)</i>\n"
                f"👉 Размер вора теперь: <b>{new_thief_size} см</b>",
                parse_mode="HTML"
            )

    # Логика кражи: сколько пытаемся украсть (от 5 до 20 см, но не больше 15% от жертвы)
    max_possible_steal = int(target['size'] * 0.15)
    if max_possible_steal < 5:
        max_possible_steal = 5
        
    steal_amount = random.randint(5, min(20, max_possible_steal))
    
    # Чтобы вор не обанкротился в минус при штрафе
    if steal_amount > thief['size']:
        steal_amount = thief['size']

    if is_godmode:
        # Режим Бога дает 100% успех без палева
        is_success = True
    else:
        # 5. КИДАЕМ КУБИК (Шанс на успех 60%)
        is_success = random.random() < 0.60

    if is_success:
        # Вор победил: забирает у жертвы
        new_thief_size = thief['size'] + steal_amount
        new_target_size = target['size'] - steal_amount
        
        await db.update_user(thief_id, chat_id, size=new_thief_size)
        await db.update_user(target_user_id, chat_id, size=new_target_size)
        
        # Обычное сообщение для всех, включая админа! Никто ничего не заподозрит.
        msg = random.choice(SUCCESS_MESSAGES).format(target=target_name, amount=steal_amount)
        text = f"{msg}\n\n👉 Твой новый размер: <b>{new_thief_size} см</b>"
        
    else:
        # Вор спалился: отдает свои см жертве (компенсация) - Только для смертных, Бог не может проиграть
        new_thief_size = thief['size'] - steal_amount
        new_target_size = target['size'] + steal_amount
        
        await db.update_user(thief_id, chat_id, size=new_thief_size)
        await db.update_user(target_user_id, chat_id, size=new_target_size)
        
        msg = random.choice(FAIL_MESSAGES).format(target=target_name, amount=steal_amount)
        text = f"{msg}\n\n👉 Твой новый размер: <b>{new_thief_size} см</b>"

    await message.answer(text, parse_mode="HTML")