"""fix_indexes_for_like

Revision ID: bb4034a62770
Revises: 929aa9a9fb6b
Create Date: 2026-06-26 15:42:18.607333

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bb4034a62770'
down_revision: Union[str, Sequence[str], None] = '929aa9a9fb6b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Replace activities index with varchar_pattern_ops for LIKE support
    op.drop_index("ix_activities_nace_code_classification", table_name="activities")
    op.create_index(
        "ix_activities_nace_code_classification",
        "activities",
        ["nace_code", "classification"],
        unique=False,
        postgresql_using="btree",
        postgresql_ops={"nace_code": "varchar_pattern_ops"},
    )

    op.create_index("ix_enterprises_status", "enterprises", ["status", "enterprise_number"], unique=False)
    op.create_index("ix_establishments_enterprise_number", "establishments", ["enterprise_number"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_establishments_enterprise_number", table_name="establishments")
    op.drop_index("ix_enterprises_status", table_name="enterprises")

    # Restore original index without varchar_pattern_ops
    op.drop_index("ix_activities_nace_code_classification", table_name="activities")
    op.create_index(
        "ix_activities_nace_code_classification",
        "activities",
        ["nace_code", "classification"],
        unique=False,
    )
