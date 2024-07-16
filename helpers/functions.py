from contextlib import suppress
from datetime import datetime
from typing import Union

from aiogram import Bot
from aiogram.enums import ContentType
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message, InputMediaPhoto, InputMediaVideo, FSInputFile
from openai import OpenAI

from data.context_vars import bot_session
from database import Order
from database.models import User
from utils.yookassa.api import payment


def russian_plural(n, forms):
    """
    Возвращает форму слова в зависимости от числа n.

    :param n: Число, в соответствии с которым выбирается форма
    :param forms: кортеж из трех форм слова (например, для слова 'яблоко': ('яблоко', 'яблока', 'яблок'))
    """
    if n % 10 == 1 and n % 100 != 11:
        return forms[0]
    elif 2 <= n % 10 <= 4 and (n % 100 < 10 or n % 100 >= 20):
        return forms[1]
    else:
        return forms[2]


async def edit_send_media(
        event: Union[CallbackQuery, Message],
        text: str,
        bot: Bot = bot_session.get('current_session'),
        reply_markup=None,
        media: dict = None,
        need_edit: bool = True
):
    bot: Bot = bot_session.get('current_session')
    message = event.message if isinstance(event, CallbackQuery) else event
    message_id = message.message_id
    chat_id = message.chat.id

    # Check if the message has media and if the sender is a bot
    have_media = message.video or message.photo or message.document
    is_bot = message.from_user.is_bot if message.from_user else True

    kwargs = {'reply_markup': reply_markup}

    if media is not None:
        send_method = message.answer_photo if media['type'] == ContentType.PHOTO else message.answer_video
        if have_media and is_bot:
            media_type = InputMediaPhoto if media['type'] == ContentType.PHOTO else InputMediaVideo
            with suppress(Exception):
                if need_edit:
                    return await bot.edit_message_media(
                        chat_id=chat_id,
                        message_id=message_id,
                        media=media_type(media=media['file_id'], caption=text),
                        reply_markup=reply_markup
                    )
                else:
                    return await send_method(
                        chat_id=chat_id,
                        media=media_type(media=media['file_id'], caption=text),
                        reply_markup=reply_markup
                    )
        else:
            if is_bot:
                await message.delete()
            try:
                return await send_method(media['file_id'], caption=text, **kwargs)
            except Exception:
                try:
                    file_extension = media['file_id'].split('.')[-1]
                    return await send_method(
                        media=FSInputFile(path=media['file_id'], filename=f"file.{file_extension}"),
                        caption=text, **kwargs
                    )
                except:
                    return await message.answer(text=text, **kwargs)

    else:
        kwargs['disable_web_page_preview'] = True
        if is_bot and not have_media:
            if need_edit:
                try:
                    return await message.edit_text(text=text, **kwargs)
                except TelegramBadRequest as error:
                    if error.message == 'Bad Request: message is not modified: specified new message content and reply markup are exactly the same as a current content and reply markup of the message':
                        return
                    else:
                        return await message.answer(text=text, **kwargs)
            else:
                return await message.answer(text=text, **kwargs)
        else:
            if have_media and is_bot:
                await message.delete()
            return await message.answer(text=text, **kwargs)


client = OpenAI(api_key="sk-proj-mxflsLySKuKrimvaPf3FT3BlbkFJyJ7KzjmCUbweZdJJm95a")


async def get_chat_response(prompt, information):
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system",
             "content": information},
            {"role": "user", "content": prompt},
        ]
    )
    content = response.choices[0].message.content
    return content


async def create_payment_link(user):
    payment_data = await payment(amount=1000)
    url = payment_data.confirmation.confirmation_url

    await Order(
        user=user.id,
        identy=payment_data.id,
        amount=1000
    ).insert()

    return url
