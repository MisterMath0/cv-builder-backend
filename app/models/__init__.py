# app/models/__init__.py
from .user import User
from .section import Section
from ..database import Base  # Import Base from database

# Export all models and Base
__all__ = ["User", "CV", "Section", "Base"]