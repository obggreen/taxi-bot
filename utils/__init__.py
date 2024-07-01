from . import logging

from typing import Dict, Any

from .redis.client import RedisClient


async def utils_setup(data: Dict[str, Any]):
    logging.init()
    data['redis'] = await RedisClient("redis://localhost:6379").initialize()
