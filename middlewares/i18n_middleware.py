from aiogram.utils.i18n.middleware import I18nMiddleware
from aiogram import types

from database.models import User

from typing import Union, Dict, Any


async def get_lang(user: Union[User, None]):
    if user:
        return user.settings.language
    else:
        return 'ru'


class ACLMiddleware(I18nMiddleware):
    async def get_locale(
            self,
            event: types.TelegramObject,
            data: Dict[str, Any]
    ):
        user = await User.find_one(User.user_id == data['event_from_user'].id)
        if user:
            return user.settings.language
        else:
            return 'en' if data['event_from_user'].language_code == 'en' else 'ru'
