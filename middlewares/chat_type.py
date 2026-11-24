from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message
from config import ADMIN_ID

class GroupOnlyMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        # Если чат личный (private), отправляем заглушку и прерываем обработку
        if event.chat.type == "private":
            # ИСКЛЮЧЕНИЕ: Админу можно писать в личку, чтобы делать рассылку!
            if event.from_user.id == ADMIN_ID:
                return await handler(event, data)
                
            await event.answer("Бот выполняет свою миссию только в групповых чатах!")
            return 
            
        # Если это группа, пропускаем сообщение дальше
        return await handler(event, data)