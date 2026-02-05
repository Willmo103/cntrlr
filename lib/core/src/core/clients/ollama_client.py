from core.config import OllamaSettings
import ollama
from sqlite_utils import Database



class OllamaClient:
    __client__: ollama.Client
    __db__: Database
    __settings__: OllamaSettings

    def __init__(self, db: Database, settings: OllamaSettings) -> None:
        if db is None or not isinstance(db, Database):
            raise ValueError("A valid sqlite_utils.Database instance is required.")
        if settings is None or not isinstance(settings, OllamaSettings):
            raise ValueError("A valid OllamaSettings instance is required.")
        self.__db__ = db
        self.__settings__ = settings
        self.__client__ = ollama.Client(host=self.__settings__.host)


    def generate(self, *args, **kwargs) -> ollama.GenerateResponse:
        generate_request = {
            k: v for k, v in kwargs.items() if k in ollama.Options.__annotations__
        }
        return self.__client__.generate(*args, **kwargs)

