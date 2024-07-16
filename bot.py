import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.types import FSInputFile
from aiogram.utils.i18n import I18n
from aiogram.utils.keyboard import InlineKeyboardBuilder
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger
from redis.asyncio import Redis

import database
from data.context_vars import bot_session
from data.settings import settings
from database import User, Tariff
from database.models.orders import Order, OrderStatus
from handlers.routers import admin_router, user_router
from handlers.users.gps_modul import check_location
# from handlers.users.base import check_location
# from handlers.users.base import monitoring_geo
from handlers.users.monitoring import monitoring
from helpers.keyboards.markups import custom_back_button
from middlewares.i18n_middleware import ACLMiddleware
from middlewares.manage_users import ManageUserMiddleware
from utils.yookassa.api import check_payment
from webhooks import web_application

logging.getLogger('apscheduler.executors.default').propagate = False


async def check_invoices_status(bot: Bot):
    active_invoices = await Order.find(
        Order.status == OrderStatus.created
    ).to_list()

    for invoice in active_invoices:
        result = await check_payment(invoice.identy)
        user = await User.find_one(
            User.id == invoice.user
        )
        if result == 'succeeded':
            link = await bot.create_chat_invite_link(
                chat_id=-1002233906745,
                name=user.username
            )
            markup = InlineKeyboardBuilder()
            markup.button(text='🔗 Вступить в группу', url=link.invite_link)
            markup.button(text='🧑🏼‍💻 Техническая поддержка', url='https://t.me/obggreen')
            markup.row(custom_back_button('start'))

            if invoice.type != 'block':
                await bot.send_message(
                    user.user_id,
                    text=
                    'Оплата успешно получена!🎉\n\n'
                    'По ссылке можете перейти только вы, она действует лишь один раз и сверяется по базе покупок, '
                    'если вы'
                    'приобретете доступ другому человеку, мы это заметим и аннулируем вашу подписку и ваши деньги '
                    'сгорят.\n\n',
                    reply_markup=markup.adjust(1).as_markup()
                )

                invoice.status = OrderStatus.success
                await invoice.save()
            else:
                await bot.send_message(
                    user.user_id,
                    text=
                    'Покупка разблокировки прошла успешно!\n\n'
                    'В следующий раз старайтесь не нарушать правила сервиса!'
                )
                user.blocked_bot = False
                invoice.status = OrderStatus.success
                await invoice.save()
                await user.save()


async def start_scheduler(bot: Bot, session: AiohttpSession):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_invoices_status, 'interval', seconds=10, args=[bot])
    scheduler.add_job(monitoring, 'interval', seconds=10, args=[bot])
    scheduler.add_job(check_location, 'interval', seconds=14400, args=[bot])
    scheduler.start()


async def on_startup(dispatcher: Dispatcher, bot: Bot):
    await database.init_db()
    # await utils.utils_setup(dispatcher.workflow_data)

    # Register middlewares
    dispatcher.message.outer_middleware(ACLMiddleware(i18n))
    dispatcher.callback_query.outer_middleware(ACLMiddleware(i18n))
    dispatcher.message.outer_middleware(ManageUserMiddleware())
    dispatcher.callback_query.outer_middleware(ManageUserMiddleware())

    # Register routers
    dispatcher.include_router(admin_router)
    dispatcher.include_router(user_router)

    # Register webhook
    await bot.delete_webhook()
    # await bot.set_webhook(f"{settings.webhook.base_url}{settings.webhook.bot_path}", allowed_updates=dispatcher.resolve_used_update_types(), max_connections=100)
    print("Updates:", dispatcher.resolve_used_update_types())

    logger.info(f"> Bot started: @{(await bot.get_me()).username}")

    await start_scheduler(bot, session)


async def main():
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    session = AiohttpSession()
    bot = Bot(token=settings.telegram.token, session=session, default=DefaultBotProperties(parse_mode="HTML"))
    bot_session.set(bot)
    storage = RedisStorage(redis=Redis(host='localhost', port=6379, db=0))

    # I18N
    i18n = I18n(path="locales", default_locale="ru", domain="messages")
    web_application['i18n'] = i18n

    # Dispatchers
    dispatcher = Dispatcher(storage=storage)
    dispatcher.startup.register(on_startup)
    dispatcher.workflow_data['session'] = session

    asyncio.run(main())

    # # Request handler
    # SimpleRequestHandler(
    #     dispatcher=dispatcher, bot=bot
    # ).register(web_application, path=settings.webhook.bot_path)
    #
    # setup_application(web_application, dispatcher, bot=bot)
    #
    # web_application['bot'] = bot
    # web_application['session'] = session
    #
    # web.run_app(web_application, host=settings.webhook.listen_address, port=settings.webhook.listen_port)
