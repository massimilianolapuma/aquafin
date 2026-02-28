"""Tests for SQLAlchemy data models."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from app.models import (
    Account,
    AccountType,
    Base,
    CategorizationMethod,
    CategorizationRule,
    Category,
    FileType,
    ImportRecord,
    ImportStatus,
    MatchType,
    SourceType,
    Transaction,
    TransactionType,
    User,
)

# ---------------------------------------------------------------------------
# Model instantiation
# ---------------------------------------------------------------------------


class TestUserModel:
    """User model unit tests."""

    def test_create_user(self) -> None:
        user = User(
            id=uuid.uuid4(),
            clerk_id="clerk_abc123",
            email="test@example.com",
            display_name="Test User",
        )
        assert user.clerk_id == "clerk_abc123"
        assert user.email == "test@example.com"
        assert user.display_name == "Test User"

    def test_user_defaults(self) -> None:
        user = User(id=uuid.uuid4(), clerk_id="c1", email="u@e.com")
        assert user.locale == "it"
        assert user.is_active is True

    def test_user_repr(self) -> None:
        user = User(id=uuid.uuid4(), clerk_id="c1", email="u@e.com")
        assert "u@e.com" in repr(user)

    def test_user_tablename(self) -> None:
        assert User.__tablename__ == "users"


class TestAccountModel:
    """Account model unit tests."""

    def test_create_account(self) -> None:
        acc = Account(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            name="Main Bank",
            type=AccountType.bank,
        )
        assert acc.name == "Main Bank"
        assert acc.type == AccountType.bank

    def test_account_defaults(self) -> None:
        acc = Account(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            name="Cash",
            type=AccountType.cash,
        )
        assert acc.currency == "EUR"
        assert acc.is_active is True

    def test_account_tablename(self) -> None:
        assert Account.__tablename__ == "accounts"


class TestCategoryModel:
    """Category model unit tests."""

    def test_create_category(self) -> None:
        cat = Category(
            id=uuid.uuid4(),
            name_key="Alimentari",
            icon="🛒",
            color="#4CAF50",
            is_system=True,
        )
        assert cat.name_key == "Alimentari"
        assert cat.is_system is True

    def test_category_defaults(self) -> None:
        cat = Category(id=uuid.uuid4(), name_key="test")
        assert cat.is_income is False
        assert cat.sort_order == 0

    def test_category_tablename(self) -> None:
        assert Category.__tablename__ == "categories"


class TestTransactionModel:
    """Transaction model unit tests."""

    def test_create_transaction(self) -> None:
        txn = Transaction(
            id=uuid.uuid4(),
            account_id=uuid.uuid4(),
            amount=Decimal("42.50"),
            date=date(2026, 1, 15),
            type=TransactionType.expense,
            description="Grocery shopping",
        )
        assert txn.amount == Decimal("42.50")
        assert txn.type == TransactionType.expense

    def test_transaction_defaults(self) -> None:
        txn = Transaction(
            id=uuid.uuid4(),
            account_id=uuid.uuid4(),
            amount=Decimal("10"),
            date=date.today(),
            type=TransactionType.income,
        )
        assert txn.currency == "EUR"
        assert txn.is_recurring is False

    def test_transaction_tablename(self) -> None:
        assert Transaction.__tablename__ == "transactions"


class TestImportRecordModel:
    """ImportRecord model unit tests."""

    def test_create_import(self) -> None:
        rec = ImportRecord(
            id=uuid.uuid4(),
            account_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            filename="export.csv",
            file_type=FileType.csv,
            source_type=SourceType.bank_csv,
        )
        assert rec.filename == "export.csv"
        assert rec.file_type == FileType.csv

    def test_import_defaults(self) -> None:
        rec = ImportRecord(
            id=uuid.uuid4(),
            account_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            filename="f.csv",
            file_type=FileType.csv,
            source_type=SourceType.manual,
        )
        assert rec.status == ImportStatus.pending
        assert rec.row_count == 0
        assert rec.imported_count == 0

    def test_import_tablename(self) -> None:
        assert ImportRecord.__tablename__ == "imports"


class TestCategorizationRuleModel:
    """CategorizationRule model unit tests."""

    def test_create_rule(self) -> None:
        rule = CategorizationRule(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            category_id=uuid.uuid4(),
            pattern="LIDL",
        )
        assert rule.pattern == "LIDL"

    def test_rule_defaults(self) -> None:
        rule = CategorizationRule(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            category_id=uuid.uuid4(),
            pattern="x",
        )
        assert rule.match_type == MatchType.contains
        assert rule.priority == 0
        assert rule.is_active is True

    def test_rule_tablename(self) -> None:
        assert CategorizationRule.__tablename__ == "categorization_rules"


# ---------------------------------------------------------------------------
# Enum value tests
# ---------------------------------------------------------------------------


class TestEnumValues:
    """Ensure enums contain the expected members."""

    def test_account_type_values(self) -> None:
        expected = {"bank", "satispay", "paypal", "cash", "investment"}
        assert {e.value for e in AccountType} == expected

    def test_transaction_type_values(self) -> None:
        expected = {"income", "expense", "transfer"}
        assert {e.value for e in TransactionType} == expected

    def test_categorization_method_values(self) -> None:
        expected = {"manual", "rule", "keyword", "pattern", "ai", "uncategorized"}
        assert {e.value for e in CategorizationMethod} == expected

    def test_file_type_values(self) -> None:
        expected = {"csv", "pdf", "xlsx"}
        assert {e.value for e in FileType} == expected

    def test_source_type_values(self) -> None:
        expected = {"bank_csv", "satispay", "paypal", "pdf", "manual"}
        assert {e.value for e in SourceType} == expected

    def test_import_status_values(self) -> None:
        expected = {"pending", "processing", "preview", "confirmed", "failed", "cancelled"}
        assert {e.value for e in ImportStatus} == expected

    def test_match_type_values(self) -> None:
        expected = {"contains", "exact", "regex", "starts_with"}
        assert {e.value for e in MatchType} == expected


# ---------------------------------------------------------------------------
# Relationship declarations (class-level, no DB)
# ---------------------------------------------------------------------------


class TestRelationships:
    """Verify relationship properties exist on the model classes."""

    def test_user_has_accounts(self) -> None:
        assert hasattr(User, "accounts")

    def test_user_has_categories(self) -> None:
        assert hasattr(User, "categories")

    def test_user_has_imports(self) -> None:
        assert hasattr(User, "imports")

    def test_user_has_categorization_rules(self) -> None:
        assert hasattr(User, "categorization_rules")

    def test_account_has_transactions(self) -> None:
        assert hasattr(Account, "transactions")

    def test_account_has_user(self) -> None:
        assert hasattr(Account, "user")

    def test_category_has_parent_and_children(self) -> None:
        assert hasattr(Category, "parent")
        assert hasattr(Category, "children")

    def test_transaction_has_account(self) -> None:
        assert hasattr(Transaction, "account")

    def test_transaction_has_category(self) -> None:
        assert hasattr(Transaction, "category")

    def test_transaction_has_import_record(self) -> None:
        assert hasattr(Transaction, "import_record")

    def test_import_record_has_transactions(self) -> None:
        assert hasattr(ImportRecord, "transactions")

    def test_categorization_rule_has_user_and_category(self) -> None:
        assert hasattr(CategorizationRule, "user")
        assert hasattr(CategorizationRule, "category")


# ---------------------------------------------------------------------------
# Base model
# ---------------------------------------------------------------------------


class TestBaseModel:
    """Verify the declarative base configuration."""

    def test_base_is_declarative(self) -> None:
        assert hasattr(Base, "metadata")
        assert hasattr(Base, "registry")

    def test_all_tables_registered(self) -> None:
        table_names = set(Base.metadata.tables.keys())
        expected = {
            "users",
            "accounts",
            "categories",
            "transactions",
            "imports",
            "categorization_rules",
        }
        assert expected.issubset(table_names)
