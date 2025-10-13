# ./config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    BOOLIAN_KEY: bool
    INTEGER_KEY: int
    STRING_KEY: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()

print (settings.BOOLIAN_KEY)
print (settings.INTEGER_KEY)
print (settings.STRING_KEY)