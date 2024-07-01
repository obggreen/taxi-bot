import json
from typing import List, Dict, Optional, Tuple
from collections import defaultdict

from aiogram import Bot
from aiogram.types import FSInputFile
from beanie import PydanticObjectId
import asyncio
from database import User


async def find_duplicate_numbers() -> Tuple[Dict[str, List[int]], Dict[str, List[int]]]:
    number_to_users: Dict[str, List[int]] = defaultdict(list)
    sts_number_to_users: Dict[str, List[int]] = defaultdict(list)

    async for user in User.find_all():
        if not user.verification.verification_auto or not user.verification.verification_user:
            continue

        auto_number = user.photo_auto_documents.auto_number
        if auto_number:
            number_to_users[auto_number].append(user.user_id)

        if user.photo_user_documents.sts_number:
            try:
                sts_data = json.loads(user.photo_user_documents.sts_number)
                sts_auto_number = sts_data.get("гос_номер")
                sts_number = str(sts_data.get("Номер"))
                if sts_auto_number:
                    number_to_users[sts_auto_number].append(user.user_id)
                if sts_number:
                    sts_number_to_users[sts_number].append(user.user_id)
            except json.JSONDecodeError:
                print(f"Ошибка декодирования JSON для пользователя {user.user_id}")

    duplicates = {number: user_ids for number, user_ids in number_to_users.items() if len(user_ids) > 1}
    sts_duplicates = {number: user_ids for number, user_ids in sts_number_to_users.items() if len(user_ids) > 1}

    return duplicates, sts_duplicates


async def get_user_by_id(user_id: int) -> Optional[User]:
    return await User.find_one(User.user_id == user_id)


async def format_duplicate_message(duplicates: Dict[str, List[int]], sts_duplicates: Dict[str, List[int]]) -> str:
    messages = []

    def get_car_info(sts_data: dict) -> str:
        return (
            f"Марка: {sts_data.get('марка', 'Не указано')}\n"
            f"Модель: {sts_data.get('модель', 'Не указано')}\n"
            f"Цвет: {sts_data.get('цвет', 'Не указано')}\n"
            f"Гос номер: {sts_data.get('гос_номер', 'Не указано')}\n"
            f"Год выпуска: {sts_data.get('год_выпуска', 'Не указано')}\n"
            f"Серия: {sts_data.get('Серия', 'Не указано')}\n"
            f"Номер: {sts_data.get('Номер', 'Не указано')}\n"
        )

    for number, user_ids in duplicates.items():
        user_info = []
        for user_id in user_ids:
            user = await get_user_by_id(user_id)
            if user:
                fio = user.fio or 'ФИО пользователя не найдено'
                user_number = user.number or 'Номера нету'
                username = user.username or f"user_id: {user.user_id}"
                sts_data = json.loads(user.photo_user_documents.sts_number) if user.photo_user_documents.sts_number else {}
                car_info = get_car_info(sts_data)
                user_info.append(f"<b>@{username}</b>:\n"
                                 f"{car_info}\n"
                                 f"ФИО: {fio}\n"
                                 f"Номер: {user_number}")

        if user_info:
            messages.append(f"<b>⚠️ Найден дубликат пользователей с гос номером {number}:</b>\n" + "\n".join(user_info))

    for number, user_ids in sts_duplicates.items():
        user_info = []
        for user_id in user_ids:
            user = await get_user_by_id(user_id)
            if user:
                fio = user.fio or 'ФИО пользователя не найдено'
                user_number = user.number or 'Номера нету'
                username = user.username or f"user_id: {user.user_id}"
                sts_data = json.loads(user.photo_user_documents.sts_number) if user.photo_user_documents.sts_number else {}
                car_info = get_car_info(sts_data)
                user_info.append(f"<b>@{username}</b>:\n"
                                 f"{car_info}\n"
                                 f"ФИО: {fio}\n"
                                 f"Номер: {user_number}\n")

        if user_info:
            messages.append(f"<b>⚠️ Найден дубликат пользователей с номером СТС {number}:</b>\n" + "\n".join(user_info))

    return "\n\n".join(messages)


async def monitoring(bot: Bot):
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
