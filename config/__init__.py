from pydantic_settings import BaseSettings
from urllib.parse import quote_plus


class CommonSettings(BaseSettings):
    APP_NAME: str = "CSV PARSER API"
    DEBUG_MODE: bool = False


class ServerSettings(BaseSettings):
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8000


class DatabaseSettings(BaseSettings):
    DB_USER: str = "fumax"
    DB_PASSWORD: str = "csvparser1234"
    DB_NAME: str = "csvparser"

    @property
    def encoded_user(self):
        return quote_plus(self.DB_USER)

    @property
    def encoded_password(self):
        return quote_plus(self.DB_PASSWORD)

    @property
    def DB_URL(self):
        return f"mongodb+srv://{self.encoded_user}:{self.encoded_password}@parser.c92mc.mongodb.net/?retryWrites=true&w=majority&appName=parser"


class Settings(CommonSettings, ServerSettings, DatabaseSettings):
    pass


settings = Settings()
