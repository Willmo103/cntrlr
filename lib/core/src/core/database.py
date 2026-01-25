"""
core.database

Shared SQLAlchemy declarative base for ORM model definitions.

Overview:
- Provides a single `declarative_base()` instance (`Base`) to be inherited by all
    SQLAlchemy ORM entity classes throughout the application.
- Ensures consistent metadata and registry sharing across all models.

Contents:
- Base:
    Singleton `declarative_base` instance. All SQLAlchemy entity classes (e.g.,
    ObsidianNoteEntity, ObsidianVaultEntity, ObsidianNoteLineEntity) should inherit
    from this base to participate in the shared ORM registry and metadata.

Design notes:
- Centralizing the declarative base avoids circular import issues and ensures all
    models share the same MetaData instance for schema generation and migrations.
- Import this module's `Base` in any model file to define new ORM entities.
"""

from sqlalchemy.orm import declarative_base

Base = declarative_base()
"""Singleton `declarative_base` instance for ORM models."""
