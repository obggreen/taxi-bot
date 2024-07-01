from aiogram import html, F, types
from aiogram.filters import Command, CommandObject
from aiogram.filters.callback_data import CallbackData
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from handlers.routers import admin_router


class AdminCallback(CallbackData, prefix='verif'):
    action: str
    types: str

@admin_router.message(Command(commands='admin'))
async def admin_command(message: Message):
    markup = InlineKeyboardBuilder()
    markup.button(
        text='Заблокировать пользователя', callback_data=AdminCallback(action='block_user', types='block')
    )
    markup.button(
        text='Разблокировать пользователя', callback_data=AdminCallback(action='block_user', types='unlock')
    )
    markup.button(
        text='Выдать подписку', callback_data='take_subscriptions'
    )
    markup.button(
        text='Забрать подписку', callback_data='off_subscriptions'
    )
    markup.button(
        text='Запросить актуализацию', callback_data='actualization'
    )
    markup.button(
        text='Рассылка', callback_data='mailing'
    )

    await message.answer(
        'Добро пожаловать в Админ меню!',
        reply_markup=markup.adjust(1).as_markup()
    )
