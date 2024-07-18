from datetime import datetime, timedelta

from aiogram import F, Bot
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import CallbackQuery, ChatPermissions

from database import User
from database.models.users import DocumentType
from handlers.admin.base import AdminCallback
from handlers.routers import admin_router


class SelectUser(StatesGroup):
    user = State()


@admin_router.callback_query(AdminCallback.filter(F.action == 'user_private'))
async def lock_unlock_user(call: CallbackQuery, callback_data: AdminCallback, bot: Bot):
    info = callback_data.types
    user = await User.find_one(User.user_id == callback_data.user_id)

    if info == 'ban':
        if user:
            try:
                until_date = datetime.now() + timedelta(hours=24)  # Время мьюта, например, 24 часа
                restrict = await bot.restrict_chat_member(
                    chat_id=-1002233906745,
                    user_id=user.user_id,
                    permissions=ChatPermissions(can_send_messages=False),
                    until_date=until_date
                )
                if restrict:
                    await call.message.edit_text(f"Пользователь: {user.full_name} получил временный мьют на 24 часа")
                    await bot.send_message(
                        chat_id=user.user_id,
                        text='Администратор временно ограничил ваши права в чате на 24 часа.'
                    )
                    user.documents = DocumentType.untested
                    user.settings.blocked = 'yes'
                    await user.save()
            except Exception as e:
                print(e)
                await call.answer('Произошла ошибка!')
        else:
            await call.message.edit_text("Пользователь не найден. Попробуйте снова.")
    else:
        if user:
            try:
                unrestrict = await bot.restrict_chat_member(
                    chat_id=-1002196208498,
                    user_id=user.user_id,
                    permissions=ChatPermissions(
                        can_send_messages=True
                    )
                )
                if unrestrict:
                    await call.message.edit_text(f"Пользователь: {user.full_name} восстановлен в правах")
                    await bot.send_message(
                        chat_id=user.user_id,
                        text='Администратор восстановил ваши права в чате.'
                    )
                    user.documents = DocumentType.untested
                    user.settings.blocked = 'no'
                    await user.save()
            except Exception as e:
                print(e)
                await call.answer('Произошла ошибка!')
        else:
            await call.message.edit_text("Пользователь не найден. Попробуйте снова.")
