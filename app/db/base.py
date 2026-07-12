"""Declarative base for all ORM models.

Note: this module intentionally does NOT import the model classes (that used
to live here and caused a circular import depending on which module got
imported first). Model registration for Alembic / metadata.create_all lives
in `app.models` instead — import that package wherever you need every model
attached to Base.metadata.
"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
