from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from database import db
from config import ADMIN_ID
import time
import random
import json

router = Router()

BOSS_COOLDOWN = 6 * 3600 # 6 часов между призывами босса
HIT_COOLDOWN = 5 * 60    # 5 минут между ударами

BOSS_NAMES = [
    "🦖 Писюнозавр Рекс",
    "🦍 Кинг-Донг",
    "👽 Инопланетный Заглот",
    "👾 Мутант-Кастратор",
    "✂️ Безумный Парикмахер",
    "🥒 Огуречный Потрошитель"
]

def generate_hp_bar(hp, max_hp, length=10):
    """Генерирует красивую полоску ХП из эмодзи"""
    if max_hp <= 0: return "💀"
    filled = int((hp / max_hp) * length)
    empty = length - filled
    return f"[{'🟥' * filled}{'⬛' * empty}]"

@router.message(Command("boss"))
async def cmd_boss(message: Message):
    if not await db.get_setting("module_boss"):
        return await message.answer("❌ Рейды на боссов временно отключены администратором.")

    chat_id = message.chat.id
    current_time = int(time.time())
    
    boss = await db.get_boss(chat_id)
    
    # 1. Если босс уже жив (ХП больше 0)
    if boss and boss['hp'] > 0:
        attackers = json.loads(boss['attackers'])
        sorted_attackers = sorted(attackers.items(), key=lambda x: x[1]['dmg'], reverse=True)
        top_text = ""
        for i, (uid, data) in enumerate(sorted_attackers[:5]):
            medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "⚔️"
            top_text += f"{medal} <b>{data['name']}</b>: {data['dmg']} урона\n"
            
        if not top_text:
            top_text = "<i>Пока никто не осмелился подойти...</i>"
            
        hp_bar = generate_hp_bar(boss['hp'], boss['max_hp'])
        
        text = (
            f"🚨 <b>В ЧАТЕ АКТИВЕН БОСС!</b> 🚨\n\n"
            f"😈 <b>{boss['name']}</b>\n"
            f"❤️ ХП: {hp_bar} <b>{boss['hp']} / {boss['max_hp']}</b>\n\n"
            f"📊 <b>Топ бойцов:</b>\n{top_text}\n"
            f"👉 Пиши <code>/hit</code>, чтобы вступить в бой!"
        )
        return await message.answer(text, parse_mode="HTML")

    # 2. Проверка таймера на призыв
    if boss and boss['last_summon']:
        remains = BOSS_COOLDOWN - (current_time - boss['last_summon'])
        if remains > 0:
            h = remains // 3600
            m = (remains % 3600) // 60
            return await message.answer(f"⏳ В чате пока тихо. Следующий монстр появится не раньше, чем через <b>{h} ч. {m} мин.</b>", parse_mode="HTML")

    name = random.choice(BOSS_NAMES)
    max_hp = random.randint(500, 2000)
    
    await db.summon_boss(chat_id, name, max_hp, max_hp, current_time)

    hp_bar = generate_hp_bar(max_hp, max_hp)
    
    text = (
        f"⚠️ <b>ВНИМАНИЕ! ТРЕВОГА!</b> ⚠️\n\n"
        f"В чат врывается <b>{name}</b>!\n"
        f"❤️ ХП: {hp_bar} <b>{max_hp}</b>\n\n"
        f"Хватайте свои агрегаты и бейте его командой <code>/hit</code> каждые 5 минут!\n"
        f"<i>Кто нанесет больше всего урона — получит главный приз (Стероиды)!</i>"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(Command("hit"))
async def cmd_hit(message: Message):
    if not await db.get_setting("module_boss"):
        return await message.answer("❌ Рейды на боссов временно отключены.")

    chat_id = message.chat.id
    user_id = message.from_user.id
    current_time = int(time.time())

    boss = await db.get_boss(chat_id)
    if not boss or boss['hp'] <= 0:
        return await message.answer("❌ В чате сейчас мирно. Вызови монстра командой /boss.")

    user = await db.get_user(user_id, chat_id)
    if not user or user['banned']:
        return await message.answer("❌ Сначала нужно вырастить свой агрегат через /grow!")

    # --- ПРОВЕРКА НА РЕЖИМ БОГА ---
    is_godmode = False
    if user_id == ADMIN_ID:
        is_godmode = await db.get_setting("admin_godmode", default=0)

    last_hit = user['last_hit'] if 'last_hit' in user.keys() else 0
    remains = HIT_COOLDOWN - (current_time - last_hit)
    
    # Обычные игроки ждут кулдаун, Бог - бьет когда захочет
    if remains > 0 and not is_godmode:
        m = remains // 60
        s = remains % 60
        return await message.answer(f"⏳ Восстановление сил. Следующий удар через <b>{m} мин. {s} сек.</b>", parse_mode="HTML")

    # Вешаем кулдаун на удар
    await db.update_user(user_id, chat_id, last_hit=current_time)

    # 1. АТАКА ИГРОКА
    base_max = max(30, int(user['size'] * 0.40))
    if base_max > 800: base_max = 800
    dmg = random.randint(10, base_max)

    roll = random.random()
    if roll < 0.10:
        dmg *= 2
        flavor = f"💥 <b>КРИТИЧЕСКИЙ УДАР!</b>\nПрямо в уязвимое место! Босс получает <b>{dmg} урона</b>!"
    elif roll < 0.20 and not is_godmode:
        # В Режиме Бога промахов не бывает!
        dmg = 0
        flavor = f"💨 <b>ПРОМАХ!</b>\nТы не рассчитал силы, и удар пришелся мимо."
    else:
        flavor = f"⚔️ <b>УДАР!</b>\nБосс получает <b>{dmg} урона</b>."

    # 2. КОНТРАТАКА БОССА
    boss_reply_text = ""
    new_user_size = user['size']

    # В Режиме Бога 100% уворот. У смертных - 30% шанс увернуться.
    if is_godmode or random.random() < 0.30:
        boss_reply_text = "🤸‍♂️ <i>Ты ловко увернулся от ответной атаки босса!</i>"
    else:
        # Урон босса: база + немного от его максимального ХП
        boss_base_dmg = random.randint(5, 20) + int(boss['max_hp'] * 0.005)

        if user['immune']:
            boss_reply_text = "🛡 <b>Босс ударил в ответ, но твой Щит поглотил урон!</b> (Щит сломан)"
            await db.update_user(user_id, chat_id, immune=False)
        else:
            if user['size'] <= 0:
                boss_reply_text = "💀 <i>Босс хотел ударить в ответ, но увидел твои 0 см и просто посмеялся...</i>"
            else:
                new_user_size = max(0, user['size'] - boss_base_dmg)
                actual_dmg = user['size'] - new_user_size
                await db.update_user(user_id, chat_id, size=new_user_size)

                boss_attacks = [
                    f"🩸 В ярости босс бьет в ответ и отрывает тебе <b>{actual_dmg} см</b>!",
                    f"🔥 Монстр контратакует! Опалено <b>{actual_dmg} см</b>.",
                    f"🦷 Босс делает резкий выпад и откусывает <b>{actual_dmg} см</b>!",
                    f"☄️ Мощный контрудар босса сплющивает твой агрегат на <b>{actual_dmg} см</b>!"
                ]
                boss_reply_text = random.choice(boss_attacks)

    # 3. НАНОСИМ УРОН БОССУ В БД
    if dmg > 0:
        new_hp = boss['hp'] - dmg
        attackers = json.loads(boss['attackers'])
        str_uid = str(user_id)
        
        if str_uid not in attackers:
            attackers[str_uid] = {"name": user['first_name'], "dmg": 0}
        attackers[str_uid]['dmg'] += dmg

        # ЕСЛИ БОСС УМЕР
        if new_hp <= 0:
            sorted_attackers = sorted(attackers.items(), key=lambda x: x[1]['dmg'], reverse=True)
            
            victory_text = (
                f"🎉 <b>БОСС ПОВЕРЖЕН!</b> 🎉\n"
                f"Монстр <b>{boss['name']}</b> не выдержал удара от <b>{user['first_name']}</b> и падает замертво!\n\n"
                f"📊 <b>ИТОГИ РЕЙДА:</b>\n"
            )

            for i, (uid_str, data) in enumerate(sorted_attackers):
                uid = int(uid_str)
                p_user = await db.get_user(uid, chat_id)
                if not p_user: continue
                
                reward_cm = max(2, int(data['dmg'] * 0.5))
                p_new_size = p_user['size'] + reward_cm
                
                medal = "⚔️"
                extra_prize = ""
                
                if i == 0:
                    medal = "👑"
                    extra_prize = " + ✖️2️⃣ Стероиды!"
                    await db.update_user(uid, chat_id, size=p_new_size, double_bonus=True)
                else:
                    await db.update_user(uid, chat_id, size=p_new_size)

                victory_text += f"{medal} <b>{data['name']}</b>: {data['dmg']} урона 👉 <b>+{reward_cm} см{extra_prize}</b>\n"

            await db.clear_boss(chat_id)
            return await message.answer(victory_text, parse_mode="HTML")

        await db.update_boss(chat_id, new_hp, json.dumps(attackers, ensure_ascii=False))
    else:
        new_hp = boss['hp'] # Если промахнулся

    # ВЫВОД РЕЗУЛЬТАТОВ БОЯ (Если босс выжил)
    hp_bar = generate_hp_bar(new_hp, boss['max_hp'])
    
    final_text = (
        f"{flavor}\n\n"
        f"========================\n"
        f"😈 <b>{boss['name']}</b>\n"
        f"{hp_bar} <b>{new_hp} / {boss['max_hp']}</b>\n"
        f"========================\n\n"
        f"{boss_reply_text}"
    )
    
    if new_user_size != user['size']:
        final_text += f"\n\n📏 Твой размер теперь: <b>{new_user_size} см</b>"

    await message.answer(final_text, parse_mode="HTML")