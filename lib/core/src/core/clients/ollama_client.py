from typing import Any, Callable, TypeVar
from functools import wraps
from datetime import datetime, timezone
import json

import ollama
from sqlite_utils import Database

from core.config import OllamaSettings


T = TypeVar("T")


def _serialize(obj: Any) -> Any:
    """Serialize objects for SQLite storage."""
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if hasattr(obj, "model_dump"):
        return json.dumps(obj.model_dump())
    if isinstance(obj, (list, tuple)):
        return json.dumps([_serialize(i) for i in obj])
    if isinstance(obj, dict):
        return json.dumps({k: _serialize(v) for k, v in obj.items()})
    return json.dumps(str(obj))


def _log_request_response(method_name: str):
    """Decorator to log request/response for any Ollama method."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(self: "OllamaClient", **kwargs) -> T:
            timestamp = datetime.now(timezone.utc).isoformat()

            # Log request
            request_row = {
                "timestamp": timestamp,
                "method": method_name,
                **{k: _serialize(v) for k, v in kwargs.items()}
            }
            self.__db__[f"{method_name}_requests"].insert(request_row)

            # Execute
            response: T = func(self, **kwargs)

            # Log response
            response_data = response.model_dump() if hasattr(response, "model_dump") else {"result": str(response)}
            response_row = {
                "timestamp": timestamp,
                "method": method_name,
                **{k: _serialize(v) for k, v in response_data.items()}
            }
            self.__db__[f"{method_name}_responses"].insert(response_row)

            return response
        return wrapper
    return decorator


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

    @_log_request_response("generate")
    def generate(self, **kwargs) -> ollama.GenerateResponse:
        return self.__client__.generate(**kwargs)

    @_log_request_response("chat")
    def chat(self, **kwargs) -> ollama.ChatResponse:
        return self.__client__.chat(**kwargs)

    @_log_request_response("embed")
    def embed(self, **kwargs) -> ollama.EmbedResponse:
        return self.__client__.embed(**kwargs)

    @_log_request_response("embeddings")
    def embeddings(self, **kwargs) -> ollama.EmbeddingsResponse:
        return self.__client__.embeddings(**kwargs)

    def list(self) -> ollama.ListResponse:
        """List available models (no logging needed)."""
        return self.__client__.list()

    def show(self, model: str) -> ollama.ShowResponse:
        """Show model info (no logging needed)."""
        return self.__client__.show(model)

    def pull(self, model: str, **kwargs) -> ollama.ProgressResponse:
        """Pull a model."""
        return self.__client__.pull(model, **kwargs)

    def push(self, model: str, **kwargs) -> ollama.ProgressResponse:
        """Push a model."""
        return self.__client__.push(model, **kwargs)

    def create(self, model: str, **kwargs) -> ollama.ProgressResponse:
        """Create a model."""
        return self.__client__.create(model, **kwargs)

    def delete(self, model: str) -> ollama.StatusResponse:
        """Delete a model."""
        return self.__client__.delete(model)

    def copy(self, source: str, destination: str) -> ollama.StatusResponse:
        """Copy a model."""
        return self.__client__.copy(source, destination)

    def ps(self) -> ollama.ProcessResponse:
        """List running models."""
        return self.__client__.ps()

