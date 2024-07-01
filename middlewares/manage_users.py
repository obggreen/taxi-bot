import uuid
from datetime import datetime

from typing import Callable, Dict, Any, Awaitable, Union

from aiogram import BaseMiddleware, Bot
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import Link
from database.models import User


async def check_referral_user(event):
    referral, link = None, None
    if isinstance(event, Message):
        if event.chat.type == 'private':
            if event.text:
                if event.text.startswith('/start ref'):
                    ref_code = event.text.split()[1].replace('ref', '')
                    referral_user = await User.find_one(User.identity == ref_code)
                    if referral_user:
                        referral = referral_user.id
                if event.text.startswith('/start link'):
                    link_code = event.text.split()[1].replace('link', '')
                    link = await Link.find_one(Link.short_link == link_code)
                    if link:
                        link = link.id

    return referral, link


async def create_update_user(event, user_id):
    user = await User.find_one(User.user_id == user_id)
    if not user:
        referral, link = await check_referral_user(event)
        user = User(
            identity=uuid.uuid4().hex[:12],
            referral_id=referral,
            link_id=link,
            user_id=user_id,
            full_name=event.from_user.full_name,
            username=event.from_user.username,
            last_active=datetime.utcnow().date()
        )
        await user.insert()
    else:
        update_fields = {}
        if user.username != event.from_user.username:
            update_fields['username'] = event.from_user.username
        if user.full_name != event.from_user.full_name:
            update_fields['full_name'] = event.from_user.full_name

        if update_fields:
            await user.update({"$set": update_fields})

    return user


# async def send_verification_reminder(bot: Bot, user: User):
#     try:
#         markup = InlineKeyboardBuilder()
#         markup.button(
#             text='Пройти верификацию', callback_data='passr'
#         )
#         file = FSInputFile('files/info.png')
#         await bot.send_photo(
#             chat_id=user.user_id,
#             photo=file,
#             caption='<b>Важная информация для вас!</>\n\n'
#                     'Вам необходимо пройти верификацию для подтверждения своей личности.\n'
#                     'Для прохождения у вас есть 30 дней, после этого вы будете отключены от сервиса.\n'
#                     'Пройти верификацию можно по кнопке ниже.',
#             reply_markup=markup.as_markup()
#         )
#     except Exception as e:
#         print(f"Failed to send verification reminder: {e}")


class ManageUserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Union[Message, CallbackQuery], Dict[str, Any]], Awaitable[Any]],
        event: Union[Message, CallbackQuery],
        data: Dict[str, Any]
    ) -> Any:
        if getattr(event, 'from_user', None) and event.from_user.is_bot:
            return await handler(event, data)

        user_id = event.from_user.id
        user = await create_update_user(event, user_id)
        data["user"] = user

        # if user.documents == 'untested':
        #     bot = data.get('bot')
        #     if bot:
        #         await send_verification_reminder(bot, user)

        return await handler(event, data)


