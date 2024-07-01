from typing import Union

from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery


class ChatTypeFilter(BaseFilter):
    chat_type: Union[str, list]

    async def __call__(self, event: Union[Message, CallbackQuery]):
        if isinstance(event, Message):
            event = event.chat
        elif isinstance(event, CallbackQuery):
            event = event.message.chat

        if isinstance(self.chat_type, str):
            return event.type == self.chat_type
        else:
            return event.type in self.chat_type
