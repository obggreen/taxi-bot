import base64
import json
import types
from contextlib import suppress

from aiogram import F, Bot
from aiogram.filters.callback_data import CallbackData
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, BufferedInputFile, InputMediaPhoto, WebAppInfo, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.models import User
from database.models.users import DocumentType, VerifType
from gpt import get_response_gpt, check_auto_number, check_rights_user, check_sts_user
from handlers.routers import user_router
from handlers.users.base import SelectVerificationType
from helpers.functions import create_payment_link
from helpers.keyboards.markups import custom_back_button, custom_back_markup



class VerificarionAuto(CallbackData, prefix='auto_verif'):
    action: str
    identity: str
    result: str


class UserBaseVerification(StatesGroup):
    photo_rights = State()
    facial_sts = State()
    rear_sts = State()
    rights_face = State()
    auto_front = State()
    auto_left = State()
    auto_right = State()
    auto_back = State()


@user_router.callback_query(F.data == 'base_verification')
async def verification_user_start(call: CallbackQuery):
    markup = InlineKeyboardBuilder()
    markup.button(
        text='✅ Согласен', callback_data='yes_base_verification'
    )
    markup.row(custom_back_button('start'))

    await call.message.edit_text(
        'Для завершения регистрации в нашем сервисе требуется прохождение верификации. '
        'Это необходимо для подтверждения вашей владельческой информации и удостоверение личности.\n\n'
        'Пожалуйста, загрузите следующие фотографии ваших документов:\n'
        '1. Фотографии прав\n'
        '2. Фотографии СТС (2 фотографии)\n'
        '3. Фотография лица с правами в руках\n'
        '4. Фотографии автомобиля со всех сторон (4 шт.)\n\n'
        'Нажмите кнопку <b>"✅ Согласен"</b>, если готовы приступить к верификации.',
        reply_markup=markup.adjust(1).as_markup()
    )


@user_router.callback_query(F.data == 'yes_base_verification')
async def start_auto(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    photo = FSInputFile('files/2Права.jpg')

    msg = await call.message.answer_photo(
        photo=photo,
        caption='<b>Отправьте фотографию водительских прав лицевой стороной:</b>',
        reply_markup=custom_back_markup('start')
    )

    await state.set_state(UserBaseVerification.photo_rights)
    await state.update_data(msg=msg.message_id)


@user_router.message(UserBaseVerification.photo_rights)
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
        photo_rights = base64.b64encode(file.read()).decode('utf-8')

        gpt_check = await get_response_gpt(
            base=photo_rights,
            content=check_rights_user
        )

        if gpt_check == '0':
            msg = await message.answer(
                'Не смогли разобрать ваши права, пришлите фотографию в лучшем качестве.',
                reply_markup=custom_back_markup('start')
            )
            await state.update_data(msg=msg.message_id)
            return

        photo = FSInputFile('files/СТС2.jpg')

        msg = await message.answer_photo(
            photo=photo,
            caption=
            f'✅ Фотография принята\n\n'
            f'Пришлите лицевую часть СТС:',
            reply_markup=custom_back_markup('start')
        )

        await state.set_state(UserBaseVerification.facial_sts)
        await state.update_data(
            msg=msg.message_id,
            photo_rights=photo_rights,
            fio=gpt_check
        )

    else:
        msg = await message.answer(
            'Ваше сообщение должно содержать фотографию.',
            reply_markup=custom_back_markup('start')
        )
        await state.update_data(msg=msg.message_id)
        return


@user_router.message(UserBaseVerification.facial_sts)
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
        facial_sts = base64.b64encode(file.read()).decode('utf-8')

        gpt_check = await get_response_gpt(
            base=facial_sts,
            content=check_sts_user
        )
        print(gpt_check)

        if gpt_check == '0':
            msg = await message.answer(
                'Не смогли разобрать номер и серию на Ваших документах, пришлите фотографию в лучшем качестве.',
                reply_markup=custom_back_markup('start')
            )
            await state.update_data(msg=msg.message_id)
            return

        photo = FSInputFile('files/СТС1.jpg')

        msg = await message.answer_photo(
            photo=photo,
            caption=
            f'✅ Фотография принята\n\n'
            f'Пришлите заднюю часть СТС:',
            reply_markup=custom_back_markup('start')
        )

        await state.set_state(UserBaseVerification.rear_sts)
        await state.update_data(
            msg=msg.message_id,
            photo_three=facial_sts,
            facial_sts=gpt_check
        )

    else:
        msg = await message.answer(
            'Ваше сообщение должно содержать фотографию.',
            reply_markup=custom_back_markup('start')
        )
        await state.update_data(msg=msg.message_id)
        return


@user_router.message(UserBaseVerification.rear_sts)
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
        rear_sts = base64.b64encode(file.read()).decode('utf-8')

        photo = FSInputFile('files/Фотопаспорт.jpg')

        msg = await message.answer_photo(
            photo=photo,
            caption=
            f'✅ Фотография принята\n\n'
            f'Пришлите фотографию прав в одном кадре рядом со своим лицом:',
            reply_markup=custom_back_markup('start')
        )

        await state.set_state(UserBaseVerification.rights_face)
        await state.update_data(
            msg=msg.message_id,
            rear_sts=rear_sts
        )

    else:
        msg = await message.answer(
            'Ваше сообщение должно содержать фотографию.',
            reply_markup=custom_back_markup('start')
        )
        await state.update_data(msg=msg.message_id)
        return


@user_router.message(UserBaseVerification.rights_face)
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
        rights_face = base64.b64encode(file.read()).decode('utf-8')

        photos = FSInputFile('files/MBF1.jpg')

        msg = await message.answer_photo(
            photo=photos,
            caption=
            f'Отправьте автомобиль с видом спереди',
            reply_markup=custom_back_markup('start')
        )

        await user.save()
        await state.update_data(
            msg=msg.message_id,
            rights_face=rights_face
        )
        await state.set_state(UserBaseVerification.auto_front)

    else:
        msg = await message.answer(
            'Ваше сообщение должно содержать фотографию.',
            reply_markup=custom_back_markup('start')
        )
        await state.update_data(msg=msg.message_id)
        return


@user_router.message(UserBaseVerification.auto_front)
async def select_front_photo(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    message_id = data['msg']
    with suppress(Exception):
        await bot.edit_message_reply_markup(
            chat_id=message.chat.id,
            message_id=message_id,
            reply_markup=None
        )

    if message.photo:
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
        file = await bot.download_file(file_info.file_path)
        photo_front = base64.b64encode(file.read()).decode('utf-8')

        gpt_check = await get_response_gpt(
            base=photo_front,
            content=check_auto_number
        )

        print(gpt_check)

        if gpt_check == '0':
            msg = await message.answer(
                'Не смогли разобрать номера на Вашем автомобиле, пришлите фотографию в лучшем качестве.'
            )
            await state.update_data(msg=msg.message_id)
            return

        file = FSInputFile('files/MBR2.jpg')

        msg = await message.answer_photo(
            photo=file,
            caption=
            f'✅ Фотография принята\n\n'
            f'Номера вашего автомобиля: <b>{gpt_check}</>\n\n'
            f'Пришлите фотографию автомобиля с правой стороны:',
            reply_markup=custom_back_markup('start')
        )

        await state.set_state(UserBaseVerification.auto_left)
        await state.update_data(
            msg=msg.message_id,
            photo_front=photo_front,
            auto_number=gpt_check
        )

    else:
        msg = await message.answer(
            'Ваше сообщение должно содержать фотографию.',
            reply_markup=custom_back_markup('start')
        )
        await state.update_data(msg=msg.message_id)
        return


@user_router.message(UserBaseVerification.auto_left)
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
        photo_left = base64.b64encode(file.read()).decode('utf-8')
        file = FSInputFile('files/MBR1.jpg')
        msg = await message.answer_photo(
            photo=file,
            caption=
            f'✅ Фотография принята\n\n'
            f'Пришлите фотографию автомобиля с левой стороны:',
            reply_markup=custom_back_markup('start')
        )

        await state.set_state(UserBaseVerification.auto_right)
        await state.update_data(
            msg=msg.message_id,
            photo_left=photo_left
        )

    else:
        msg = await message.answer(
            'Ваше сообщение должно содержать фотографию.',
            reply_markup=custom_back_markup('start')
        )
        await state.update_data(msg=msg.message_id)
        return


@user_router.message(UserBaseVerification.auto_right)
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

        file = FSInputFile('files/BMB1.jpg')

        msg = await message.answer_photo(
            photo=file,
            caption=
            f'✅ Фотография принята\n\n'
            f'Пришлите фотографию автомобиля сзади:',
            reply_markup=custom_back_markup('start')
        )

        await state.set_state(UserBaseVerification.auto_back)
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


@user_router.message(UserBaseVerification.auto_back)
async def select_back_photo(message: Message, state: FSMContext, bot: Bot, user: User):
    data = await state.get_data()
    message_id = data['msg']
    await bot.edit_message_reply_markup(
        chat_id=message.chat.id,
        message_id=message_id,
        reply_markup=None
    )

    if message.photo:

        markup = InlineKeyboardBuilder()
        markup.button(
            text='Подтвердить верификацию',
            callback_data=VerificarionAuto(action='open', identity=user.identity, result='okay')
        )
        markup.button(
            text='Отклонить верификацию',
            callback_data=VerificarionAuto(action='open', identity=user.identity, result='no')
        )

        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
        file = await bot.download_file(file_info.file_path)
        back_auto = base64.b64encode(file.read()).decode('utf-8')

        data = await state.get_data()

        photo_rights = data['photo_rights']
        photo_three = data['photo_three']
        facial_sts = data['facial_sts']
        rear_sts = data['rear_sts']
        rights_face = data['rights_face']
        photo_front = data['photo_front']
        auto_number = data['auto_number']
        photo_left = data['photo_left']
        photo_rigth = data['photo_rigth']

        user.base_verification.photo_rights = photo_rights
        user.base_verification.facial_sts = photo_three
        user.base_verification.rear_sts = rear_sts
        user.base_verification.rights_face = rights_face
        user.base_verification.auto_front = photo_front
        user.base_verification.auto_left = photo_left
        user.base_verification.auto_right = photo_rigth
        user.base_verification.auto_back = back_auto
        user.base_verification.auto_number = auto_number
        user.base_verification.sts_number = facial_sts
        user.fio = data['fio']

        await user.save()

        photo_1 = BufferedInputFile(base64.b64decode(user.base_verification.photo_rights), filename='1')
        photo_2 = BufferedInputFile(base64.b64decode(user.base_verification.facial_sts), filename='1')
        photo_3 = BufferedInputFile(base64.b64decode(user.base_verification.rear_sts), filename='1')
        photo_4 = BufferedInputFile(base64.b64decode(user.base_verification.rights_face), filename='1')
        photo_5 = BufferedInputFile(base64.b64decode(user.base_verification.auto_front), filename='1')
        photo_6 = BufferedInputFile(base64.b64decode(user.base_verification.auto_left), filename='1')
        photo_7 = BufferedInputFile(base64.b64decode(user.base_verification.auto_right), filename='1')
        photo_8 = BufferedInputFile(base64.b64decode(back_auto), filename='1')

        try:
            sts_data = json.loads(user.base_verification.sts_number)

            sts_info = (
                f"Марка: {sts_data.get('марка', '0')}\n"
                f"Модель: {sts_data.get('модель', '0')}\n"
                f"Цвет: {sts_data.get('цвет', '0')}\n"
                f"Гос номер: {sts_data.get('гос_номер', '0')}\n"
                f"Год выпуска: {sts_data.get('год_выпуска', '0')}\n"
                f"Серия: {sts_data.get('Серия', '0')}\n"
                f"Номер: {sts_data.get('Номер', '0')}"
            )
        except:
            sts_info = user.base_verification.sts_number

        media_group = [
            InputMediaPhoto(media=photo_1),
            InputMediaPhoto(media=photo_2),
            InputMediaPhoto(media=photo_3),
            InputMediaPhoto(media=photo_4),
            InputMediaPhoto(media=photo_5),
            InputMediaPhoto(media=photo_6),
            InputMediaPhoto(media=photo_7),
            InputMediaPhoto(media=photo_8)
        ]

        await bot.send_media_group(
            chat_id=-1002233300548,
            message_thread_id=4,
            media=media_group
        )
        await bot.send_message(
            text=f'Username: <b>@{user.username}</>\n'
                 f'Номер телефона: {user.number}\n'
                 f'ФИО: <b>{user.fio}</>\n'
                 f'<b>Данные СТС</>:\n{sts_info}',
            chat_id=-1002233300548,
            message_thread_id=4,
            reply_markup=markup.adjust(1).as_markup()
        )

        await message.answer(
            f'✅ Ваши фотографии документов успешно отправлена на модерацию администрации.\n\n'
            f'Ожидайте уведомления о результате проверки.',
            reply_markup=custom_back_markup('start')
        )

        user.active_doc = VerifType.waiting
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

        kb.button(
            text='✅', callback_data='pass'
        )

        await bot.edit_message_reply_markup(
            chat_id=-1002233300548,
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
                 'Стоимость подключения к группе: 1000 рублей.\n\n'
                 'Если у вас не проходит оплата по кнопке, используется ссылку ⬇️\n'
                 f'{url}',
            reply_markup=markup.adjust(1).as_markup()
        )

        user.verification.verification_base = True
        user.active_doc = VerifType.yes
        await user.save()
    else:
        kb.button(
            text='✅', callback_data='pass'
        )
        await bot.edit_message_reply_markup(
            chat_id=-1002233300548,
            message_id=call.message.message_id,
            reply_markup=kb.as_markup()
        )

        markup.button(
            text='Узнать почему', url='t.me/transfermezhgorod'
        )
        await bot.send_message(
            chat_id=user.user_id,
            text='Ваши документы не прошли проверку.',
            reply_markup=markup.adjust(1).as_markup()
        )
        user.active_doc = VerifType.no
        await user.save()
