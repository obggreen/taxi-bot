import base64
import io
from contextlib import suppress
from io import BytesIO
from typing import Union

from aiogram import F, types, Bot
from aiogram.enums import ContentType
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.i18n import gettext as _, get_i18n
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, ChatMemberUpdated, FSInputFile, InlineKeyboardButton, \
    BufferedInputFile
from aiogram.filters.chat_member_updated import ChatMemberUpdatedFilter, MEMBER, KICKED
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.fsm.context import FSMContext
from docx import Document as DocxDocument
from docx.shared import Pt

from data.settings import settings
from database import Tariff
from database.models import User
from database.models.users import DocumentType
from handlers.users.monitoring import find_duplicate_numbers, format_duplicate_message
from helpers.functions import edit_send_media
from helpers.keyboards.fabric import SelectLanguageCallback
from helpers.keyboards.markups import default_markup, custom_back_button

from handlers.routers import user_router


class SelectTariff(CallbackData, prefix='tariff'):
    action: str
    identity: int


class SelectVerificationType(CallbackData, prefix='ver'):
    action: str
    verif: str


class PhoneState(StatesGroup):
    waiting_for_phone = State()


@user_router.callback_query(F.data == 'start')
@user_router.message(Command(commands='start'))
async def start_command(event: Union[Message, CallbackQuery], state: FSMContext, user: User, bot: Bot):
    await state.clear()

    if isinstance(event, Message):
        answer = event.answer
    else:
        await event.message.delete()
        answer = event.message.answer

    duplicates, sts_duplicates = await find_duplicate_numbers()
    duplicate_message = await format_duplicate_message(duplicates, sts_duplicates)

    if duplicate_message:
        file = FSInputFile('files/wairning.jpg')

        await bot.send_photo(
            photo=file,
            chat_id=-1002210540953,
            message_thread_id=4
        )

        await bot.send_message(
            text=duplicate_message,
            chat_id=-1002210540953,
            message_thread_id=4
        )

    if user:
        if user.number is None:

            markup = ReplyKeyboardBuilder()
            markup.button(text='📞 Поделиться номером', request_contact=True)

            await answer(
                'Добро пожаловать в бота!\n'
                'Вам нужно подтвердить свой номер телефона.',
                reply_markup=markup.as_markup(resize_keyboard=True)
            )

            await state.set_state(PhoneState.waiting_for_phone)
        else:
            await answer(
                'Добро пожаловать в бота!',
                reply_markup=default_markup()
            )

            tariffs = await Tariff.all().to_list()
            markup = InlineKeyboardBuilder()

            if user.verification.verification_auto and user.verification.verification_user:
                if tariffs:
                    for tariff in tariffs:
                        markup.button(
                            text=tariff.name, callback_data=SelectTariff(action='open', identity=tariff.identity)
                        )

                    await answer(
                        'Выберите желаемый для вас тарифный план:  ⤵️',
                        reply_markup=markup.adjust(1).as_markup()
                    )
            else:

                if not user.verification.verification_user:
                    markup.button(
                        text='📃 Верификация документов',
                        callback_data=SelectVerificationType(action='open', verif='document')
                    )

                if not user.verification.verification_auto:
                    markup.button(
                        text='📃 Верификация автомобиля',
                        callback_data=SelectVerificationType(action='open', verif='auto')
                    )

                await answer(
                    '<b>⚠️ СЛУЖЕБНОЕ УВЕДОМЛЕНИЕ</>\n\n'
                    '<i>Для использования функционала бота, вам нужно пройти верификацию</>',
                    reply_markup=markup.adjust(1).as_markup()
                )
    else:
        await answer(
            'Добро пожаловать в бота!',
            reply_markup=default_markup()
        )


@user_router.message(PhoneState.waiting_for_phone)
async def select_user_phone(message: Message, state: FSMContext, user: User):
    if message.contact:
        contact = message.contact

        if contact:
            original_number = contact.phone_number

            corrected_number = original_number.replace('7', '8', 1)

            user.number = corrected_number

            await message.answer(
                '💬 Номер телефона успешно сохранен!',
                reply_markup=default_markup()
            )

            tariffs = await Tariff.all().to_list()
            markup = InlineKeyboardBuilder()

            if user.documents == DocumentType.verified:
                if tariffs:
                    for tariff in tariffs:
                        markup.button(
                            text=tariff.name, callback_data=SelectTariff(action='open', identity=tariff.identity)
                        )

                    await message.answer(
                        'Выберите желаемый для вас тарифный план:  ⤵️',
                        reply_markup=markup.adjust(1).as_markup()
                    )
                else:
                    markup.button(
                        text='Верификация документов',
                        callback_data=SelectVerificationType(action='open', verif='document')
                    )
                    markup.button(
                        text='Верификация автомобиля', callback_data=SelectVerificationType(action='open', verif='auto')
                    )

                    await message.answer(
                        '<b>⚠️ СЛУЖЕБНОЕ УВЕДОМЛЕНИЕ</>\n\n'
                        '<i>Для использования функционала бота, вам нужно пройти верификацию</>',
                        reply_markup=markup.adjust(1).as_markup()
                    )

            await user.save()
            await state.clear()
        else:
            await message.answer(
                '❌ Произошла ошибка при получение номера, попробуйте позже.'
            )
            await state.clear()
    else:
        await message.answer(
            'Сообщение не содержит телефона или вы поделились телефоном не через кнопку.'
        )


def add_image_if_base64(doc, title, base64_str):
    if base64_str:
        try:
            image_data = base64.b64decode(base64_str)
            image_stream = io.BytesIO(image_data)
            doc.add_heading(title, level=2)
            doc.add_picture(image_stream)
        except Exception as e:
            pass  # Ignore errors for invalid base64 strings


def generate_user_report_in_memory(user: User):
    doc = DocxDocument()

    doc.add_heading(f'Досье на пользователя {user.full_name}', 0)

    doc.add_heading('Основная информация', level=1)
    doc.add_paragraph(f'Полное имя: {user.full_name}')
    doc.add_paragraph(f'Имя пользователя: {user.username}')
    doc.add_paragraph(f'Роль: {user.role}')
    doc.add_paragraph(f'Дата регистрации: {user.registration_date.strftime("%Y-%m-%d %H:%M:%S")}')
    doc.add_paragraph(
        f'Последняя активность: {user.last_active.strftime("%Y-%m-%d %H:%M:%S") if user.last_active else "N/A"}')

    doc.add_heading('Верификация', level=1)
    doc.add_paragraph(f'Верификация на автомобиль: {"Да" if user.verification.verification_auto else "Нет"}')
    doc.add_paragraph(f'Верификация на документы: {"Да" if user.verification.verification_user else "Нет"}')

    doc.add_heading('Настройки', level=1)
    doc.add_paragraph(f'Язык: {user.settings.language}')

    doc.add_heading('Финансовая информация', level=1)
    doc.add_paragraph(f'Баланс: {user.balance} руб.')
    doc.add_paragraph(f'Подписка: {user.subscription if user.subscription else "Нет"}')

    doc.add_heading('Информация об автомобиле', level=1)
    doc.add_paragraph(f'Номера автомобиля: {user.photo_auto_documents.auto_number}')
    add_image_if_base64(doc, 'Перед автомобиля', user.photo_auto_documents.auto_front)
    add_image_if_base64(doc, 'Левая сторона автомобиля', user.photo_auto_documents.auto_left)
    add_image_if_base64(doc, 'Правая сторона автомобиля', user.photo_auto_documents.auto_right)
    add_image_if_base64(doc, 'Зад автомобиля', user.photo_auto_documents.auto_back)
    add_image_if_base64(doc, 'Салон спереди', user.photo_auto_documents.salon_front)
    add_image_if_base64(doc, 'Зад салона', user.photo_auto_documents.salon_back)

    byte_stream = io.BytesIO()
    doc.save(byte_stream)
    byte_stream.seek(0)

    return byte_stream


@user_router.message(Command(commands='test'))
async def test(message: Message, user: User):
    byte_stream = generate_user_report_in_memory(user)

    # Создание BufferedInputFile для отправки файла
    document = BufferedInputFile(byte_stream.read(), filename=f'user_report_{user.user_id}.docx')

    # Отправка документа пользователю
    await message.answer_document(document)


@user_router.callback_query(F.data == 'close')
async def close_callback(event: CallbackQuery):
    with suppress(Exception):
        await event.message.delete()


# @user_router.callback_query(F.data == 'language')
# async def change_language(event: CallbackQuery):
#     markup = InlineKeyboardBuilder()
#     markup.button(text='🇷🇺 Русский', callback_data=SelectLanguageCallback(language='ru'))
#     markup.button(text='🇺🇸 English', callback_data=SelectLanguageCallback(language='en')).adjust(2)
#     markup.row(custom_back_button('profile'))
#
#     await edit_send_media(
#         event=event,
#         text=_(
#             "Выберите язык интерфейса:"
#         ),
#         reply_markup=markup.as_markup()
#     )


# @user_router.callback_query(SelectLanguageCallback.filter())
# async def change_language_callback(event: CallbackQuery, callback_data: SelectLanguageCallback, user: User, state: FSMContext):
#     user.settings.language = callback_data.language
#     await user.save()
#
#     await event.message.delete()
#
#     get_i18n().ctx_locale.set(callback_data.language)
#
#     await start_command(event.message, state)


@user_router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=KICKED))
async def user_blocked_bot(event: ChatMemberUpdated):
    user = await User.find_one(User.user_id == event.from_user.id)
    if user:
        user.blocked_bot = True
        await user.save()


@user_router.my_chat_member(ChatMemberUpdatedFilter(member_status_changed=MEMBER))
async def user_unblocked_bot(event: ChatMemberUpdated):
    user = await User.find_one(User.user_id == event.from_user.id)
    if user:
        user.blocked_bot = False
        await user.save()
