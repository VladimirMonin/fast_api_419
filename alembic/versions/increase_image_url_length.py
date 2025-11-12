"""Увеличение длины поля image_url до 500 символов

Revision ID: increase_image_url
Revises: 33e05a6a546e
Create Date: 2025-11-12 22:05:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "increase_image_url"
down_revision: Union[str, Sequence[str], None] = "33e05a6a546e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Увеличение длины image_url с 200 до 500 символов."""
    # SQLite не поддерживает ALTER COLUMN, используем batch mode
    with op.batch_alter_table("products", schema=None) as batch_op:
        batch_op.alter_column(
            "image_url",
            existing_type=sa.String(length=200),
            type_=sa.String(length=500),
            existing_nullable=True,
        )


def downgrade() -> None:
    """Возврат длины image_url к 200 символам."""
    # SQLite не поддерживает ALTER COLUMN, используем batch mode
    with op.batch_alter_table("products", schema=None) as batch_op:
        batch_op.alter_column(
            "image_url",
            existing_type=sa.String(length=500),
            type_=sa.String(length=200),
            existing_nullable=True,
        )
