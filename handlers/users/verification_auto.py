import base64
import types

from aiogram import F, Bot
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, BufferedInputFile, InputMediaPhoto, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.models import User
from database.models.users import DocumentType, VerifType
from gpt import get_response_gpt, check_auto_number
from handlers.routers import user_router
from handlers.users.base import SelectVerificationType
from helpers.functions import create_payment_link
from helpers.keyboards.markups import custom_back_button, custom_back_markup


class VerificarionAuto(CallbackData, prefix='auto_verif'):
    action: str
    identity: str
    result: str


class UserAutoPhoto(StatesGroup):
    waiting_photo_auto_front = State()
    waiting_photo_auto_left = State()
    waiting_photo_right_left = State()
    waiting_photo_back_left = State()
    waiting_photo_salon_front = State()
    waiting_photo_salon_back = State()


@user_router.callback_query(SelectVerificationType.filter(F.verif == 'auto'))
async def verification_auto_start(call: CallbackQuery):
    markup = InlineKeyboardBuilder()
    markup.button(
        text='✅ Согласен', callback_data='yes_auto_verification'
    )
    markup.row(custom_back_button('start'))

    await call.message.edit_text(
        'Для завершения регистрации вашего автомобиля в нашем сервисе требуется прохождение верификации. '
        'Это необходимо для подтверждения вашей владельческой информации и состояния автомобиля.\n\n'
        'Пожалуйста, загрузите следующие фотографии вашего автомобиля:\n'
        '1. Фотографии автомобиля со всех сторон (4 фотографии)\n'
        '2. Фотографии салона автомобиля (2 фотографии)\n'
        '3. Фотография багажного отделения\n\n'
        'Нажмите кнопку <b>"✅ Согласен"</b>, если готовы приступить к верификации.',
        reply_markup=markup.adjust(1).as_markup()
    )


@user_router.callback_query(F.data == 'yes_auto_verification')
async def start_auto(call: CallbackQuery, state: FSMContext):
    msg = await call.message.edit_text(
        '<b>Отправьте фотографию автомобиля спереди в ответ на данное сообщение!</b>',
        reply_markup=custom_back_markup('start')
    )

    await state.set_state(UserAutoPhoto.waiting_photo_auto_front)
    await state.update_data(msg=msg.message_id)


@user_router.message(UserAutoPhoto.waiting_photo_auto_front)
async def select_front_photo(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
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
        photo_1_front_bytes = base64.b64encode(file.read()).decode('utf-8')

        gpt_check = await get_response_gpt(
            base=photo_1_front_bytes,
            content=check_auto_number
        )

        print(gpt_check)

        if gpt_check == '0':
            msg = await message.answer(
                'Не смогли разобрать номера на вашем автомобиле, пришлите фотографию в лучшем качестве.'
            )
            await state.update_data(msg=msg.message_id)
            return

        msg = await message.answer(
            f'✅ Фотография принята\n\n'
            f'Номера вашего автомобиля: <b>{gpt_check}</>\n\n'
            f'Пришлите фотографию автомобиля с правой стороны:',
            reply_markup=custom_back_markup('start')
        )

        await state.set_state(UserAutoPhoto.waiting_photo_auto_left)
        await state.update_data(
            msg=msg.message_id,
            photo_front=photo_1_front_bytes,
            auto_number=gpt_check
        )

    else:
        msg = await message.answer(
            'Ваше сообщение должно содержать фотографию.',
            reply_markup=custom_back_markup('start')
        )
        await state.update_data(msg=msg.message_id)
        return


@user_router.message(UserAutoPhoto.waiting_photo_auto_left)
async def select_left_photo(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
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
        photo_2_left_bytes = base64.b64encode(file.read()).decode('utf-8')

        msg = await message.answer(
            f'✅ Фотография принята\n\n'
            f'Пришлите фотографию автомобиля с левой стороны:',
            reply_markup=custom_back_markup('start')
        )

        await state.set_state(UserAutoPhoto.waiting_photo_right_left)
        await state.update_data(
            msg=msg.message_id,
            photo_left=photo_2_left_bytes
        )

    else:
        msg = await message.answer(
            'Ваше сообщение должно содержать фотографию.',
            reply_markup=custom_back_markup('start')
        )
        await state.update_data(msg=msg.message_id)
        return


@user_router.message(UserAutoPhoto.waiting_photo_right_left)
async def select_right_photo(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
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
        photo_3_right_bytes = base64.b64encode(file.read()).decode('utf-8')

        msg = await message.answer(
            f'✅ Фотография принята\n\n'
            f'Пришлите фотографию автомобиля сзади:',
            reply_markup=custom_back_markup('start')
        )

        await state.set_state(UserAutoPhoto.waiting_photo_back_left)
        await state.update_data(
            msg=msg.message_id,
            photo_rigth=photo_3_right_bytes
        )

    else:
        msg = await message.answer(
            'Ваше сообщение должно содержать фотографию.',
            reply_markup=custom_back_markup('start')
        )
        await state.update_data(msg=msg.message_id)
        return


@user_router.message(UserAutoPhoto.waiting_photo_back_left)
async def select_back_photo(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
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
        photo_4_back_bytes = base64.b64encode(file.read()).decode('utf-8')

        msg = await message.answer(
            f'✅ Фотография принята\n\n'
            f'Пришлите фотографию салона спереди:',
            reply_markup=custom_back_markup('start')
        )

        await state.set_state(UserAutoPhoto.waiting_photo_salon_front)
        await state.update_data(
            msg=msg.message_id,
            photo_back=photo_4_back_bytes
        )

    else:
        msg = await message.answer(
            'Ваше сообщение должно содержать фотографию.',
            reply_markup=custom_back_markup('start')
        )
        await state.update_data(msg=msg.message_id)
        return


@user_router.message(UserAutoPhoto.waiting_photo_salon_front)
async def select_sl_photo(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
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
        photo_5_front_salon_bytes = base64.b64encode(file.read()).decode('utf-8')

        msg = await message.answer(
            f'✅ Фотография принята\n\n'
            f'Пришлите фотографию салона сзади:',
            reply_markup=custom_back_markup('start')
        )

        await state.set_state(UserAutoPhoto.waiting_photo_salon_back)
        await state.update_data(
            msg=msg.message_id,
            photo_salon_front=photo_5_front_salon_bytes
        )

    else:
        msg = await message.answer(
            'Ваше сообщение должно содержать фотографию.',
            reply_markup=custom_back_markup('start')
        )
        await state.update_data(msg=msg.message_id)
        return


@user_router.message(UserAutoPhoto.waiting_photo_salon_back)
async def select_sl_photo(message: Message, state: FSMContext, bot: Bot, user: User):
    data = await state.get_data()
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
        photo_5_back_salon_bytes = base64.b64encode(file.read()).decode('utf-8')

        await message.answer(
            f'✅ Ваши фотографии автомобиля успешно отправлена на модерацию администрации.\n\n'
            f'Ожидайте уведомления о результате проверки.',
            reply_markup=custom_back_markup('start')
        )

        markup = InlineKeyboardBuilder()
        markup.button(
            text='Подтвердить верификацию',
            callback_data=VerificarionAuto(action='open', identity=user.identity, result='okay')
        )
        markup.button(
            text='Отклонить верификацию',
            callback_data=VerificarionAuto(action='open', identity=user.identity, result='no')
        )

        user.photo_auto_documents.auto_front = data['photo_front']
        user.photo_auto_documents.auto_back = data['photo_back']
        user.photo_auto_documents.auto_left = data['photo_left']
        user.photo_auto_documents.auto_right = data['photo_rigth']
        user.photo_auto_documents.salon_front = data['photo_salon_front']
        user.photo_auto_documents.salon_back = photo_5_back_salon_bytes
        user.photo_auto_documents.auto_number = data['auto_number']
        await user.save()
        await state.clear()

        photo_1 = BufferedInputFile(base64.b64decode(user.photo_auto_documents.auto_front), filename='1')
        photo_2 = BufferedInputFile(base64.b64decode(user.photo_auto_documents.auto_left), filename='1')
        photo_3 = BufferedInputFile(base64.b64decode(user.photo_auto_documents.auto_back), filename='1')
        photo_4 = BufferedInputFile(base64.b64decode(user.photo_auto_documents.auto_right), filename='1')
        photo_5 = BufferedInputFile(base64.b64decode(user.photo_auto_documents.salon_back), filename='1')
        photo_6 = BufferedInputFile(base64.b64decode(user.photo_auto_documents.salon_front), filename='1')

        media_group = [
            InputMediaPhoto(media=photo_1),
            InputMediaPhoto(media=photo_2),
            InputMediaPhoto(media=photo_3),
            InputMediaPhoto(media=photo_4),
            InputMediaPhoto(media=photo_5),
            InputMediaPhoto(media=photo_6)
        ]

        await bot.send_media_group(
            chat_id=-1002210540953,
            message_thread_id=231,
            media=media_group
        )
        await bot.send_message(
            text=f'Username: <b>@{user.username}</>\n'
                 f'Номер телефона: {user.number}\n'
                 f'Номера автомобиля: {user.photo_auto_documents.auto_number}',
            chat_id=-1002210540953,
            message_thread_id=231,
            reply_markup=markup.adjust(1).as_markup()
        )
        user.active_auto = VerifType.waiting
        await state.clear()
        await user.save()

    else:
        msg = await message.answer(
            'Ваше сообщение должно содержать фотографию.',
            reply_markup=custom_back_markup('start')
        )
        await state.update_data(msg=msg.message_id)
        return


@user_router.callback_query(VerificarionAuto.filter(F.action == 'open'))
async def chat_callback(call: CallbackQuery, callback_data: VerificarionAuto, bot: Bot):
    user = await User.find_one(
        User.identity == callback_data.identity
    )
    markup = InlineKeyboardBuilder()
    kb = InlineKeyboardBuilder()

    if callback_data.result == 'okay':
        key = InlineKeyboardBuilder()

        key.button(
            text='📍Поделиться геопозицией',
            callback_data='call_geoposition'
        )

        kb.button(
            text='✅', callback_data='pass'
        )

        await bot.edit_message_reply_markup(
            chat_id=-1002210540953,
            message_id=call.message.message_id,
            reply_markup=kb.as_markup()
        )

        url = await create_payment_link(user)

        markup.button(
            text='Оплатить 1000 ₽', web_app=WebAppInfo(url=url)
        )
        await bot.send_message(
            chat_id=user.user_id,
            text='Ваши документы успешно прошли проверку!\n'
                 'Стоимость подключения к группе: 1000 рублей.',
            reply_markup=markup.adjust(1).as_markup()
        )
        await bot.send_message(
            chat_id=user.user_id,
            text=
            'Для повышение приоритета выдачи заказов, вы можете поделиться своим местоположение, что бы операторы '
            'видели вас около заказа и могли вам выдать ближайший!',
            reply_markup=key.as_markup()
        )

        user.verification.verification_auto = True
        user.active_auto = VerifType.yes
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
        user.active_doc = VerifType.no
        await user.save()
