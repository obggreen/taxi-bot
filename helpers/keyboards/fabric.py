from aiogram.utils.keyboard import CallbackData


class SelectLanguageCallback(CallbackData, prefix='language'):
    language: str
