from pydantic_settings import BaseSettings


class TelegramSettings(BaseSettings):
    token: str
    support: str
    username_bot: str

    class Config:
        extra = "ignore"
        env_prefix = "TELEGRAM_"
        env_file = ".env"
        case_insensitive = True


class WebhookSettings(BaseSettings):
    listen_address: str
    listen_port: int
    base_url: str
    bot_path: str

    class Config:
        extra = "ignore"
        env_prefix = "WEBHOOK_"
        env_file = ".env"
        case_insensitive = True


class MongoDBSettings(BaseSettings):
    uri: str

    class Config:
        extra = "ignore"
        env_prefix = "MONGODB_"
        env_file = ".env"
        case_insensitive = True


class Settings(BaseSettings):
    telegram: TelegramSettings = TelegramSettings()
    webhook: WebhookSettings = WebhookSettings()
    mongodb: MongoDBSettings = MongoDBSettings()

    class Config:
        env_file = ".env"
        case_insensitive = True


settings = Settings()
