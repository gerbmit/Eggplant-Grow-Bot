import aiosqlite
import json
import os
from config import DB_PATH

class Database:
    def __init__(self):
        self.path = DB_PATH
        os.makedirs(os.path.dirname(self.path), exist_ok=True)

    async def init_db(self):
        async with aiosqlite.connect(self.path) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    telegram_id INTEGER,
                    chat_id INTEGER,
                    username TEXT,
                    first_name TEXT,
                    size INTEGER DEFAULT 0,
                    attempts INTEGER DEFAULT 0,
                    last_grow INTEGER DEFAULT 0,
                    last_bonus INTEGER DEFAULT 0,
                    last_steal INTEGER DEFAULT 0,
                    last_hit INTEGER DEFAULT 0,
                    created_at INTEGER,
                    immune BOOLEAN DEFAULT 0,
                    double_bonus BOOLEAN DEFAULT 0,
                    banned BOOLEAN DEFAULT 0,
                    has_trap BOOLEAN DEFAULT 0,
                    cursed BOOLEAN DEFAULT 0,
                    airdrop_banned BOOLEAN DEFAULT 0,
                    achievements TEXT DEFAULT '[]',
                    PRIMARY KEY (telegram_id, chat_id)
                )
            ''')
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS bosses (
                    chat_id INTEGER PRIMARY KEY,
                    name TEXT,
                    hp INTEGER,
                    max_hp INTEGER,
                    attackers TEXT DEFAULT '{}',
                    last_summon INTEGER DEFAULT 0
                )
            ''')
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    name TEXT PRIMARY KEY,
                    value INTEGER DEFAULT 1
                )
            ''')
                
            try:
                await db.execute("ALTER TABLE users ADD COLUMN last_steal INTEGER DEFAULT 0")
            except: pass
                
            try:
                await db.execute("ALTER TABLE users ADD COLUMN last_hit INTEGER DEFAULT 0")
            except: pass

            try:
                await db.execute("ALTER TABLE users ADD COLUMN has_trap BOOLEAN DEFAULT 0")
            except: pass
            
            try:
                await db.execute("ALTER TABLE users ADD COLUMN cursed BOOLEAN DEFAULT 0")
            except: pass
                
            try:
                await db.execute("ALTER TABLE users ADD COLUMN airdrop_banned BOOLEAN DEFAULT 0")
            except: pass

            await db.commit()

    async def get_all_unique_users(self):
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute("SELECT DISTINCT telegram_id FROM users WHERE banned = 0")
            return [row[0] for row in await cursor.fetchall()]

    async def get_all_unique_chats(self):
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute("SELECT DISTINCT chat_id FROM users")
            return [row[0] for row in await cursor.fetchall()]

    async def get_all_users_in_chat(self, chat_id: int):
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute("SELECT telegram_id FROM users WHERE chat_id = ? AND banned = 0", (chat_id,))
            return [row[0] for row in await cursor.fetchall()]

    async def get_user(self, telegram_id: int, chat_id: int):
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM users WHERE telegram_id = ? AND chat_id = ?", (telegram_id, chat_id))
            return await cursor.fetchone()

    async def add_user(self, telegram_id: int, chat_id: int, username: str, first_name: str, created_at: int):
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "INSERT OR IGNORE INTO users (telegram_id, chat_id, username, first_name, created_at) VALUES (?, ?, ?, ?, ?)",
                (telegram_id, chat_id, username, first_name, created_at)
            )
            await db.commit()

    async def update_user(self, telegram_id: int, chat_id: int, **kwargs):
        if not kwargs:
            return
        columns = ", ".join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values())
        values.extend([telegram_id, chat_id])
        async with aiosqlite.connect(self.path) as db:
            await db.execute(f"UPDATE users SET {columns} WHERE telegram_id = ? AND chat_id = ?", values)
            await db.commit()

    async def get_top(self, chat_id: int, limit: int = 10):
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM users WHERE chat_id = ? AND banned = 0 ORDER BY size DESC LIMIT ?", (chat_id, limit))
            return await cursor.fetchall()

    async def get_global_top(self, limit: int = 10):
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute('''
                SELECT first_name, MAX(size) as max_size 
                FROM users 
                WHERE banned = 0 
                GROUP BY telegram_id 
                ORDER BY max_size DESC 
                LIMIT ?
            ''', (limit,))
            return await cursor.fetchall()

    async def get_rank(self, telegram_id: int, chat_id: int):
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute("SELECT COUNT(*) FROM users WHERE size > (SELECT size FROM users WHERE telegram_id = ? AND chat_id = ?) AND chat_id = ? AND banned = 0", (telegram_id, chat_id, chat_id))
            rank = await cursor.fetchone()
            return rank[0] + 1 if rank else 0

    async def get_stats(self, chat_id: int):
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT COUNT(*) as total, AVG(size) as avg_size, MAX(size) as max_size, MIN(size) as min_size FROM users WHERE chat_id = ? AND banned = 0", (chat_id,))
            return await cursor.fetchone()

    async def get_global_stats(self):
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT COUNT(DISTINCT chat_id) as total_chats, COUNT(DISTINCT telegram_id) as total_users, SUM(size) as total_size FROM users WHERE banned = 0")
            return await cursor.fetchone()

    async def get_boss(self, chat_id: int):
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM bosses WHERE chat_id = ?", (chat_id,))
            return await cursor.fetchone()

    async def summon_boss(self, chat_id: int, name: str, hp: int, max_hp: int, last_summon: int):
        async with aiosqlite.connect(self.path) as db:
            await db.execute('''
                INSERT INTO bosses (chat_id, name, hp, max_hp, attackers, last_summon)
                VALUES (?, ?, ?, ?, '{}', ?)
                ON CONFLICT(chat_id) DO UPDATE SET
                name=excluded.name, hp=excluded.hp, max_hp=excluded.max_hp, 
                attackers=excluded.attackers, last_summon=excluded.last_summon
            ''', (chat_id, name, hp, max_hp, last_summon))
            await db.commit()

    async def update_boss(self, chat_id: int, hp: int, attackers: str):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("UPDATE bosses SET hp = ?, attackers = ? WHERE chat_id = ?", (hp, attackers, chat_id))
            await db.commit()
            
    async def clear_boss(self, chat_id: int):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("UPDATE bosses SET hp = 0, attackers = '{}' WHERE chat_id = ?", (chat_id,))
            await db.commit()

    async def get_setting(self, name: str, default: int = 1) -> int:
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute("SELECT value FROM settings WHERE name = ?", (name,))
            row = await cursor.fetchone()
            return row[0] if row is not None else default

    async def set_setting(self, name: str, value: int):
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "INSERT INTO settings (name, value) VALUES (?, ?) ON CONFLICT(name) DO UPDATE SET value=excluded.value", 
                (name, value)
            )
            await db.commit()

db = Database()