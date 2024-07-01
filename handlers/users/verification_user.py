import base64
import json

from aiogram import F, Bot
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, BufferedInputFile, InputMediaPhoto
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.models import User
from database.models.users import DocumentType
from gpt import get_response_gpt, check_sts_user, check_rights_user
from handlers.routers import user_router
from handlers.users.base import SelectVerificationType
from helpers.keyboards.markups import custom_back_button, custom_back_markup


class UserDocumentPhoto(StatesGroup):
    right_side = State()
    right_front = State()
    sts_side = State()
    sts_front = State()
    right_face = State()


class VerificarionUser(CallbackData, prefix='auto_verif'):
    action: str
    identity: str
    result: str


@user_router.callback_query(SelectVerificationType.filter(F.verif == 'document'))
async def verification_user_start(call: CallbackQuery):
    markup = InlineKeyboardBuilder()
    markup.button(
        text='✅ Согласен', callback_data='yes_user_verification'
    )
    markup.row(custom_back_button('start'))

    await call.message.edit_text(
        'Для завершения регистрации в нашем сервисе требуется прохождение верификации. '
        'Это необходимо для подтверждения вашей владельческой информации и удостоверение личности.\n\n'
        'Пожалуйста, загрузите следующие фотографии ваших документов:\n'
        '1. Фотографии прав (2 фотографии)\n'
        '2. Фотографии СТС (2 фотографии)\n'
        '3. Фотография лица с правами в руках\n\n'
        'Нажмите кнопку <b>"✅ Согласен"</b>, если готовы приступить к верификации.',
        reply_markup=markup.adjust(1).as_markup()
    )


@user_router.callback_query(F.data == 'yes_user_verification')
async def start_user(call: CallbackQuery, state: FSMContext):
    msg = await call.message.edit_text(
        '<b>Отправьте фотографию прав лицевой стороной:</b>',
        reply_markup=custom_back_markup('start')
    )

    await state.set_state(UserDocumentPhoto.right_side)
    await state.update_data(msg=msg.message_id)


@user_router.message(UserDocumentPhoto.right_side)
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
            content=check_rights_user
        )

        if gpt_check == '0':
            msg = await message.answer(
                'Не смогли разобрать номера на вашем автомобиле, пришлите фотографию в лучшем качестве.'
            )
            await state.update_data(msg=msg.message_id)
            return

        msg = await message.answer(
            f'✅ Фотография принята\n\n'
            f'Пришлите права задней части:',
            reply_markup=custom_back_markup('start')
        )

        await state.set_state(UserDocumentPhoto.right_front)
        await state.update_data(
            msg=msg.message_id,
            photo_one=photo_1_front_bytes,
            fio=gpt_check
        )

    else:
        msg = await message.answer(
            'Ваше сообщение должно содержать фотографию.',
            reply_markup=custom_back_markup('start')
        )
        await state.update_data(msg=msg.message_id)
        return


@user_router.message(UserDocumentPhoto.right_front)
async def select_bask_photo(message: Message, state: FSMContext, bot: Bot):
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
            f'Пришлите лицевую часть СТС:',
            reply_markup=custom_back_markup('start')
        )

        await state.set_state(UserDocumentPhoto.sts_front)
        await state.update_data(
            msg=msg.message_id,
            photo_two=photo_2_left_bytes
        )

    else:
        msg = await message.answer(
            'Ваше сообщение должно содержать фотографию.',
            reply_markup=custom_back_markup('start')
        )
        await state.update_data(msg=msg.message_id)
        return


@user_router.message(UserDocumentPhoto.sts_front)
async def select_bask_photo(message: Message, state: FSMContext, bot: Bot):
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
        photo_3_left_bytes = base64.b64encode(file.read()).decode('utf-8')

        gpt_check = await get_response_gpt(
            base=photo_3_left_bytes,
            content=check_sts_user
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
            f'Пришлите заднюю часть СТС:',
            reply_markup=custom_back_markup('start')
        )

        await state.set_state(UserDocumentPhoto.sts_side)
        await state.update_data(
            msg=msg.message_id,
            photo_three=photo_3_left_bytes,
            sts_number=gpt_check
        )

    else:
        msg = await message.answer(
            'Ваше сообщение должно содержать фотографию.',
            reply_markup=custom_back_markup('start')
        )
        await state.update_data(msg=msg.message_id)
        return


@user_router.message(UserDocumentPhoto.sts_side)
async def select_bask_photo(message: Message, state: FSMContext, bot: Bot):
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
        photo_5_left_bytes = base64.b64encode(file.read()).decode('utf-8')

        msg = await message.answer(
            f'✅ Фотография принята\n\n'
            f'Пришлите фотографию прав в одном кадре рядом со своим лицом:',
            reply_markup=custom_back_markup('start')
        )

        await state.set_state(UserDocumentPhoto.right_face)
        await state.update_data(
            msg=msg.message_id,
            photo_five=photo_5_left_bytes
        )

    else:
        msg = await message.answer(
            'Ваше сообщение должно содержать фотографию.',
            reply_markup=custom_back_markup('start')
        )
        await state.update_data(msg=msg.message_id)
        return


@user_router.message(UserDocumentPhoto.right_face)
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
        photo_6_back_salon_bytes = base64.b64encode(file.read()).decode('utf-8')

        await message.answer(
            f'✅ Ваши фотографии автомобиля успешно отправлена на модерацию администрации.\n\n'
            f'Ожидайте уведомления о результате проверки.',
            reply_markup=custom_back_markup('start')
        )

        markup = InlineKeyboardBuilder()
        markup.button(
            text='Подтвердить верификацию',
            callback_data=VerificarionUser(action='open', identity=user.identity, result='okay')
        )
        markup.button(
            text='Отклонить верификацию',
            callback_data=VerificarionUser(action='open', identity=user.identity, result='no')
        )

        user.photo_user_documents.right_front = data['photo_one']
        user.photo_user_documents.right_back = data['photo_two']
        user.photo_user_documents.sts_front = data['photo_three']
        user.photo_user_documents.sts_back = data['photo_five']
        user.photo_user_documents.person_right = photo_6_back_salon_bytes
        user.photo_user_documents.sts_number = data['sts_number']
        user.fio = data['fio']
        await user.save()
        await state.clear()

        photo_1 = BufferedInputFile(base64.b64decode(user.photo_user_documents.right_front), filename='1')
        photo_2 = BufferedInputFile(base64.b64decode(user.photo_user_documents.right_back), filename='1')
        photo_3 = BufferedInputFile(base64.b64decode(user.photo_user_documents.sts_front), filename='1')
        photo_4 = BufferedInputFile(base64.b64decode(user.photo_user_documents.sts_back), filename='1')
        photo_5 = BufferedInputFile(base64.b64decode(user.photo_user_documents.person_right), filename='1')

        media_group = [
            InputMediaPhoto(media=photo_1),
            InputMediaPhoto(media=photo_2),
            InputMediaPhoto(media=photo_3),
            InputMediaPhoto(media=photo_4),
            InputMediaPhoto(media=photo_5),
        ]

        sts_data = json.loads(user.photo_user_documents.sts_number)

        sts_info = (
            f"Марка: {sts_data.get('марка', '0')}\n"
            f"Модель: {sts_data.get('модель', '0')}\n"
            f"Цвет: {sts_data.get('цвет', '0')}\n"
            f"Гос номер: {sts_data.get('гос_номер', '0')}\n"
            f"Год выпуска: {sts_data.get('год_выпуска', '0')}\n"
            f"Серия: {sts_data.get('Серия', '0')}\n"
            f"Номер: {sts_data.get('Номер', '0')}"
        )

        await bot.send_media_group(
            chat_id=-1002210540953,
            message_thread_id=4,
            media=media_group
        )
        await bot.send_message(
            text=f'Username: <b>@{user.username}</>\n'
                 f'Номер телефона: {user.number}\n'
                 f'ФИО: <b>{user.fio}</>\n'
                 f'<b>Данные СТС</>:\n{sts_info}',
            chat_id=-1002210540953,
            message_thread_id=4,
            reply_markup=markup.adjust(1).as_markup()
        )
        await state.clear()

    else:
        msg = await message.answer(
            'Ваше сообщение должно содержать фотографию.',
            reply_markup=custom_back_markup('start')
        )
        await state.update_data(msg=msg.message_id)
        return


@user_router.callback_query(VerificarionUser.filter(F.action == 'open'))
async def chat_callback(call: CallbackQuery, callback_data: VerificarionUser, bot: Bot):
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
            text='Ваши личные документы успешно прошли проверку!\n'
                 'Можете использовать весь функционал бота.',
            reply_markup=markup.adjust(1).as_markup()
        )

        user.verification.verification_auto = True
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
