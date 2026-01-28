import pytest
import sys
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from core.database import Base

# Add the src directory to the path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


@pytest.fixture(scope="session")
def test_database_url():
    """Provide a test database URL (in-memory SQLite)."""
    return "sqlite:///:memory:"


@pytest.fixture(scope="session")
def engine(test_database_url):
    """Create a test database engine."""
    engine = create_engine(
        test_database_url,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(
    engine,
) -> Session:  # pyright: ignore[reportInvalidTypeForm]
    """Create a new database session for each test."""
    # Import Base here to avoid circular imports

    Base.metadata.create_all(bind=engine)

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_config_env(monkeypatch):
    """Set up test environment variables for config testing."""
    test_env_vars = {
        "APP_ENV": "testing",
        "DEBUG": "true",
        "DATABASE_URL": "sqlite:///:memory:",
        "SECRET_KEY": "test-secret-key-for-testing-only",
    }
    for key, value in test_env_vars.items():
        monkeypatch.setenv(key, value)
    return test_env_vars


@pytest.fixture
def sample_model_data():
    """Provide sample data for model testing."""
    return {
        "id": 1,
        "name": "Test Item",
        "description": "A test description",
        "is_active": True,
    }
