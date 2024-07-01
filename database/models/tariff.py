from datetime import datetime
from typing import Optional

from beanie import Document, BeanieObjectId, Indexed


class Tariff(Document):
    identity: int
    name: Optional[str] = None
    price: Optional[float] = None
    count_days: Optional[int] = None

    class Settings:
        validate_on_save = True

