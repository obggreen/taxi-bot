from aiogram import Router, F

from filters.access_filter import AdminFilter, BlockedFilter

user_router = Router()
admin_router = Router()

admin_router.message.filter(AdminFilter(), F.chat.type.in_(["private"]))
admin_router.callback_query.filter(AdminFilter(), F.message.chat.type.in_(["private"]))

user_router.message.filter(F.chat.type.in_(["private", "group", "supergroup"]), BlockedFilter())
user_router.callback_query.filter(F.message.chat.type.in_(["private", "group", "supergroup"]), BlockedFilter())
