from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.enums import TransplantType


class CaseBase(BaseModel):
    case_date: date
    patient_name: str | None = None
    transplant_type: TransplantType
    multiplier: Decimal | None = None
    graft_count: int
    harvester_id: int | None = None
    planter_id: int | None = None
    technician1_id: int | None = None
    technician2_id: int | None = None
    notes: str | None = None

    @field_validator("multiplier")
    @classmethod
    def validate_multiplier(cls, value: Decimal | None) -> Decimal | None:
        if value is not None and value not in {Decimal("0.5"), Decimal("1.0")}:
            raise ValueError("Multiplier must be 0.5 or 1.0")
        return value

    @field_validator("graft_count")
    @classmethod
    def validate_graft_count(cls, value: int) -> int:
        if value < 0:
            raise ValueError("Graft count cannot be negative")
        return value


class CaseCreate(CaseBase):
    pass


class CaseUpdate(CaseBase):
    pass


class CaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    case_number: int
    case_date: date
    patient_name: str | None
    transplant_type: TransplantType
    multiplier: Decimal
    graft_count: int
    harvester_id: int | None
    planter_id: int | None
    technician1_id: int | None
    technician2_id: int | None
    notes: str | None
    created_at: datetime
    updated_at: datetime
