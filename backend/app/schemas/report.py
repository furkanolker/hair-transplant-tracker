from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class MonthlyReportSummary(BaseModel):
    month: str
    total_cases: int
    total_grafts: int
    total_bonus: Decimal
    case_type_counts: dict[str, int]
    personnel_bonus_totals: dict[str, Decimal]


class PersonnelReportSummary(BaseModel):
    personnel_id: int
    personnel_name: str
    case_count: int
    role_case_counts: dict[str, int]
    total_grafts: int
    total_bonus: Decimal
    start_date: date
    end_date: date
