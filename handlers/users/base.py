import base64
import io
from contextlib import suppress
from typing import Union

from aiogram import F, Bot
from aiogram.client.session import aiohttp
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram.filters.chat_member_updated import ChatMemberUpdatedFilter, MEMBER, KICKED
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery, ChatMemberUpdated, BufferedInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from docx import Document as DocxDocument

from database import Tariff
from database.models import User
from database.models.users import DocumentType, VerifType
from handlers.routers import user_router
from helpers.functions import make_tellcode_call
from helpers.keyboards.markups import default_markup, custom_back_markup


class SelectTariff(CallbackData, prefix='tariff'):
    action: str
    identity: int


class SelectVerificationType(CallbackData, prefix='ver'):
    action: str
    verif: str


class PhoneState(StatesGroup):
    waiting_for_phone = State()
    waiting_for_sms = State()


@user_router.callback_query(F.data == 'start')
@user_router.message(Command(commands='start'))
async def start_command(event: Union[Message, CallbackQuery], state: FSMContext, user: User, bot: Bot):
    await state.clear()

    if isinstance(event, Message):
        answer = event.answer
    else:
        await event.message.delete()
        answer = event.message.answer

    # duplicates, sts_duplicates = await find_duplicate_numbers()
    # duplicate_message = await format_duplicate_message(duplicates, sts_duplicates)
    #
    # if duplicate_message:
    #     file = FSInputFile('files/wairning.jpg')
    #
    #     await bot.send_photo(
    #         photo=file,
    #         chat_id=-1002210540953,
    #         message_thread_id=4
    #     )
    #
    #     await bot.send_message(
    #         text=duplicate_message,
    #         chat_id=-1002210540953,
    #         message_thread_id=4
    #     )

    if user:
        if user.number is None:

            markup = ReplyKeyboardBuilder()
            markup.button(text='📞 Поделиться номером', request_contact=True)

            await answer(
                'Добро пожаловать в группу Свободные Заказы | Межгород!\n'
                'Для работы с нами подтвердите свой номер телефона.',
                reply_markup=markup.as_markup(resize_keyboard=True)
            )

            await state.set_state(PhoneState.waiting_for_phone)
        else:
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

                await answer(
                    'Рады вас приветствовать в <b>Свободные Заказы | Межгород!</>',
                    reply_markup=default_markup()
                )

                if not user.verification.verification_user:
                    if user.active_doc == VerifType.no:
                        markup.button(
                            text='📃 Верификация документов',
                            callback_data=SelectVerificationType(action='open', verif='document')
                        )

                if not user.verification.verification_auto:
                    if user.active_auto == VerifType.no:
                        markup.button(
                            text='📃 Верификация автомобиля',
                            callback_data=SelectVerificationType(action='open', verif='auto')
                        )

                await answer(
                    '<i>Для получения заказов необходимо пройти проверку Вашей '
                    'личности, Вашего автомобиля, водительского удостоверения, технического паспорта автомобиля.</>',
                    reply_markup=markup.adjust(1).as_markup()
                )

                # if not user.geo_message_id:
                #     key = InlineKeyboardBuilder()
                #
                #     key.button(
                #         text='📍Поделиться геопозицией',
                #         callback_data='call_geoposition'
                #     )
                #
                #     await answer(
                #         'Для повышение приоритета выдачи заказов, вы можете поделиться своим местоположение, что бы операторы '
                #         'видели вас около заказа и могли вам выдать ближайший!',
                #         reply_markup=key.as_markup()
                #     )


    else:
        await answer(
            'Добро пожаловать в бота!',
            reply_markup=default_markup()
        )


@user_router.message(PhoneState.waiting_for_phone)
async def select_user_phone(message: Message, state: FSMContext, user: User, bot: Bot):
    if message.contact:
        contact = message.contact

        if contact:
            original_number = contact.phone_number

            corrected_number = original_number.replace('7', '8', 1)

            user.number = corrected_number

            call_user = await make_tellcode_call(contact.phone_number)
            if call_user:
                msg = await message.answer(
                    'Сейчас вам позвонят и продиктуют 4-х значный код, введите его в ответ на это сообщение:',
                    reply_markup=custom_back_markup('start')
                )
                await state.set_state(PhoneState.waiting_for_sms)
                await state.update_data(code=call_user, number=corrected_number, msg=msg.message_id)
            else:
                msg = await message.answer(
                    'Произошла ошибка при отправке кода на ваш номер, попробуйте еще раз '
                    'или свяжитесь с администратором!',
                    reply_markup=custom_back_markup('start')
                )
                await state.update_data(msg=msg.message_id)
                return
        else:
            msg = await message.answer(
                'Не получилось получить номер, попробуйте еще раз или свяжитесь с администратором',
                reply_markup=custom_back_markup('start')
            )
            await state.update_data(msg=msg.message_id)
            return
    else:
        msg = await message.answer(
            'Сообщение не содержит телефона или вы поделились телефоном не через кнопку.',
            reply_markup=custom_back_markup('start')
        )
        await state.update_data(msg=msg.message_id)
        return

@user_router.message(PhoneState.waiting_for_sms)
async def select_user_phone(message: Message, state: FSMContext, user: User, bot: Bot):
    data = await state.get_data()
    number = data['number']
    code = data['code']
    message_id = data['msg']

    await bot.edit_message_reply_markup(
        chat_id=message.chat.id,
        message_id=message_id,
        reply_markup=None
    )

    if message.text == code:
        markup = InlineKeyboardBuilder()
        user.number = number
        await user.save()
        await message.answer(
            'Код успешно введен, ваш номер верифицирован в системе!',
            reply_markup=default_markup()
        )

        if not user.verification.verification_user:
            if user.active_doc == VerifType.no:
                markup.button(
                    text='📃 Верификация документов',
                    callback_data=SelectVerificationType(action='open', verif='document')
                )

        if not user.verification.verification_auto:
            if user.active_auto == VerifType.no:
                markup.button(
                    text='📃 Верификация автомобиля',
                    callback_data=SelectVerificationType(action='open', verif='auto')
                )

        await message.answer(
            '<i>Для получения заказов необходимо пройти проверку Вашей '
            'личности, Вашего автомобиля, водительского удостоверения, технического паспорта автомобиля.</>',
            reply_markup=markup.adjust(1).as_markup()
        )

        if user.verification.verification_auto:
            await message.answer(
                'тут покупка'
            )

        await state.clear()
    else:
        msg = await message.answer(
            'Код введен не верно, попробуйте еще раз:',
            reply_markup=custom_back_markup('start')
        )
        await state.update_data(msg=msg.message_id)
        return



# def add_image_if_base64(doc, title, base64_str):
#     if base64_str:
#         try:
#             image_data = base64.b64decode(base64_str)
#             image_stream = io.BytesIO(image_data)
#             doc.add_heading(title, level=2)
#             doc.add_picture(image_stream)
#         except Exception as e:
#             pass
#
#
# def generate_user_report_in_memory(user: User):
#     doc = DocxDocument()
#
#     doc.add_heading(f'Досье на пользователя {user.full_name}', 0)
#
#     doc.add_heading('Основная информация', level=1)
#     doc.add_paragraph(f'Полное имя: {user.full_name}')
#     doc.add_paragraph(f'Имя пользователя: {user.username}')
#     doc.add_paragraph(f'Роль: {user.role}')
#     doc.add_paragraph(f'Дата регистрации: {user.registration_date.strftime("%Y-%m-%d %H:%M:%S")}')
#     doc.add_paragraph(
#         f'Последняя активность: {user.last_active.strftime("%Y-%m-%d %H:%M:%S") if user.last_active else "N/A"}')
#
#     doc.add_heading('Верификация', level=1)
#     doc.add_paragraph(f'Верификация на автомобиль: {"Да" if user.verification.verification_auto else "Нет"}')
#     doc.add_paragraph(f'Верификация на документы: {"Да" if user.verification.verification_user else "Нет"}')
#
#     doc.add_heading('Настройки', level=1)
#     doc.add_paragraph(f'Язык: {user.settings.language}')
#
#     doc.add_heading('Финансовая информация', level=1)
#     doc.add_paragraph(f'Баланс: {user.balance} руб.')
#     doc.add_paragraph(f'Подписка: {user.subscription if user.subscription else "Нет"}')
#
#     doc.add_heading('Информация об автомобиле', level=1)
#     doc.add_paragraph(f'Номера автомобиля: {user.photo_auto_documents.auto_number}')
#     add_image_if_base64(doc, 'Перед автомобиля', user.photo_auto_documents.auto_front)
#     add_image_if_base64(doc, 'Левая сторона автомобиля', user.photo_auto_documents.auto_left)
#     add_image_if_base64(doc, 'Правая сторона автомобиля', user.photo_auto_documents.auto_right)
#     add_image_if_base64(doc, 'Зад автомобиля', user.photo_auto_documents.auto_back)
#     add_image_if_base64(doc, 'Салон спереди', user.photo_auto_documents.salon_front)
#     add_image_if_base64(doc, 'Зад салона', user.photo_auto_documents.salon_back)
#
#     byte_stream = io.BytesIO()
#     doc.save(byte_stream)
#     byte_stream.seek(0)
#
#     return byte_stream


# @user_router.message(Command(commands='test'))
# async def test(message: Message, user: User):
#     byte_stream = generate_user_report_in_memory(user)
#
#     # Создание BufferedInputFile для отправки файла
#     document = BufferedInputFile(byte_stream.read(), filename=f'user_report_{user.user_id}.docx')
#
#     # Отправка документа пользователю
#     await message.answer_document(document)


async def reverse_geocode(latitude, longitude):
    url = f'https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat={latitude}&lon={longitude}'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                address = data.get('display_name', 'Местоположение не найдено')
                return address
            else:
                return 'Ошибка при получении данных'


class Test(StatesGroup):
    test = State()


@user_router.message(Command(commands='geo'))
async def testing(message: Message, state: FSMContext):
    await message.answer('Пришлите геопозицию')

    await state.set_state(Test.test)


@user_router.message(Test.test)
async def tests(message: Message, state: FSMContext, user: User):
    if message.location and message.location.live_period:
        latitude = message.location.latitude
        longitude = message.location.longitude
        timestamp = message.date.strftime("%Y-%m-%d %H:%M:%S")
        data = await state.get_data()
        previous_location = data.get('previous_location')
        address = await reverse_geocode(latitude, longitude)
        if previous_location:
            prev_latitude, prev_longitude = previous_location
            if prev_latitude != latitude or prev_longitude != longitude:
                await message.reply(f'Ваше местоположение обновлено: Широта {latitude}, Долгота {longitude}\n'
                                    f'Адрес: {address}\n'
                                    f'Время обновления: {timestamp}')
            else:
                await message.reply(f'Ваше местоположение не изменилось: Широта {latitude}, Долгота {longitude}\n'
                                    f'Адрес: {address}\n'
                                    f'Время обновления: {timestamp}')
        else:
            await message.reply(f'Ваше местоположение получено: Широта {latitude}, Долгота {longitude}\n'
                                f'Адрес: {address}\n'
                                f'Время обновления: {timestamp}')

        user.geo_message_id = message.message_id
        await user.save()

    else:
        await message.reply('Пожалуйста, отправьте свою **живую** геопозицию, а не выбранное место.')


# async def check_location(bot: Bot):
#     async with aiohttp.ClientSession() as session:
#         for user in await User.find_all().to_list():
#             if user.geo_message_id:
#                 message = await bot.forward_message(from_chat_id=user.user_id, message_id=user.geo_message_id,
#                                                     chat_id=user.user_id)
#                 latitude = message.location.latitude
#                 longitude = message.location.longitude
#                 address = await reverse_geocode(latitude, longitude)
#                 await bot.send_message(user.user_id, f'Вы сейчас находитесь по адресу: {address}')


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
