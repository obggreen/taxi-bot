from datetime import datetime
from typing import Optional

from beanie import Document, BeanieObjectId, Indexed
from pydantic import BaseModel, Field
from traitlets import List


# Constants
class UserType:
    user = 'user'
    tuser = 'tuser'
    admin = 'admin'


class DocumentType:
    verified = 'verified'
    untested = 'untested'


class UserVerification(BaseModel):
    verification_auto: Optional[bool] = Field(default=False)
    verification_user: Optional[bool] = Field(default=False)


class UserDocument(BaseModel):
    auto_front: Optional[str] = None
    auto_left: Optional[str] = None
    auto_right: Optional[str] = None
    auto_back: Optional[str] = None
    salon_front: Optional[str] = None
    salon_back: Optional[str] = None
    auto_number: Optional[str] = None


class UserPhotoMe(BaseModel):
    right_front: Optional[str] = None
    right_back: Optional[str] = None
    sts_front: Optional[str] = None
    sts_back: Optional[str] = None
    person_right: Optional[str] = None
    sts_number: Optional[str] = None


class UserSettings(BaseModel):
    language: str = 'ru'


class User(Document):
    identity: str

    referral_id: Optional[BeanieObjectId] = None
    link_id: Optional[BeanieObjectId] = None

    user_id: Indexed(int, unique=True)
    username: Optional[str]
    full_name: str
    role: str = UserType.user
    fio: Optional[str] = None
    documents: str = DocumentType.untested
    photo_auto_documents: UserDocument = UserDocument()
    photo_user_documents: UserPhotoMe = UserPhotoMe()
    verification: UserVerification = UserVerification()
    number: Optional[int] = None

    subscription: Optional[BeanieObjectId] = None

    balance: float = 5

    settings: UserSettings = UserSettings()

    blocked_bot: bool = False
    registration_date: datetime = Field(default_factory=datetime.utcnow)
    today_payment: Optional[str] = None
    last_active: Optional[datetime] = None

    class Settings:
        validate_on_save = True

    @classmethod
    def validate_role(cls, value: str) -> str:
        if value not in [UserType.user, UserType.admin]:
            raise ValueError(f"role must be either '{UserType.user}' or '{UserType.admin}'")
        return value