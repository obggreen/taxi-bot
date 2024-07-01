from aiogram.utils.keyboard import InlineKeyboardButton, InlineKeyboardBuilder, ReplyKeyboardBuilder, KeyboardButton
from aiogram.utils.i18n.context import gettext as _


def default_markup():
    markup = ReplyKeyboardBuilder()

    markup.row(
        KeyboardButton(text='🛒 Тарифы'),
        KeyboardButton(text='📊 Подписка'),
    )
    markup.row(
        KeyboardButton(text='📨 Обратная связь')
    )

    return markup.as_markup(resize_keyboard=True)


def custom_back_button(data, text: str = None):
    return InlineKeyboardButton(text=text or '← Назад', callback_data=data)


def custom_back_markup(data, text: str = None):
    markup = InlineKeyboardBuilder()
    markup.row(
        custom_back_button(data, text)
    )
    return markup.as_markup()
