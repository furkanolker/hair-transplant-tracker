from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import TransplantType


class Case(Base):
    __tablename__ = "cases"
    __table_args__ = (
        CheckConstraint("multiplier IN (0.5, 1.0)", name="ck_case_multiplier"),
        CheckConstraint("graft_count >= 0", name="ck_case_graft_count"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    case_number: Mapped[int] = mapped_column(unique=True, nullable=False, index=True)
    case_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    patient_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    transplant_type: Mapped[TransplantType] = mapped_column(Enum(TransplantType), nullable=False)
    multiplier: Mapped[Decimal] = mapped_column(Numeric(2, 1), nullable=False)
    graft_count: Mapped[int] = mapped_column(Integer, nullable=False)
    harvester_id: Mapped[int | None] = mapped_column(ForeignKey("personnel.id"), nullable=True)
    planter_id: Mapped[int | None] = mapped_column(ForeignKey("personnel.id"), nullable=True)
    technician1_id: Mapped[int | None] = mapped_column(ForeignKey("personnel.id"), nullable=True)
    technician2_id: Mapped[int | None] = mapped_column(ForeignKey("personnel.id"), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
