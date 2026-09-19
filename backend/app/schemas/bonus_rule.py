from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.enums import PersonnelRole


class BonusRuleBase(BaseModel):
    personnel_role: PersonnelRole
    multiplier: Decimal
    amount_usd: Decimal
    effective_from: date
    is_active: bool = True

    @field_validator("multiplier")
    @classmethod
    def validate_multiplier(cls, value: Decimal) -> Decimal:
        if value not in {Decimal("0.5"), Decimal("1.0")}:
            raise ValueError("Multiplier must be 0.5 or 1.0")
        return value


class BonusRuleCreate(BonusRuleBase):
    pass


class BonusRuleUpdate(BonusRuleBase):
    pass


class BonusRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    personnel_role: PersonnelRole
    multiplier: Decimal
    amount_usd: Decimal
    effective_from: date
    is_active: bool
    created_at: datetime
