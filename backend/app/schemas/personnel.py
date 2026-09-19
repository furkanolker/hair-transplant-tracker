from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import PersonnelRole


class PersonnelBase(BaseModel):
    full_name: str
    role: PersonnelRole
    arrival_date: date | None = None
    notes: str | None = None


class PersonnelCreate(PersonnelBase):
    passport_number: str | None = None


class PersonnelUpdate(PersonnelBase):
    passport_number: str | None = None
    is_active: bool = True


class PersonnelStatusPatch(BaseModel):
    is_active: bool


class PersonnelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    role: PersonnelRole
    arrival_date: date | None
    is_active: bool
    notes: str | None
    created_at: datetime


class PersonnelAdminResponse(PersonnelResponse):
    passport_number_masked: str | None = None
