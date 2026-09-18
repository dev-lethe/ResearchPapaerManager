"""add_paper_duplicate_indexes

Revision ID: b8f11c2f4d8a
Revises: a4c43ccbbf2f
Create Date: 2026-08-15 17:10:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "b8f11c2f4d8a"
down_revision = "a4c43ccbbf2f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_papers_pdf_sha256", "papers", ["pdf_sha256"], unique=False)
    op.create_index("ix_papers_doi_lower", "papers", [sa.text("lower(doi)")], unique=False)


def downgrade() -> None:
    op.drop_index("ix_papers_doi_lower", table_name="papers")
    op.drop_index("ix_papers_pdf_sha256", table_name="papers")
