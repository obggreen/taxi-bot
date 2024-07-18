from typing import Optional

from aiogram import html, F, types
from aiogram.filters import Command, CommandObject
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext

from database import User
from database.models.users import DocumentType
from handlers.routers import admin_router
from helpers.keyboards.markups import custom_back_markup


class SearchUser(StatesGroup):
    user = State()


class AdminCallback(CallbackData, prefix='verif'):
    action: str
    types: str
    user_id: Optional[int] = None

@admin_router.message(Command(commands='admin'))
async def admin_command(message: Message):
    markup = InlineKeyboardBuilder()
    markup.button(
        text='🔍 Найти пользователя', callback_data='search_user'
    )
    markup.button(
        text='👥 Работа со всеми пользователями', callback_data='work_all_users'
    )
    markup.button(
        text='📤 Рассылка', callback_data='mailing'
    )

    await message.answer(
        'Добро пожаловать в Админ меню!',
        reply_markup=markup.adjust(1).as_markup()
    )


@admin_router.callback_query(F.data == 'search_user')
async def search_user(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(
        'Введите ID, username или ФИО пользователя:',
        reply_markup=custom_back_markup('start')
    )
    await state.set_state(SearchUser.user)


@admin_router.message(SearchUser.user)
async def view_user(message: Message, state: FSMContext):
    input_data = message.text.strip()
    markup = InlineKeyboardBuilder()

    if input_data.isdigit():
        user = await User.find_one(User.user_id == int(input_data))
    else:
        user = await User.find_one(User.username == input_data)
        if not user:
            user = await User.find_one(User.fio == input_data)

    if user:
        markup.button(
            text='Заблокировать пользователя', callback_data=AdminCallback(
                action='user_private',
                types='ban',
                user_id=user.user_id
            )
        )
        markup.button(
            text='Разблокировать пользователя', callback_data=AdminCallback(
                action='user_private',
                types='unban',
                user_id=user.user_id
            )
        )
        markup.button(
            text='Запросить верификацию', callback_data=AdminCallback(
                action='user_verification',
                types='one_verification',
                user_id=user.user_id
            )
        )
        markup.button(
            text='Сгенерировать отчет', callback_data=AdminCallback(
                action='user_check_doc',
                types='check_doc',
                user_id=user.user_id
            )
        )
        markup.button(
            text='Забрать подписку', callback_data=AdminCallback(
                action='user_un_subscribe',
                types='check_doc',
                user_id=user.user_id
            )
        )
        markup.button(
            text='Выдать подписку', callback_data=AdminCallback(
                action='user_add_subscribe',
                types='check_doc',
                user_id=user.user_id
            )
        )

        if user.documents == DocumentType.verified:
            verification = '✅'
        else:
            verification = '❌'

        if user.blocked_bot == False:
            blocked = '<b>Нет блокировки</>'
        else:
            blocked = '<b>Заблокирован</>'


        await message.answer(
            f'<b>👱🏻‍♂️ Пользователь найден:</>\n\n'
            f'└ ID пользователя: {user.user_id}\n'
            f'└ username: {user.username}\n'
            f'└ Никнейм: {user.full_name}\n'
            f'└ Верификация: {verification}\n'
            f'└ Блокировка: {blocked}\n\n'
            f'└ ФИО: <b>{user.fio}</>\n'
            f'└ Номер телефона: <b>{user.number}</>',
            reply_markup=markup.adjust(1).as_markup()
        )
        await state.clear()
