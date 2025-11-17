# core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    TELEGRAM_BOT_API_KEY: str = ""
    TELEGRAM_USER_ID: str = ""
    DATABASE_URL: str = ""
    SECRET_KEY: str = "change_me"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
