"""initial schema

Revision ID: 20260919_0001
Revises:
Create Date: 2026-09-19
"""

from alembic import op
import sqlalchemy as sa


revision = "20260919_0001"
down_revision = None
branch_labels = None
depends_on = None


user_role = sa.Enum("ADMIN", "VIEWER", name="userrole")
transplant_type = sa.Enum("HAIR", "BEARD", "EYEBROW", "HAIR_BEARD", "HAIR_EYEBROW", "HAIR_BEARD_EYEBROW", name="transplanttype")
personnel_role = sa.Enum("HARVESTER", "PLANTER", "DHI_TECHNICIAN", "HARVESTER_DHI", name="personnelrole")


def upgrade() -> None:
    bind = op.get_bind()
    user_role.create(bind, checkfirst=True)
    transplant_type.create(bind, checkfirst=True)
    personnel_role.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_users_username", "users", ["username"], unique=True)

    op.create_table(
        "personnel",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("full_name", sa.String(length=150), nullable=False),
        sa.Column("role", personnel_role, nullable=False),
        sa.Column("passport_number_encrypted", sa.String(length=255), nullable=True),
        sa.Column("arrival_date", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "bonus_rules",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("personnel_role", personnel_role, nullable=False),
        sa.Column("multiplier", sa.Numeric(2, 1), nullable=False),
        sa.Column("amount_usd", sa.Numeric(10, 2), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("personnel_role", "multiplier", "effective_from", name="uq_bonus_rule_role_mult_date"),
    )

    op.create_table(
        "cases",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("case_number", sa.Integer(), nullable=False),
        sa.Column("case_date", sa.Date(), nullable=False),
        sa.Column("patient_name", sa.String(length=200), nullable=True),
        sa.Column("transplant_type", transplant_type, nullable=False),
        sa.Column("multiplier", sa.Numeric(2, 1), nullable=False),
        sa.Column("graft_count", sa.Integer(), nullable=False),
        sa.Column("harvester_id", sa.Integer(), sa.ForeignKey("personnel.id"), nullable=True),
        sa.Column("planter_id", sa.Integer(), sa.ForeignKey("personnel.id"), nullable=True),
        sa.Column("technician1_id", sa.Integer(), sa.ForeignKey("personnel.id"), nullable=True),
        sa.Column("technician2_id", sa.Integer(), sa.ForeignKey("personnel.id"), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("multiplier IN (0.5, 1.0)", name="ck_case_multiplier"),
        sa.CheckConstraint("graft_count >= 0", name="ck_case_graft_count"),
    )
    op.create_index("ix_cases_case_number", "cases", ["case_number"], unique=True)

    op.create_table(
        "case_bonus_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("case_id", sa.Integer(), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("personnel_id", sa.Integer(), sa.ForeignKey("personnel.id"), nullable=False),
        sa.Column("personnel_role", personnel_role, nullable=False),
        sa.Column("multiplier", sa.Numeric(2, 1), nullable=False),
        sa.Column("amount_usd", sa.Numeric(10, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("actor_username", sa.String(length=50), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("case_bonus_items")
    op.drop_index("ix_cases_case_number", table_name="cases")
    op.drop_table("cases")
    op.drop_table("bonus_rules")
    op.drop_table("personnel")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_table("users")

    bind = op.get_bind()
    personnel_role.drop(bind, checkfirst=True)
    transplant_type.drop(bind, checkfirst=True)
    user_role.drop(bind, checkfirst=True)
