from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, Enum, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import PersonnelRole


class BonusRule(Base):
    __tablename__ = "bonus_rules"
    __table_args__ = (
        UniqueConstraint("personnel_role", "multiplier", "effective_from", name="uq_bonus_rule_role_mult_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    personnel_role: Mapped[PersonnelRole] = mapped_column(Enum(PersonnelRole), nullable=False, index=True)
    multiplier: Mapped[Decimal] = mapped_column(Numeric(2, 1), nullable=False)
    amount_usd: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    effective_from: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
