from typing import Union

from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import Tariff
from database.models import User
from handlers.routers import user_router


@user_router.message(F.text == '📊 Подписка')
async def check_tariff_plan(event: Union[Message, CallbackQuery], state: FSMContext, user: User):
    if isinstance(event, Message):
        answer = event.answer
    else:
        await event.message.delete()
        answer = event.message.answer


    if user.subscription is None:
        markup = InlineKeyboardBuilder()
        markup.button(
            text='🛒 Список тарифов', callback_data='tariff'
        )
        await answer(
            'У вас нет активных подписок. Перейти к покупке?',
            reply_markup=markup.as_markup()
        )
    else:
        tariff = await Tariff.find_one(
            Tariff.id == user.subscription
        )
        await answer(
            f'<b>Информация о вашей подписки:</>\n\n'
            f'└ Название тарифа: {tariff.name}\n'
            f'└ Количество дней: {tariff.count_days}\n'
            f'└ Ссылка для вступления в группу: ....'
        )