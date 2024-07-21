import pytz
from aiogram import F, Bot
from aiogram.client.session import aiohttp
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery

from database.models import User
from handlers.routers import user_router
from helpers.keyboards.markups import custom_back_markup


class SelectGPSUSer(StatesGroup):
    location = State()


async def reverse_geocode(latitude, longitude):
    url = f'https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat={latitude}&lon={longitude}'
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                address_components = data.get('address', {})

                street = address_components.get('road', 'Не указано')
                suburb = address_components.get('suburb', 'Не указано')
                district = address_components.get('city_district', 'Не указано')
                city = address_components.get('city', 'Не указано')
                state = address_components.get('state', 'Не указано')

                formatted_address = (
                    f"Улица: {street}\n"
                    f"Район: {suburb}\n"
                    f"Округ: {district}\n"
                    f"Город: {city}\n"
                    f"Область: {state}"
                )

                return formatted_address
            else:
                return 'Ошибка при получении данных'


@user_router.callback_query(F.data == 'call_geoposition')
async def select_call_opposition(call: CallbackQuery, state: FSMContext):
    await call.message.edit_text(
        'Что бы поделиться своим местоположением, <b>следуйте инструкции ниже:</>\n\n'
        '<b>1.</> Нажмите на скрепку в углу экрана.\n'
        '<b>2.</> Выберите пункт <b>"геопозиция"</>\n'
        '<b>3.</> Используйте "Транслировать геопозицию"\n'
        '<b>4.</> Время ограничения <b>"Пока не отключу"</>\n\n'
        '<b>📍Поделитесь своей геопозицией:</>',
        reply_markup=custom_back_markup('start')
    )
    await state.set_state(SelectGPSUSer.location)


@user_router.message(SelectGPSUSer.location)
async def select_location(message: Message, state: FSMContext, user: User):
    moscow_tz = pytz.timezone('Europe/Moscow')
    if message.location and message.location.live_period:
        latitude = message.location.latitude
        longitude = message.location.longitude
        live_period = message.location.live_period

        print(f"Обновлена живая геолокация: Широта: {latitude}, Долгота: {longitude}, Период: {live_period}")

        if live_period < 214748364:
            await message.answer(
                '❗️Вы поделились геопозицией на <b>ограниченный период времени</>, пожалуйста, поделитесь геопозицией на '
                'не ограниченный срок:'
            )
            return

        address = await reverse_geocode(latitude, longitude)

        user.geo_message_id = message.message_id
        user.gps.latitude = latitude
        user.gps.longitude = longitude
        user.gps.live_period = live_period
        user.gps.last_location_update = datetime.now(moscow_tz)
        await message.answer(
            f'<b>📍Ваша геопозиция обнаружена успешно!</>\n\n'
            f'Вы находитесь по адресу:\n{address}'
        )
        await user.save()
        await state.clear()
    else:
        await message.answer(
            'Ваше сообщение не содержит геолокации, либо вы поделились не текущим местоположением!\n'
            'Повторите свою попытку:'
        )
        return


from datetime import datetime, time


async def check_location(bot: Bot):
    moscow_tz = pytz.timezone('Europe/Moscow')
    current_time = datetime.now(moscow_tz).time()
    start_time = time(0, 0)  # 12 AM по МСК
    end_time = time(20, 0)  # 11 PM по МСК

    if start_time <= current_time <= end_time:
        for user in await User.find_all().to_list():
            if user.geo_message_id and user.gps.latitude and user.gps.longitude:
                # Проверяем, изменились ли координаты
                latitude = user.gps.latitude
                longitude = user.gps.longitude

                current_location = await bot.forward_message(
                    from_chat_id=user.user_id,
                    message_id=user.geo_message_id,
                    chat_id=user.user_id
                )

                if current_location.location:
                    current_latitude = current_location.location.latitude
                    current_longitude = current_location.location.longitude

                    if latitude == current_latitude and longitude == current_longitude:
                        print(f"Пользователь @{user.username} отключил LIVE режим или не изменил местоположение")
                        continue

                    user.gps.latitude = current_latitude
                    user.gps.longitude = current_longitude
                    user.gps.last_location_update = datetime.now(moscow_tz)
                    await user.save()

                    address = await reverse_geocode(current_latitude, current_longitude)
                    await bot.send_message(
                        chat_id=-1002210540953,
                        message_thread_id=274,
                        text=f'<b>Водитель:</> @{user.username}\n\n'
                             f'<b>Местоположение:</>\n'
                             f'{address}'
                    )
                else:
                    print(f"Пользователь @{user.username} не передал геолокацию")
    else:
        print("Проверка геолокации не выполняется с 11 ночи до 12 утра по МСК")


