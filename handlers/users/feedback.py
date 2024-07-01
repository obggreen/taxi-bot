from typing import Union

from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from database.models import User
from handlers.routers import user_router
from helpers.keyboards.markups import custom_back_markup


@user_router.message(F.text == '📨 Обратная связь')
async def check_tariff_plan(event: Union[Message, CallbackQuery], state: FSMContext, user: User):
    if isinstance(event, Message):
        answer = event.answer
    else:
        await event.message.delete()
        answer = event.message.answer

    await answer(
        'Задайте ваш вопрос текстом, фотографией или любым другим медиавложением:',
        reply_markup=custom_back_markup('start')
    )
