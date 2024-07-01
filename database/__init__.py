from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from database.models import User, Link, Tariff, Order

from data.settings import settings


async def init_db():
    client = AsyncIOMotorClient(settings.mongodb.uri)
    await init_beanie(
        database=client.taxi,
        document_models=[
            User, Link, Tariff, Order
        ]
    )
