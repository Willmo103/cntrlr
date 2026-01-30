"""
core.database

Shared SQLAlchemy declarative base and session management for ORM model definitions.

Overview:
- Provides a single `declarative_base()` instance (`Base`) to be inherited by all
    SQLAlchemy ORM entity classes throughout the application.
- Ensures consistent metadata and registry sharing across all models.
- Includes a utility class for generating SQLAlchemy sessions (sync and async).

Contents:
- Base:
    Singleton `declarative_base` instance. All SQLAlchemy entity classes (e.g.,
    ObsidianNoteEntity, ObsidianVaultEntity, ObsidianNoteLineEntity) should inherit
    from this base to participate in the shared ORM registry and metadata.

- DatabaseSessionGenerator:
    Utility class to generate SQLAlchemy sessions bound to a specific engine.
    - __init__(settings: DatabaseSettings):
        Initializes the engine from the provided DatabaseSettings.
    - get_session() -> Session:
        Creates a new synchronous SQLAlchemy session.
    - get_async_session() -> AsyncSession:
        Creates a new asynchronous SQLAlchemy session.
    - get_db() -> AsyncGenerator[AsyncSession]:
        Async generator that yields a new async session for dependency injection.
    - init_db():
        Initializes the database by creating all tables defined in the ORM models.

Design Notes:
- Centralizing the declarative base avoids circular import issues and ensures all
    models share the same MetaData instance for schema generation and migrations.
- Import this module's `Base` in any model file to define new ORM entities.
- The DatabaseSessionGenerator supports both synchronous and asynchronous database
    access patterns for flexibility in different application contexts.
"""

from sqlalchemy import engine
from sqlalchemy.orm import declarative_base

from core.config import DatabaseSettings


Base = declarative_base()
"""Singleton `declarative_base` instance for ORM models."""


class DatabaseSessionGenerator:
    """
    Utility class to generate SQLAlchemy sessions bound to a specific engine.

    Attributes:
        engine (sqlalchemy.engine.Engine): The SQLAlchemy engine to bind sessions to.
    """

    def __init__(self, settings: DatabaseSettings):
        self.engine = engine.create_engine(settings.database_url)

    def get_session(self):
        """
        Creates a new SQLAlchemy session bound to the configured engine.

        Returns:
            sqlalchemy.orm.Session: A new session instance.
        """
        from sqlalchemy.orm import sessionmaker

        Session = sessionmaker(bind=self.engine)
        return Session()

    def get_async_session(self):
        """
        Creates a new SQLAlchemy async session bound to the configured engine.

        Returns:
            sqlalchemy.ext.asyncio.AsyncSession: A new async session instance.
        """
        from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
        from sqlalchemy.orm import sessionmaker

        async_engine = create_async_engine(self.engine.url)
        AsyncSessionLocal = sessionmaker(
            bind=async_engine, class_=AsyncSession, expire_on_commit=False
        )
        return AsyncSessionLocal()

    async def get_db(self):
        """
        Async generator that yields a new SQLAlchemy async session.

        Yields:
            sqlalchemy.ext.asyncio.AsyncSession: A new async session instance.
        """
        async with self.get_async_session() as session:
            yield session

    def init_db(self):
        """
        Initializes the database by creating all tables defined in the ORM models.
        """
        Base.metadata.create_all(self.engine)
