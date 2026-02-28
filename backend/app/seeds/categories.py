"""Seed the database with system categories."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.seeds import SYSTEM_CATEGORIES


async def seed_categories(session: AsyncSession) -> int:
    """Insert predefined system categories.

    Returns the number of categories created.
    """
    count = 0

    for sort_order, (name_key, icon, color, is_income, children) in enumerate(SYSTEM_CATEGORIES):
        parent = Category(
            id=uuid.uuid4(),
            user_id=None,
            parent_id=None,
            name_key=name_key,
            icon=icon,
            color=color,
            is_system=True,
            is_income=is_income,
            sort_order=sort_order,
        )
        session.add(parent)
        count += 1

        for child_sort, (child_name, child_icon, child_color) in enumerate(children):
            child = Category(
                id=uuid.uuid4(),
                user_id=None,
                parent_id=parent.id,
                name_key=child_name,
                icon=child_icon,
                color=child_color,
                is_system=True,
                is_income=is_income,
                sort_order=child_sort,
            )
            session.add(child)
            count += 1

    await session.flush()
    return count
