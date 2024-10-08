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
from aiogram.types import Message, CallbackQuery, ChatMemberUpdated, BufferedInputFile, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from babel.numbers import format_currency
from docx import Document as DocxDocument

from database import Tariff
from database.models import User
from database.models.users import DocumentType, VerifType
from handlers.routers import user_router
from helpers.functions import make_tellcode_call, create_payment_link
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


# @user_router.message(Command(commands='start'))
# async def ykassa(message: Message, user: User):
#     url = await create_payment_link(user)
#     markup = InlineKeyboardBuilder()
#     markup.button(
#         text='Оплатить 1000 ₽', web_app=WebAppInfo(url=url)
#     )
#
#     await message.answer(
#         'Работа для водителей такси, междугородние поездки по всей России.',
#         reply_markup=markup.as_markup()
#     )


@user_router.callback_query(F.data == 'start')
@user_router.message(Command(commands='start'))
async def start_command(event: Union[Message, CallbackQuery], state: FSMContext, user: User, bot: Bot):
    await state.clear()

    if isinstance(event, Message):
        answer = event.answer
    else:
        await event.message.delete()
        answer = event.message.answer

    if user:
        if user.number is None:

            markup = ReplyKeyboardBuilder()
            markup.button(text='📞 Поделиться номером', request_contact=True)

            await answer(
                'RuWays - Работа, для водителей такси, о которой можно было только мечтать 🤭\n'
                'Для работы с нами подтвердите свой номер телефона.',
                reply_markup=markup.as_markup(resize_keyboard=True)
            )

            await state.set_state(PhoneState.waiting_for_phone)
        else:
            if user.verification.verification_base:
                markup = InlineKeyboardBuilder()

                url = await create_payment_link(user)

                markup.button(
                    text='Оплатить 1000 ₽', web_app=WebAppInfo(url=url)
                )

                await answer(
                    'Ваш профиль верифицирован, вы можете приобрести вход в группу:  ⤵️',
                    reply_markup=markup.adjust(1).as_markup()
                )
            else:
                markup = InlineKeyboardBuilder()

                await answer(
                    '<b>RuWays - Работа, для водителей такси, о которой можно было только мечтать 🤭</>',
                    reply_markup=default_markup()
                )

                if not user.verification.verification_base:
                    if user.active_doc == VerifType.no:
                        markup.button(
                            text='📃 Пройти верификацию',
                            callback_data='base_verification'
                        )

                    await answer(
                        'Для получения доступа к сервису RuWays I Driver необходимо пройти проверку Вашей личности, '
                        'Вашего автомобиля, водительского удостоверения, технического паспорта. Для '
                        'продолжения верификации следуйте дальнейшим подсказкам бота',
                        reply_markup=markup.adjust(1).as_markup()
                    )

                if user.active_doc == VerifType.waiting:
                    await answer(
                        'Ваши данные находятся на проверке, пожалуйста, ожидайте!',
                        reply_markup=markup.adjust(1).as_markup()
                    )



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
                    'Сейчас Вам позвонит робот и продиктуют 4-х значный код, введите его в ответ на это сообщение.',
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

        if not user.verification.verification_base:
            if user.active_doc == VerifType.no:
                markup.button(
                    text='📃 Пройти верификацию',
                    callback_data='base_verification'
                )

        await message.answer(
            'Для получения доступа к сервису RuWays I Driver необходимо пройти проверку Вашей личности, '
            'Вашего автомобиля, водительского удостоверения, технического паспорта. Для '
            'продолжения верификации следуйте дальнейшим подсказкам бота.',
            reply_markup=markup.adjust(1).as_markup()
        )

        if user.verification.verification_base:
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



@user_router.message(F.text == '💳 Приобрести доступ')
async def select_dostup_monet(message: Message, user: User):

    if user.verification.verification_user or user.verification.verification_auto:
        markup = InlineKeyboardBuilder()
        url = await create_payment_link(user)

        markup.button(
            text='Оплатить 1000 ₽', web_app=WebAppInfo(url=url)
        )

        await message.answer(
            f'У вас успешно пройдена верификация, оплатите {format_currency(1000, "RUB")}\n\n'
            f'Если у вас не проходит оплата по кнопке, оплатите по ссылке: {url}',
            reply_markup=markup.adjust(1).as_markup()
        )
    elif user.active_doc == VerifType.waiting or user.active_auto == VerifType.waiting:
        await message.answer(
            'Ваши заявки на модерации, подождите их одобрения',
            reply_markup=custom_back_markup('start')
        )
    else:
        markup = InlineKeyboardBuilder()

        if not user.verification.verification_user:
            if user.active_doc == VerifType.no:
                markup.button(
                    text='📃 Верификация документов',
                    callback_data=SelectVerificationType(action='open', verif='document')
                )

        if user.verification.verification_user:
            if not user.verification.verification_auto:
                    markup.button(
                        text='📃 Верификация автомобиля',
                        callback_data=SelectVerificationType(action='open', verif='auto')
                    )


        await message.answer(
            'Для входа в группу вам нужно пройти верификацию',
            reply_markup=markup.adjust(1).as_markup()
        )



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
