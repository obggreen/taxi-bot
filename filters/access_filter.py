from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery, WebAppInfo

from typing import Union

from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import Order
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

            payment_data = await payment(amount=3000)
            url = payment_data.confirmation.confirmation_url

            await Order(
                user=user.id,
                identy=payment_data.id,
                amount=3000,
                type='block'
            ).insert()

            markup.button(
                text='Оплатить штраф (3000₽)', web_app=WebAppInfo(url=url)
            )
            await call.answer("Ваш профиль был заблокирован в группе Свободные Заказы | "
                              "Межгород за нарушение правил группы на пожизненный срок, что бы "
                              "снова получать заказы оплатите штраф.",
                              reply_markup=markup.as_markup()
                              )
            return False
        return True


# class GeolocationFilter(BaseFilter):
#     async def __call__(self, call: Union[Message, CallbackQuery], user: User) -> bool:
#         if not user.geo_message_id:
#             markup = InlineKeyboardBuilder()
#
#             markup.button(
#                 text='Поделиться геопозицией',
#                 callback_data='accept_geolocation'
#             )
#
#             await call.answer(
#                 'Для получения приоритетных заказов, вы можете поделиться геопозицией, тогда операторы будут видеть '
#                 'ваше местоположение и смогут дать вам выгодные заказы',
#                 reply_markup=markup.as_markup()
#             )
#             return False
#         return True
