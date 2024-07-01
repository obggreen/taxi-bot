import base64
from contextlib import suppress
from typing import Union

from aiogram import F, types, Bot
from aiogram.enums import ContentType
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.i18n import gettext as _, get_i18n
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, ChatMemberUpdated, FSInputFile, InlineKeyboardButton, \
    BufferedInputFile, InputMediaPhoto
from aiogram.filters.chat_member_updated import ChatMemberUpdatedFilter, MEMBER, KICKED
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.fsm.context import FSMContext

from data.settings import settings
from database import Tariff
from database.models import User
from database.models.users import DocumentType, UserDocument
from handlers.users.base import SelectTariff
from helpers.functions import edit_send_media
from helpers.keyboards.fabric import SelectLanguageCallback
from helpers.keyboards.markups import default_markup, custom_back_button, custom_back_markup

from handlers.routers import user_router


class Verificarion(CallbackData, prefix='verif'):
    action: str
    identity: str
    result: str


class UserPhoto(StatesGroup):
    waiting_fio = State()
    waiting_titul_photo = State()
    waiting_two_photo = State()


@user_router.callback_query(F.data == 'verification')
async def verification_user_start(call: CallbackQuery):
    markup = InlineKeyboardBuilder()
    markup.button(
        text='✅ Согласен', callback_data='yes_verification'
    )
    markup.row(custom_back_button('start'))

    await call.message.edit_text(
        'Для доступа к сервису и всего его функционала, мы проводим верификацию пользователей, что бы удостовериться, '
        'что человек является тем, за кого себя выдает\n\n'
        'Если согласны пройти верификацию на нашем сервисе, нажмите кнопку <b>"✅ Согласен"</>\n\n'
        '<i>Нажимая кнопку "✅ Согласен" вы соглашаетесь с обработкой ваших персональных данных, так же, наш сервис дает'
        ' гарантию, что ваши персональные данные не попадут третьим лицам.</>',
        reply_markup=markup.adjust(1).as_markup()
    )


@user_router.callback_query(F.data == 'yes_verification')
async def start_verification(call: CallbackQuery, state: FSMContext):
    msg = await call.message.edit_text(
        'Для верификации, вам нужно отправить фотографии паспорта на котором главная страница с вашей фотографией и '
        'сторона с пропиской. В описание к фото пришлите ваше полное ФИО.\n\n'
        '<b>Отправьте полное ФИО в ответ на данное сообщение!</>',
        reply_markup=custom_back_markup('start')
    )

    await state.set_state(UserPhoto.waiting_fio)
    await state.update_data(msg=msg.message_id)


@user_router.message(UserPhoto.waiting_fio)
async def select_photo(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    message_id = data['msg']
    await bot.edit_message_reply_markup(
        chat_id=message.chat.id,
        message_id=message_id,
        reply_markup=None
    )

    if message.text:
        words = message.text.split()
        if len(words) >= 3:
            msg = await message.answer(
                f'<b>Ваше ФИО:</> {message.text}\n\n'
                f'Пришлите фотографию паспорта с разворотом фотографии:',
                reply_markup=custom_back_markup('start')
            )

            await state.set_state(UserPhoto.waiting_titul_photo)
            await state.update_data(
                msg=msg.message_id,
                fio=message.text
            )
        else:
            msg = await message.answer(
                'Вы указали не верное ФИО, попробуйте еще раз!'
            )
            await state.update_data(msg=msg.message_id)
            return
    else:
        msg = await message.answer(
            'ФИО должно содержать в себе только текст.'
        )
        await state.update_data(msg=msg.message_id)
        return


@user_router.message(UserPhoto.waiting_titul_photo)
async def select_titul(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    fio = data['fio']
    message_id = data['msg']

    await bot.edit_message_reply_markup(
        chat_id=message.chat.id,
        message_id=message_id,
        reply_markup=None
    )

    if message.photo:
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
        file = await bot.download_file(file_info.file_path)
        photo_1_bytes = base64.b64encode(file.read()).decode('utf-8')

        msg = await message.answer(
            f'<b>Ваше ФИО:</> {fio}\n'
            f'<b>Фотография номер 1: ✅</>\n\n'
            f'Пришлите фотографию паспорта с разворотом прописки:',
            reply_markup=custom_back_markup('start')
        )

        await state.set_state(UserPhoto.waiting_two_photo)
        await state.update_data(
            msg=msg.message_id,
            photo_1=photo_1_bytes
        )
    else:
        msg = await message.answer(
            'Ваше сообщение должно содержать фотографию.'
        )
        await state.update_data(msg=msg.message_id)
        return


@user_router.message(UserPhoto.waiting_two_photo)
async def select_two_photo(message: Message, state: FSMContext, bot: Bot, user: User):
    data = await state.get_data()
    fio = data['fio']
    photo_1 = data['photo_1']
    message_id = data['msg']

    await bot.edit_message_reply_markup(
        chat_id=message.chat.id,
        message_id=message_id,
        reply_markup=None
    )

    if message.photo:
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
        file = await bot.download_file(file_info.file_path)
        photo_2 = base64.b64encode(file.read()).decode('utf-8')

        await message.answer(
            f'<b>Ваше ФИО:</> {fio}\n'
            f'<b>Фотография номер 1: ✅</>\n'
            f'<b>Фотография номер 2: ✅</>\n\n'
            f'<b>Данные отправлены на проверку администрации, как только ваши данные проверят, вам придет уведомление!</>'
        )

        user.fio = fio
        user.photo_auto_documents.titul_photo = photo_1
        user.photo_auto_documents.street_photo = photo_2
        await user.save()

        markup = InlineKeyboardBuilder()
        markup.button(
            text='Подтвердить верификацию',
            callback_data=Verificarion(action='open', identity=user.identity, result='okay')
        )
        markup.button(
            text='Отклонить верификацию',
            callback_data=Verificarion(action='open', identity=user.identity, result='no')
        )

        photo_1_bytes = BufferedInputFile(base64.b64decode(user.photo_auto_documents.titul_photo), filename='1')
        photo_2_bytes = BufferedInputFile(base64.b64decode(user.photo_auto_documents.street_photo), filename='1')

        media_group = [
            InputMediaPhoto(media=photo_1_bytes, caption=fio),
            InputMediaPhoto(media=photo_2_bytes, caption=fio)
        ]

        await bot.send_media_group(
            chat_id=-1002210540953,
            message_thread_id=4,
            media=media_group
        )
        await bot.send_message(
            text=f'ФИО: <b>{fio}</>\n'
                 f'Username: <b>@{user.username}</>\n'
                 f'Номер телефона: {user.number}',
            chat_id=-1002210540953,
            message_thread_id=4,
            reply_markup=markup.adjust(1).as_markup()
        )
        await state.clear()
    else:
        msg = await message.answer(
            'Ваше сообщение должно содержать фотографию.'
        )
        await state.update_data(msg=msg.message_id)
        return


@user_router.callback_query(Verificarion.filter(F.action == 'open'))
async def chat_callback(call: CallbackQuery, callback_data: Verificarion, bot: Bot):
    user = await User.find_one(
        User.identity == callback_data.identity
    )
    markup = InlineKeyboardBuilder()
    kb = InlineKeyboardBuilder()

    if callback_data.result == 'okay':
        kb.button(
            text='✅', callback_data='pass'
        )
        await bot.edit_message_reply_markup(
            chat_id=-1002210540953,
            message_id=call.message.message_id,
            reply_markup=kb.as_markup()
        )
        markup.button(
            text='🚖 Тарифы', callback_data='tariff'
        )
        await bot.send_message(
            chat_id=user.user_id,
            text='Ваши документы успешно прошли проверку!\n'
                 'Можете использовать весь функционал бота.',
            reply_markup=markup.adjust(1).as_markup()
        )

        user.documents = DocumentType.verified
        await user.save()
    else:
        kb.button(
            text='✅', callback_data='pass'
        )
        await bot.edit_message_reply_markup(
            chat_id=-1002210540953,
            message_id=call.message.message_id,
            reply_markup=kb.as_markup()
        )

        markup.button(
            text='Узнать почему', url='t.me/greenbot'
        )
        await bot.send_message(
            chat_id=user.user_id,
            text='Ваши документы не прошли проверку.',
            reply_markup=markup.adjust(1).as_markup()
        )
