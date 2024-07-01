from datetime import datetime
from typing import Optional

from beanie import Document, BeanieObjectId, Indexed
from pydantic import Field


class OrderStatus:
    created = 'создан'
    canceled = 'отменен'
    time_out = 'истек'
    success = 'успешно'


class Order(Document):
    user: BeanieObjectId
    identy: Optional[str] = None
    subscribe_id: Optional[int] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    status: str = OrderStatus.created
    type: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        validate_on_save = True

