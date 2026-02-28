"""Models package – import all models so Alembic can discover them."""

from app.models.base import Base
from app.models.user import User
from app.models.account import Account, AccountType
from app.models.category import Category
from app.models.transaction import (
    CategorizationMethod,
    Transaction,
    TransactionType,
)
from app.models.import_record import (
    FileType,
    ImportRecord,
    ImportStatus,
    SourceType,
)
from app.models.categorization_rule import CategorizationRule, MatchType

__all__ = [
    "Base",
    "User",
    "Account",
    "AccountType",
    "Category",
    "Transaction",
    "TransactionType",
    "CategorizationMethod",
    "ImportRecord",
    "FileType",
    "ImportStatus",
    "SourceType",
    "CategorizationRule",
    "MatchType",
]
