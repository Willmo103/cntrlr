"""
Test suite for OllamaClient with 100% coverage.

Tests cover:
- _serialize() function for all data types
- _log_request_response decorator
- OllamaClient initialization and validation
- All client methods (generate, chat, embed, embeddings, list, show, pull, push, create, delete, copy, ps)
"""

import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, PropertyMock, patch

import pytest
from pydantic import BaseModel
from sqlite_utils import Database

from core.clients.ollama_client import OllamaClient, _log_request_response, _serialize
from core.config import OllamaSettings

# region Test Constants

TEST_HOST = "http://localhost:11434"
TEST_MODEL = "llama3.2:3b"


# endregion
# region Fixtures


class MockPydanticModel(BaseModel):
    """Mock Pydantic model for testing serialization."""

    field1: str
    field2: int


@pytest.fixture
def mock_settings(monkeypatch) -> OllamaSettings:
    """Create test OllamaSettings with env vars cleared."""
    # Clear any environment variables that might override settings
    monkeypatch.delenv("OLLAMA_HOST", raising=False)
    monkeypatch.delenv("OLLAMA_MODEL", raising=False)
    monkeypatch.delenv("OLLAMA_CTX", raising=False)
    monkeypatch.delenv("OLLAMA_TEMPERATURE", raising=False)
    monkeypatch.delenv("OLLAMA_TOP_K", raising=False)
    monkeypatch.delenv("OLLAMA_TOP_P", raising=False)
    monkeypatch.delenv("OLLAMA_EMBEDDING_MODEL", raising=False)
    monkeypatch.delenv("OLLAMA_VL_MODEL", raising=False)

    return OllamaSettings(
        host=TEST_HOST,
        default_model=TEST_MODEL,
        context_size=4096,
        default_temperature=0.7,
        default_top_k=40,
        default_top_p=0.9,
        embedding_model="nomic-embed-text",
        vl_model="llava",
    )


@pytest.fixture
def mock_db() -> MagicMock:
    """Create a mock sqlite_utils.Database."""
    db = MagicMock(spec=Database)
    # Mock table access via __getitem__
    db.__getitem__ = MagicMock(return_value=MagicMock())
    return db


@pytest.fixture
def mock_ollama_client() -> MagicMock:
    """Create a mock ollama.Client."""
    return MagicMock()


@pytest.fixture
def client(
    mock_db: MagicMock, mock_settings: OllamaSettings, mock_ollama_client: MagicMock
) -> OllamaClient:
    """Create OllamaClient with mocked dependencies."""
    with patch(
        "core.clients.ollama_client.ollama.Client", return_value=mock_ollama_client
    ):
        oc = OllamaClient(db=mock_db, settings=mock_settings)
        # Store reference to the mock for test access
        oc._mock_client = mock_ollama_client
        return oc


# endregion
# region Test _serialize Function


class TestSerialize:
    """Tests for the _serialize helper function."""

    def test_serialize_none(self):
        """Test serialization of None."""
        assert _serialize(None) is None

    def test_serialize_string(self):
        """Test serialization of string."""
        assert _serialize("hello") == "hello"

    def test_serialize_int(self):
        """Test serialization of integer."""
        assert _serialize(42) == 42

    def test_serialize_float(self):
        """Test serialization of float."""
        assert _serialize(3.14) == 3.14

    def test_serialize_bool(self):
        """Test serialization of boolean."""
        assert _serialize(True) is True
        assert _serialize(False) is False

    def test_serialize_pydantic_model(self):
        """Test serialization of Pydantic BaseModel."""
        model = MockPydanticModel(field1="test", field2=123)
        result = _serialize(model)
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed == {"field1": "test", "field2": 123}

    def test_serialize_list(self):
        """Test serialization of list."""
        result = _serialize([1, "two", 3.0])
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed == [1, "two", 3.0]

    def test_serialize_tuple(self):
        """Test serialization of tuple."""
        result = _serialize((1, 2, 3))
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed == [1, 2, 3]

    def test_serialize_dict(self):
        """Test serialization of dict."""
        result = _serialize({"key": "value", "num": 42})
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed == {"key": "value", "num": 42}

    def test_serialize_nested_list_with_pydantic(self):
        """Test serialization of list containing Pydantic models."""
        model = MockPydanticModel(field1="nested", field2=999)
        result = _serialize([model, "plain"])
        assert isinstance(result, str)
        parsed = json.loads(result)
        # Nested Pydantic model gets double-serialized (JSON string within JSON)
        assert len(parsed) == 2

    def test_serialize_nested_dict(self):
        """Test serialization of nested dict."""
        result = _serialize({"outer": {"inner": "value"}})
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed == {"outer": '{"inner": "value"}'}

    def test_serialize_unknown_type(self):
        """Test serialization of unknown type (falls back to str)."""

        class CustomClass:
            def __str__(self):
                return "custom_object"

        result = _serialize(CustomClass())
        assert isinstance(result, str)
        assert "custom_object" in result


# endregion
# region Test OllamaClient Initialization


class TestOllamaClientInit:
    """Tests for OllamaClient initialization."""

    def test_init_success(self, mock_db: MagicMock, mock_settings: OllamaSettings):
        """Test successful initialization."""
        with patch("core.clients.ollama_client.ollama.Client") as mock_client_class:
            client = OllamaClient(db=mock_db, settings=mock_settings)
            mock_client_class.assert_called_once_with(host=mock_settings.host)
            assert client.__db__ is mock_db
            assert client.__settings__ is mock_settings

    def test_init_none_db_raises(self, mock_settings: OllamaSettings):
        """Test that None db raises ValueError."""
        with pytest.raises(ValueError, match="valid sqlite_utils.Database instance"):
            OllamaClient(db=None, settings=mock_settings)

    def test_init_invalid_db_type_raises(self, mock_settings: OllamaSettings):
        """Test that invalid db type raises ValueError."""
        with pytest.raises(ValueError, match="valid sqlite_utils.Database instance"):
            OllamaClient(db="not_a_database", settings=mock_settings)

    def test_init_none_settings_raises(self, mock_db: MagicMock):
        """Test that None settings raises ValueError."""
        with pytest.raises(ValueError, match="valid OllamaSettings instance"):
            OllamaClient(db=mock_db, settings=None)

    def test_init_invalid_settings_type_raises(self, mock_db: MagicMock):
        """Test that invalid settings type raises ValueError."""
        with pytest.raises(ValueError, match="valid OllamaSettings instance"):
            OllamaClient(db=mock_db, settings="not_settings")


# endregion
# region Test Decorated Methods (generate, chat, embed, embeddings)


class TestDecoratedMethods:
    """Tests for methods decorated with _log_request_response."""

    def test_generate_logs_and_returns(self, client: OllamaClient, mock_db: MagicMock):
        """Test generate method logs request/response and returns result."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.model_dump.return_value = {
            "model": TEST_MODEL,
            "response": "Hello, world!",
            "done": True,
        }
        client._mock_client.generate.return_value = mock_response

        # Call method
        result = client.generate(model=TEST_MODEL, prompt="Say hello")

        # Verify client was called
        client._mock_client.generate.assert_called_once_with(
            model=TEST_MODEL, prompt="Say hello"
        )

        # Verify request was logged
        mock_db.__getitem__.assert_any_call("generate_requests")

        # Verify response was logged
        mock_db.__getitem__.assert_any_call("generate_responses")

        # Verify return value
        assert result is mock_response

    def test_chat_logs_and_returns(self, client: OllamaClient, mock_db: MagicMock):
        """Test chat method logs request/response and returns result."""
        mock_response = MagicMock()
        mock_response.model_dump.return_value = {
            "model": TEST_MODEL,
            "message": {"role": "assistant", "content": "Hi!"},
            "done": True,
        }
        client._mock_client.chat.return_value = mock_response

        messages = [{"role": "user", "content": "Hello"}]
        result = client.chat(model=TEST_MODEL, messages=messages)

        client._mock_client.chat.assert_called_once_with(
            model=TEST_MODEL, messages=messages
        )
        mock_db.__getitem__.assert_any_call("chat_requests")
        mock_db.__getitem__.assert_any_call("chat_responses")
        assert result is mock_response

    def test_embed_logs_and_returns(self, client: OllamaClient, mock_db: MagicMock):
        """Test embed method logs request/response and returns result."""
        mock_response = MagicMock()
        mock_response.model_dump.return_value = {
            "model": TEST_MODEL,
            "embeddings": [[0.1, 0.2, 0.3]],
        }
        client._mock_client.embed.return_value = mock_response

        result = client.embed(model=TEST_MODEL, input="test text")

        client._mock_client.embed.assert_called_once_with(
            model=TEST_MODEL, input="test text"
        )
        mock_db.__getitem__.assert_any_call("embed_requests")
        mock_db.__getitem__.assert_any_call("embed_responses")
        assert result is mock_response

    def test_embeddings_logs_and_returns(
        self, client: OllamaClient, mock_db: MagicMock
    ):
        """Test embeddings method logs request/response and returns result."""
        mock_response = MagicMock()
        mock_response.model_dump.return_value = {
            "embedding": [0.1, 0.2, 0.3],
        }
        client._mock_client.embeddings.return_value = mock_response

        result = client.embeddings(model=TEST_MODEL, prompt="test")

        client._mock_client.embeddings.assert_called_once_with(
            model=TEST_MODEL, prompt="test"
        )
        mock_db.__getitem__.assert_any_call("embeddings_requests")
        mock_db.__getitem__.assert_any_call("embeddings_responses")
        assert result is mock_response

    def test_response_without_model_dump(
        self, client: OllamaClient, mock_db: MagicMock
    ):
        """Test handling of response without model_dump method."""
        # Create a response without model_dump
        mock_response = "plain_string_response"
        client._mock_client.generate.return_value = mock_response

        result = client.generate(model=TEST_MODEL, prompt="test")

        assert result == mock_response
        # Should still log (using str fallback)
        mock_db.__getitem__.assert_any_call("generate_responses")


# endregion
# region Test Non-Decorated Methods


class TestNonDecoratedMethods:
    """Tests for methods without logging decorator."""

    def test_list_returns_models(self, client: OllamaClient):
        """Test list method returns available models."""
        mock_response = MagicMock()
        mock_response.models = [{"name": TEST_MODEL}]
        client._mock_client.list.return_value = mock_response

        result = client.list()

        client._mock_client.list.assert_called_once()
        assert result is mock_response

    def test_show_returns_model_info(self, client: OllamaClient):
        """Test show method returns model information."""
        mock_response = MagicMock()
        mock_response.modelfile = "FROM llama3.2"
        client._mock_client.show.return_value = mock_response

        result = client.show(TEST_MODEL)

        client._mock_client.show.assert_called_once_with(TEST_MODEL)
        assert result is mock_response

    def test_pull_downloads_model(self, client: OllamaClient):
        """Test pull method downloads a model."""
        mock_response = MagicMock()
        client._mock_client.pull.return_value = mock_response

        result = client.pull(TEST_MODEL, insecure=False)

        client._mock_client.pull.assert_called_once_with(TEST_MODEL, insecure=False)
        assert result is mock_response

    def test_push_uploads_model(self, client: OllamaClient):
        """Test push method uploads a model."""
        mock_response = MagicMock()
        client._mock_client.push.return_value = mock_response

        result = client.push("mymodel:latest", insecure=False)

        client._mock_client.push.assert_called_once_with(
            "mymodel:latest", insecure=False
        )
        assert result is mock_response

    def test_create_creates_model(self, client: OllamaClient):
        """Test create method creates a new model."""
        mock_response = MagicMock()
        client._mock_client.create.return_value = mock_response

        result = client.create("newmodel", modelfile="FROM llama3.2")

        client._mock_client.create.assert_called_once_with(
            "newmodel", modelfile="FROM llama3.2"
        )
        assert result is mock_response

    def test_delete_removes_model(self, client: OllamaClient):
        """Test delete method removes a model."""
        mock_response = MagicMock()
        mock_response.status = "success"
        client._mock_client.delete.return_value = mock_response

        result = client.delete(TEST_MODEL)

        client._mock_client.delete.assert_called_once_with(TEST_MODEL)
        assert result is mock_response

    def test_copy_duplicates_model(self, client: OllamaClient):
        """Test copy method duplicates a model."""
        mock_response = MagicMock()
        mock_response.status = "success"
        client._mock_client.copy.return_value = mock_response

        result = client.copy(TEST_MODEL, "llama3.2:3b-copy")

        client._mock_client.copy.assert_called_once_with(TEST_MODEL, "llama3.2:3b-copy")
        assert result is mock_response

    def test_ps_lists_running_models(self, client: OllamaClient):
        """Test ps method lists running models."""
        mock_response = MagicMock()
        mock_response.models = []
        client._mock_client.ps.return_value = mock_response

        result = client.ps()

        client._mock_client.ps.assert_called_once()
        assert result is mock_response


# endregion
# region Test OllamaSettings Configuration


class TestOllamaSettings:
    """Tests for OllamaSettings configuration."""

    def test_default_values(self, monkeypatch):
        """Test default settings values."""
        # Clear environment variables that might override defaults
        monkeypatch.delenv("OLLAMA_HOST", raising=False)
        monkeypatch.delenv("OLLAMA_MODEL", raising=False)
        monkeypatch.delenv("OLLAMA_CTX", raising=False)
        monkeypatch.delenv("OLLAMA_TEMPERATURE", raising=False)
        monkeypatch.delenv("OLLAMA_TOP_K", raising=False)
        monkeypatch.delenv("OLLAMA_TOP_P", raising=False)
        monkeypatch.delenv("OLLAMA_EMBEDDING_MODEL", raising=False)
        monkeypatch.delenv("OLLAMA_VL_MODEL", raising=False)

        settings = OllamaSettings()
        assert settings.host == "http://localhost:11434"
        assert settings.default_model == "gpt-oss:20b"
        assert settings.context_size == 65536
        assert settings.default_temperature == 0.7
        assert settings.default_top_k == 40
        assert settings.default_top_p == 0.9
        assert settings.embedding_model == "embeddinggemma"
        assert settings.vl_model == "qwen"

    def test_custom_values(self, monkeypatch):
        """Test custom settings values."""
        # Clear environment variables
        monkeypatch.delenv("OLLAMA_HOST", raising=False)
        monkeypatch.delenv("OLLAMA_MODEL", raising=False)

        settings = OllamaSettings(
            host=TEST_HOST,
            default_model=TEST_MODEL,
            context_size=4096,
            default_temperature=0.5,
            default_top_k=50,
            default_top_p=0.95,
            embedding_model="nomic-embed-text",
            vl_model="llava",
        )
        assert settings.host == TEST_HOST
        assert settings.default_model == TEST_MODEL
        assert settings.context_size == 4096
        assert settings.default_temperature == 0.5
        assert settings.default_top_k == 50
        assert settings.default_top_p == 0.95
        assert settings.embedding_model == "nomic-embed-text"
        assert settings.vl_model == "llava"

    def test_environment_variable_aliases(self, monkeypatch):
        """Test that environment variable aliases work."""
        monkeypatch.setenv("OLLAMA_HOST", "http://custom:11434")
        monkeypatch.setenv("OLLAMA_MODEL", "custom-model")
        monkeypatch.setenv("OLLAMA_CTX", "8192")
        monkeypatch.setenv("OLLAMA_TEMPERATURE", "0.3")
        monkeypatch.setenv("OLLAMA_TOP_K", "30")
        monkeypatch.setenv("OLLAMA_TOP_P", "0.8")
        monkeypatch.setenv("OLLAMA_EMBEDDING_MODEL", "custom-embed")
        monkeypatch.setenv("OLLAMA_VL_MODEL", "custom-vl")

        settings = OllamaSettings()
        assert settings.host == "http://custom:11434"
        assert settings.default_model == "custom-model"
        assert settings.context_size == 8192
        assert settings.default_temperature == 0.3
        assert settings.default_top_k == 30
        assert settings.default_top_p == 0.8
        assert settings.embedding_model == "custom-embed"
        assert settings.vl_model == "custom-vl"


# endregion
# region Test Decorator Behavior


class TestLogRequestResponseDecorator:
    """Tests for the _log_request_response decorator."""

    def test_decorator_preserves_function_metadata(self, client: OllamaClient):
        """Test that decorator preserves function name and docstring."""
        # The wrapped function should maintain its name
        assert client.generate.__name__ == "generate"

    def test_decorator_logs_timestamp(self, client: OllamaClient, mock_db: MagicMock):
        """Test that decorator logs with timestamp."""
        mock_response = MagicMock()
        mock_response.model_dump.return_value = {"done": True}
        client._mock_client.generate.return_value = mock_response

        client.generate(model=TEST_MODEL, prompt="test")

        # Get the insert call arguments
        insert_calls = mock_db.__getitem__.return_value.insert.call_args_list
        assert len(insert_calls) >= 1

        # First call should be request with timestamp
        request_data = insert_calls[0][0][0]
        assert "timestamp" in request_data

    def test_decorator_logs_method_name(self, client: OllamaClient, mock_db: MagicMock):
        """Test that decorator logs method name."""
        mock_response = MagicMock()
        mock_response.model_dump.return_value = {"done": True}
        client._mock_client.chat.return_value = mock_response

        client.chat(model=TEST_MODEL, messages=[])

        insert_calls = mock_db.__getitem__.return_value.insert.call_args_list
        request_data = insert_calls[0][0][0]
        assert request_data["method"] == "chat"


# endregion
