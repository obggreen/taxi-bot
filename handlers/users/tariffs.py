from contextlib import suppress
from typing import Union

from aiogram import F, types
from aiogram.enums import ContentType
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.i18n import gettext as _, get_i18n
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, ChatMemberUpdated, FSInputFile, InlineKeyboardButton
from aiogram.filters.chat_member_updated import ChatMemberUpdatedFilter, MEMBER, KICKED
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.fsm.context import FSMContext

from data.settings import settings
from database import Tariff, Order
from database.models import User
from database.models.users import DocumentType
from handlers.users.base import SelectTariff
from helpers.functions import edit_send_media
from helpers.keyboards.fabric import SelectLanguageCallback
from helpers.keyboards.markups import default_markup, custom_back_button, custom_back_markup

from handlers.routers import user_router
from utils.yookassa.api import payment


@user_router.callback_query(F.data == 'tariff')
@user_router.message(F.text == '🛒 Тарифы')
async def check_tariff_plan(event: Union[Message, CallbackQuery], state: FSMContext, user: User):
    if isinstance(event, Message):
        answer = event.answer
    else:
        await event.message.delete()
        answer = event.message.answer

    if user.documents == DocumentType.untested:
        kb = InlineKeyboardBuilder()
        kb.button(
            text='ℹ️ Верификация', callback_data='verification'
        )
        await answer(
            'Что бы приобрести тариф, ваш нужно верифицировать свои данные.\n\n'
            'Используйте клавиатуру для верификации.',
            reply_markup=kb.adjust(1).as_markup()
        )
        return

    tariffs = await Tariff.all().to_list()

    if tariffs:
        markup = InlineKeyboardBuilder()

        for tariff in tariffs:
            markup.button(
                text=f'{tariff.name}', callback_data=SelectTariff(action='open', identity=tariff.identity)
            )

        await answer(
            'Выберите желаемый для вас тарифный план:  ⤵️',
            reply_markup=markup.adjust(1).as_markup()
        )
    else:
        await answer(
            '☹️ На данный момент нету активных тарифов, попробуйте чуть позже.'
        )


@user_router.callback_query(SelectTariff.filter(F.action == 'open'))
async def select_tariff(call: CallbackQuery, callback_data: SelectTariff, user: User):
    tariff = await Tariff.find_one(
        Tariff.identity == callback_data.identity
    )

    payment_data = await payment(amount=tariff.price)
    print(payment_data)
    url = payment_data.confirmation.confirmation_url
    print(url)

    await Order(
        user=user.id,
        identy=payment_data.id,
        amount=tariff.price,
        subscribe_id=tariff.identity
    ).insert()

    markup = InlineKeyboardBuilder()
    markup.button(
        text='ЮMoney', web_app=types.WebAppInfo(url=url)
    )

    if user.documents == DocumentType.untested:
        kb = InlineKeyboardBuilder()
        kb.button(
            text='ℹ️ Верификация', callback_data='verification'
        )
        await call.message.edit_text(
            'Что бы приобрести тариф, ваш нужно верифицировать свои данные.\n\n'
            'Используйте клавиатуру для верификации.',
            reply_markup=kb.adjust(1).as_markup()
        )
        return

    markup.row(custom_back_button('start'))

    await call.message.edit_text(
        f'<b>Выбранный тариф:</> {tariff.name}\n\n'
        f'<b>Цена:</> {tariff.price}₽\n'
        f'<b>Продолжительность:</> {tariff.count_days} дней\n\n'
        f'Вы получите доступ к чату: ...',
        reply_markup=markup.adjust(1).as_markup()
    )


