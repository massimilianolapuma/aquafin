"""Export service – CSV, JSON, and GDPR data-portability exports."""

from __future__ import annotations

import csv
import io
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.account import Account
from app.models.categorization_rule import CategorizationRule
from app.models.category import Category
from app.models.import_record import ImportRecord
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.export import ExportFilters, TransactionExportRow


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

CSV_COLUMNS = [
    "Data",
    "Descrizione",
    "Importo",
    "Valuta",
    "Tipo",
    "Categoria",
    "Conto",
    "Metodo categorizzazione",
]


async def _query_transactions(
    db: AsyncSession,
    user_id: UUID,
    filters: ExportFilters,
) -> list[TransactionExportRow]:
    """Fetch transactions owned by *user_id* with optional filters."""
    stmt = (
        select(Transaction, Account.name.label("account_name"), Category.name_custom.label("category_custom"), Category.name_key.label("category_key"))
        .join(Account, Transaction.account_id == Account.id)
        .outerjoin(Category, Transaction.category_id == Category.id)
        .where(Account.user_id == user_id)
        .order_by(Transaction.date.desc(), Transaction.created_at.desc())
    )

    if filters.account_id is not None:
        stmt = stmt.where(Transaction.account_id == filters.account_id)
    if filters.category_id is not None:
        stmt = stmt.where(Transaction.category_id == filters.category_id)
    if filters.date_from is not None:
        stmt = stmt.where(Transaction.date >= filters.date_from)
    if filters.date_to is not None:
        stmt = stmt.where(Transaction.date <= filters.date_to)
    if filters.type is not None:
        stmt = stmt.where(Transaction.type == filters.type)

    result = await db.execute(stmt)
    rows: list[TransactionExportRow] = []
    for txn, acct_name, cat_custom, cat_key in result.all():
        rows.append(
            TransactionExportRow(
                date=txn.date,
                description=txn.description,
                amount=txn.amount,
                currency=txn.currency,
                type=txn.type.value if txn.type else "",
                category_name=cat_custom or cat_key,
                account_name=acct_name,
                categorization_method=(
                    txn.categorization_method.value
                    if txn.categorization_method
                    else None
                ),
            )
        )
    return rows


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def export_transactions_csv(
    db: AsyncSession,
    user_id: UUID,
    filters: ExportFilters,
) -> str:
    """Return a CSV string (without BOM) of the user's transactions."""
    rows = await _query_transactions(db, user_id, filters)

    buf = io.StringIO()
    writer = csv.writer(buf, delimiter=";", quoting=csv.QUOTE_MINIMAL)
    writer.writerow(CSV_COLUMNS)
    for r in rows:
        writer.writerow(
            [
                r.date.isoformat(),
                r.description or "",
                str(r.amount),
                r.currency,
                r.type,
                r.category_name or "",
                r.account_name,
                r.categorization_method or "",
            ]
        )
    return buf.getvalue()


async def export_transactions_json(
    db: AsyncSession,
    user_id: UUID,
    filters: ExportFilters,
) -> list[dict]:
    """Return a list of dicts representing the user's transactions."""
    rows = await _query_transactions(db, user_id, filters)
    return [
        {
            "date": r.date.isoformat(),
            "description": r.description,
            "amount": str(r.amount),
            "currency": r.currency,
            "type": r.type,
            "category_name": r.category_name,
            "account_name": r.account_name,
            "categorization_method": r.categorization_method,
        }
        for r in rows
    ]


async def export_gdpr(db: AsyncSession, user_id: UUID) -> dict:
    """Full GDPR data-portability export for a single user."""

    # User ------------------------------------------------------------------
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    user_data: dict = {}
    if user:
        user_data = {
            "id": str(user.id),
            "clerk_id": user.clerk_id,
            "email": user.email,
            "display_name": user.display_name,
            "locale": user.locale,
            "preferences": user.preferences,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
        }

    # Accounts --------------------------------------------------------------
    acct_result = await db.execute(
        select(Account).where(Account.user_id == user_id)
    )
    accounts_data = [
        {
            "id": str(a.id),
            "name": a.name,
            "type": a.type.value if a.type else None,
            "currency": a.currency,
            "is_active": a.is_active,
            "created_at": a.created_at.isoformat() if a.created_at else None,
        }
        for a in acct_result.scalars().all()
    ]

    # Categories ------------------------------------------------------------
    cat_result = await db.execute(
        select(Category).where(
            (Category.user_id == user_id) | (Category.is_system == True)  # noqa: E712
        )
    )
    categories_data = [
        {
            "id": str(c.id),
            "name_key": c.name_key,
            "name_custom": c.name_custom,
            "icon": c.icon,
            "color": c.color,
            "is_system": c.is_system,
            "is_income": c.is_income,
        }
        for c in cat_result.scalars().all()
    ]

    # Transactions ----------------------------------------------------------
    txn_result = await db.execute(
        select(Transaction)
        .join(Account, Transaction.account_id == Account.id)
        .where(Account.user_id == user_id)
    )
    transactions_data = [
        {
            "id": str(t.id),
            "account_id": str(t.account_id),
            "category_id": str(t.category_id) if t.category_id else None,
            "amount": str(t.amount),
            "currency": t.currency,
            "date": t.date.isoformat(),
            "description": t.description,
            "original_description": t.original_description,
            "type": t.type.value if t.type else None,
            "categorization_method": (
                t.categorization_method.value if t.categorization_method else None
            ),
            "is_recurring": t.is_recurring,
            "tags": t.tags if t.tags else [],
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in txn_result.scalars().all()
    ]

    # Imports ---------------------------------------------------------------
    imp_result = await db.execute(
        select(ImportRecord).where(ImportRecord.user_id == user_id)
    )
    imports_data = [
        {
            "id": str(i.id),
            "account_id": str(i.account_id),
            "filename": i.filename,
            "file_type": i.file_type.value if i.file_type else None,
            "source_type": i.source_type.value if i.source_type else None,
            "status": i.status.value if i.status else None,
            "row_count": i.row_count,
            "created_at": i.created_at.isoformat() if i.created_at else None,
        }
        for i in imp_result.scalars().all()
    ]

    # Categorization rules --------------------------------------------------
    rule_result = await db.execute(
        select(CategorizationRule).where(CategorizationRule.user_id == user_id)
    )
    rules_data = [
        {
            "id": str(r.id),
            "category_id": str(r.category_id),
            "pattern": r.pattern,
            "match_type": r.match_type.value if r.match_type else None,
            "priority": r.priority,
            "is_active": r.is_active,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rule_result.scalars().all()
    ]

    return {
        "user": user_data,
        "accounts": accounts_data,
        "categories": categories_data,
        "transactions": transactions_data,
        "imports": imports_data,
        "rules": rules_data,
        "exported_at": datetime.now(timezone.utc).isoformat(),
    }
