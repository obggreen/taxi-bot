from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery, WebAppInfo

from typing import Union

from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.models import User, UserType
from utils.yookassa.api import payment


class AdminFilter(BaseFilter):
    async def __call__(self, event: Union[Message, CallbackQuery], user: User) -> bool:
        if user:
            return user.role == UserType.admin


class BlockedFilter(BaseFilter):
    async def __call__(self, call: Union[Message, CallbackQuery], user: User) -> bool:
        if user and user.blocked_bot:
            markup = InlineKeyboardBuilder()

            payment_data = await payment(amount=500)
            url = payment_data.confirmation.confirmation_url

            markup.button(
                text='Купить разбан', web_app=WebAppInfo(url=url)
            )
            await call.answer("Ваш профиль заблокирован, что бы использовать бота, вы можете приобрести "
                              "<b>'Разблокировку'</>",
                              reply_markup=markup.as_markup()
                              )
            return False
        return True
