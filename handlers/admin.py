from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from utils.filters import IsAdmin
from database import db
import aiosqlite
import asyncio
from config import ADMIN_ID

router = Router()
router.message.filter(IsAdmin())

class BroadcastState(StatesGroup):
    text = State()

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    text = (
        "🛠 <b>Админ-панель</b>\n\n"
        "/broadcast - Рассылка по группам\n"
        "/give [id] [см] - Выдать см\n"
        "/take [id] [см] - Забрать см\n"
        "/givebuff [id] [щит/х2] - Выдать бафф\n"
        "/curse [id] - ⚡️ Проклясть (-100 см в /grow)\n"
        "/godmode - 👑 Вкл/Выкл Режим Бога (кражи без правил)\n"
        "/reset [id] - Обнулить игрока\n"
        "/botstats - Статистика бота\n"
        "/ban [id] - Забанить\n"
        "/unban [id] - Разбанить\n"
        "/bandrop [id] - 🚫 Запретить дропы (Глобально)\n"
        "/unbandrop [id] - ✅ Разрешить дропы (Глобально)\n"
        "/modules - ⚙️ Вкл/Выкл игры"
    )
    await message.answer(text, parse_mode="HTML")

async def get_modules_kb():
    modules = [
        ("🎰 Казино", "module_casino"),
        ("🥊 Дуэли", "module_duel"),
        ("🦖 Боссы", "module_boss"),
        ("🥷 Кражи", "module_steal"),
        ("🎁 Аирдропы", "module_airdrop"),
        ("🎁 Сундуки", "module_bonus") 
    ]
    
    kb_builder = []
    for name, key in modules:
        is_enabled = await db.get_setting(key)
        status = "🟢 Вкл" if is_enabled else "🔴 Выкл"
        kb_builder.append([InlineKeyboardButton(text=f"{name}: {status}", callback_data=f"toggle_{key}")])
        
    return InlineKeyboardMarkup(inline_keyboard=kb_builder)

@router.message(Command("modules"))
async def cmd_modules(message: Message):
    kb = await get_modules_kb()
    await message.answer(
        "⚙️ <b>Управление играми:</b>\n"
        "<i>Здесь можно глобально отключить любую мини-игру.</i>\n"
        "⚠️ <b>(Кнопки реагируют только на админа)</b>", 
        reply_markup=kb, 
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("toggle_module_"))
async def process_toggle_module(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return await callback.answer("❌ Руки убрал! Это админская кнопка.", show_alert=True)
        
    key = callback.data.replace("toggle_", "")
    current_status = await db.get_setting(key)
    new_status = 0 if current_status else 1
    
    await db.set_setting(key, new_status)
    
    kb = await get_modules_kb()
    await callback.message.edit_reply_markup(reply_markup=kb)
    await callback.answer("✅ Статус модуля изменен!")

@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, state: FSMContext):
    await message.answer("Отправьте сообщение для рассылки ПО ГРУППАМ (можно текст, фото или видео):")
    await state.set_state(BroadcastState.text)

@router.message(BroadcastState.text)
async def process_broadcast(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    
    chats = await db.get_all_unique_chats()
    if not chats:
        return await message.answer("❌ В базе нет ни одной группы!")

    count = 0
    await message.answer(f"🚀 Рассылка началась по {len(chats)} группам...")
    
    for chat_id in chats:
        try:
            await message.copy_to(chat_id)
            count += 1
            await asyncio.sleep(0.05)
        except Exception:
            continue
            
    await message.answer(f"✅ Рассылка завершена! Успешно доставлено в {count} групп(ы).")

@router.message(Command("give"))
async def cmd_give(message: Message):
    args = message.text.split()
    if len(args) != 3: 
        return await message.answer("Формат: <code>/give [id] [см]</code>", parse_mode="HTML")
    try:
        user_id = int(args[1])
        amount = abs(int(args[2])) 
    except ValueError:
        return await message.answer("❌ ID и количество см должны быть числами!")

    user = await db.get_user(user_id, message.chat.id)
    if user:
        new_size = user['size'] + amount
        await db.update_user(user_id, message.chat.id, size=new_size)
        await message.answer(f"✅ Успешно! Ты накинул <b>{amount} см</b> игроку <b>{user['first_name']}</b>.\n📏 Теперь у него: <b>{new_size} см</b>.", parse_mode="HTML")
    else:
        await message.answer("❌ Пользователь не найден в этом чате.")

@router.message(Command("take"))
async def cmd_take(message: Message):
    args = message.text.split()
    if len(args) != 3: 
        return await message.answer("Формат: <code>/take [id] [см]</code>", parse_mode="HTML")
    try:
        user_id = int(args[1])
        amount = abs(int(args[2]))
    except ValueError:
        return await message.answer("❌ ID и количество см должны быть числами!")

    user = await db.get_user(user_id, message.chat.id)
    if user:
        new_size = max(0, user['size'] - amount)
        await db.update_user(user_id, message.chat.id, size=new_size)
        await message.answer(f"✅ Успешно! Ты отрезал <b>{amount} см</b> у игрока <b>{user['first_name']}</b>.\n📏 Теперь у него: <b>{new_size} см</b>.", parse_mode="HTML")
    else:
        await message.answer("❌ Пользователь не найден в этом чате.")

@router.message(Command("ban"))
async def cmd_ban(message: Message):
    args = message.text.split()
    if len(args) != 2: 
        return await message.answer("Формат: <code>/ban [id]</code>", parse_mode="HTML")
    try:
        user_id = int(args[1])
    except ValueError:
        return await message.answer("❌ ID должен быть числом!")
        
    user = await db.get_user(user_id, message.chat.id)
    if user:
        await db.update_user(user_id, message.chat.id, banned=True)
        await message.answer(f"🛑 Игрок <b>{user['first_name']}</b> забанен в этом чате.", parse_mode="HTML")
    else:
        await message.answer("❌ Пользователь не найден в этом чате.")

@router.message(Command("unban"))
async def cmd_unban(message: Message):
    args = message.text.split()
    if len(args) != 2: 
        return await message.answer("Формат: <code>/unban [id]</code>", parse_mode="HTML")
    try:
        user_id = int(args[1])
    except ValueError:
        return await message.answer("❌ ID должен быть числом!")

    user = await db.get_user(user_id, message.chat.id)
    if user:
        await db.update_user(user_id, message.chat.id, banned=False)
        await message.answer(f"✅ Игрок <b>{user['first_name']}</b> разбанен в этом чате.", parse_mode="HTML")
    else:
        await message.answer("❌ Пользователь не найден в этом чате.")

@router.message(Command("bandrop"))
async def cmd_bandrop(message: Message):
    args = message.text.split()
    if len(args) != 2: 
        return await message.answer("Формат: <code>/bandrop [id]</code>", parse_mode="HTML")
    try:
        user_id = int(args[1])
    except ValueError:
        return await message.answer("❌ ID должен быть числом!")

    # Обновляем напрямую через базу, чтобы работало из личных сообщений (глобально)
    async with aiosqlite.connect(db.path) as conn:
        await conn.execute("UPDATE users SET airdrop_banned = 1 WHERE telegram_id = ?", (user_id,))
        await conn.commit()
        
    await message.answer(f"🚫 Игрок с ID <b>{user_id}</b> теперь не сможет поднимать аирдропы ни в одном чате.\n<i>(Сработано скрытно)</i>", parse_mode="HTML")

@router.message(Command("unbandrop"))
async def cmd_unbandrop(message: Message):
    args = message.text.split()
    if len(args) != 2: 
        return await message.answer("Формат: <code>/unbandrop [id]</code>", parse_mode="HTML")
    try:
        user_id = int(args[1])
    except ValueError:
        return await message.answer("❌ ID должен быть числом!")

    async with aiosqlite.connect(db.path) as conn:
        await conn.execute("UPDATE users SET airdrop_banned = 0 WHERE telegram_id = ?", (user_id,))
        await conn.commit()
        
    await message.answer(f"✅ Игроку с ID <b>{user_id}</b> снова разрешено брать аирдропы.", parse_mode="HTML")

@router.message(Command("givebuff"))
async def cmd_givebuff(message: Message):
    args = message.text.split()
    if len(args) != 3: 
        return await message.answer("Формат: <code>/givebuff [id] [щит/х2]</code>", parse_mode="HTML")
    try:
        user_id = int(args[1])
    except ValueError:
        return await message.answer("❌ ID должен быть числом!")

    buff_type = args[2].lower()
    user = await db.get_user(user_id, message.chat.id)
    if not user:
        return await message.answer("❌ Пользователь не найден в этом чате.")

    if buff_type in ["щит", "shield", "immune"]:
        await db.update_user(user_id, message.chat.id, immune=True)
        await message.answer(f"🛡 Админ выдал <b>Иммунитет (Щит)</b> игроку <b>{user['first_name']}</b>!", parse_mode="HTML")
    elif buff_type in ["х2", "x2", "double"]:
        await db.update_user(user_id, message.chat.id, double_bonus=True)
        await message.answer(f"✖️2️⃣ Админ выдал <b>Стероиды (Х2)</b> игроку <b>{user['first_name']}</b>!", parse_mode="HTML")
    else:
        await message.answer("❌ Неизвестный бафф. Используй 'щит' или 'х2'.")

@router.message(Command("curse"))
async def cmd_curse(message: Message):
    args = message.text.split()
    if len(args) != 2: 
        return await message.answer("Формат: <code>/curse [id]</code>\n<i>Накладывает проклятие на следующий /grow (-100 см)</i>", parse_mode="HTML")
    try:
        user_id = int(args[1])
    except ValueError:
        return await message.answer("❌ ID должен быть числом!")

    # Обновляем напрямую через базу, чтобы работало из личных сообщений (глобально)
    async with aiosqlite.connect(db.path) as conn:
        await conn.execute("UPDATE users SET cursed = 1 WHERE telegram_id = ?", (user_id,))
        await conn.commit()
        
    await message.answer(f"⛈ <b>ПРОКЛЯТИЕ НАЛОЖЕНО!</b>\nИгрок с ID <b>{user_id}</b> проклят глобально. При следующей попытке роста (в любом чате) его агрегат почернеет и отвалится на 100 см!\n<i>(Сработано скрытно)</i>", parse_mode="HTML")

@router.message(Command("godmode"))
async def cmd_godmode(message: Message):
    current_status = await db.get_setting("admin_godmode", default=0)
    new_status = 0 if current_status else 1
    
    await db.set_setting("admin_godmode", new_status)
    
    if new_status:
        await message.answer("👑 <b>РЕЖИМ БОГА ВКЛЮЧЕН!</b>\nТеперь ты можешь воровать без задержек, ломать капканы, и каждая твоя кража забирает 50% размера жертвы с 100% успехом!", parse_mode="HTML")
    else:
        await message.answer("👤 <b>Режим Бога выключен.</b>\nАдмин снова стал простым смертным и подчиняется правилам.", parse_mode="HTML")

@router.message(Command("reset"))
async def cmd_reset(message: Message):
    args = message.text.split()
    if len(args) != 2: 
        return await message.answer("Формат: <code>/reset [id]</code>", parse_mode="HTML")
    try:
        user_id = int(args[1])
    except ValueError:
        return await message.answer("❌ ID должен быть числом!")
        
    user = await db.get_user(user_id, message.chat.id)
    if user:
        await db.update_user(
            user_id, message.chat.id, 
            size=0, attempts=0, immune=False, 
            double_bonus=False, cursed=False, achievements='[]'
        )
        await message.answer(f"💀 <b>ПОЛНОЕ ОБНУЛЕНИЕ!</b>\nИгрок <b>{user['first_name']}</b> был сброшен до заводских настроек.", parse_mode="HTML")
    else:
        await message.answer("❌ Пользователь не найден в этом чате.")

@router.message(Command("botstats"))
async def cmd_botstats(message: Message):
    stats = await db.get_global_stats()
    if stats:
        total_chats = stats['total_chats'] or 0
        total_users = stats['total_users'] or 0
        total_size = stats['total_size'] or 0
        
        await message.answer(
            f"📊 <b>ГЛОБАЛЬНАЯ СТАТИСТИКА БОТА</b>\n\n"
            f"🌍 Всего групп: <b>{total_chats}</b>\n"
            f"👥 Всего игроков: <b>{total_users}</b>\n"
            f"🍆 Общий размер всех писюнов: <b>{total_size} см</b>",
            parse_mode="HTML"
        )
    else:
        await message.answer("❌ Ошибка получения статистики.")