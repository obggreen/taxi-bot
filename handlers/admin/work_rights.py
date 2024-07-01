from aiogram import html, F, types, Bot
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database import User, Order
from database.models.users import DocumentType
from handlers.admin.base import AdminCallback
from handlers.routers import admin_router
from helpers.keyboards.markups import custom_back_markup
from utils.yookassa.api import payment


class SelectUser(StatesGroup):
    user = State()


@admin_router.callback_query(AdminCallback.filter(F.action == 'block_user'))
async def block_user(call: CallbackQuery, callback_data: AdminCallback, state: FSMContext):
    msg = await call.message.edit_text(
        'Введите ID пользователя, username или ФИО:',
        reply_markup=custom_back_markup('start')
    )
    await state.set_state(SelectUser.user)
    await state.update_data(msg=msg.message_id, typ=callback_data.types)


@admin_router.message(SelectUser.user)
async def lock_unlock_user(message: Message, state: FSMContext, bot: Bot):
    markup = InlineKeyboardBuilder()
    data = await state.get_data()
    info = data['typ']
    input_data = message.text.strip()

    if input_data.isdigit():
        user = await User.find_one(User.user_id == int(input_data))
    else:
        user = await User.find_one(User.username == input_data)
        if not user:
            user = await User.find_one(User.fio == input_data)

    if info == 'block':
        payment_data = await payment(amount=999.999)
        url = payment_data.confirmation.confirmation_url
        markup.button(
            text='Купить разблокировку', web_app=types.WebAppInfo(url=url)
        )
        if user:
            delete = await bot.ban_chat_member(
                chat_id=-1002210540953,
                user_id=user.user_id
            )
            if delete:
                await message.answer(f"Пользователь: {user.full_name} заблокирован")
                await bot.send_message(
                    chat_id=user.user_id,
                    text='Администратор забрал у вас права участника и выдал блокировку.',
                    reply_markup=markup.adjust(1).as_markup()
                )
                user.documents = DocumentType.untested
                await Order(
                    user=user.id,
                    identy=payment_data.id,
                    amount=999.99,
                    description='block'
                ).insert()

                await user.save()
                await state.clear()
            else:
                await message.answer('Пользователь был найден, но произошла ошибка при блокировке.\n'
                                     'Возможно он уже не является участником группы.')
                await state.clear()
        else:
            await message.answer("Пользователь не найден. Попробуйте снова.")
            await state.clear()
    else:
        if user:
            delete = await bot.unban_chat_member(
                chat_id=-1002210540953,
                user_id=user.user_id
            )
            if delete:
                await message.answer(f"Пользователь: {user.full_name} разблокирован")
                await bot.send_message(
                    chat_id=user.user_id,
                    text='Администратор забрал у вас права участника и выдал блокировку.'
                )
                user.documents = DocumentType.untested
                await user.save()
            else:
                await message.answer('Пользователь был найден, но произошла ошибка при блокировке.\n'
                                     'Возможно он уже не является участником группы.')
                await state.clear()
        else:
            await message.answer("Пользователь не найден. Попробуйте снова.")
            await state.clear()