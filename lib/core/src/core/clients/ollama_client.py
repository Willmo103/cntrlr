from core.config import OllamaSettings
import ollama
from pydantic import BaseModel
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
        self. __clent_method_map__ = {
            "generate": self.__client__.generate,
            "chat": self.__client__.chat,
            "embed": self.__client__.embed,
            "embedings": self.__client__.embeddings,
            "pull": self.__client__.pull,
            "push": self.__client__.push,
            "create": self.__client__.create,
            "delete": self.__client__.delete,
            "list": self.__client__.list,
            "copy": self.__client__.copy,
            "show": self.__client__.show,
            "ps": self.__client__.ps,
        }

    def _process_kwargs(self, kwargs: dict) -> dict:
        # Placeholder for any argument processing logic before calling the client method
        for key, value in kwargs.items():
            if isinstance(BaseModel, value):
                kwargs[key] = value.model_dump()
        return kwargs
