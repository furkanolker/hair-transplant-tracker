from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.models.bonus_rule import BonusRule
from app.models.enums import PersonnelRole


@dataclass
class BonusAssignment:
    personnel_id: int
    personnel_role: PersonnelRole
    multiplier: Decimal


class BonusCalculator:
    def __init__(self, db: Session):
        self.db = db

    def _resolve_rule(self, role: PersonnelRole, multiplier: Decimal, case_date: date) -> BonusRule:
        stmt = (
            select(BonusRule)
            .where(
                and_(
                    BonusRule.personnel_role == role,
                    BonusRule.multiplier == multiplier,
                    BonusRule.effective_from <= case_date,
                    BonusRule.is_active.is_(True),
                )
            )
            .order_by(BonusRule.effective_from.desc())
            .limit(1)
        )
        rule = self.db.execute(stmt).scalar_one_or_none()
        if not rule:
            raise ValueError(f"Bonus rule not found for role={role}, multiplier={multiplier}")
        return rule

    def calculate_case_bonus(self, assignments: list[BonusAssignment], case_date: date) -> list[dict]:
        result: list[dict] = []
        for assignment in assignments:
            if assignment.personnel_role == PersonnelRole.HARVESTER:
                continue
            rule = self._resolve_rule(assignment.personnel_role, assignment.multiplier, case_date)
            result.append(
                {
                    "personnel_id": assignment.personnel_id,
                    "personnel_role": assignment.personnel_role,
                    "multiplier": assignment.multiplier,
                    "amount_usd": Decimal(rule.amount_usd),
                }
            )
        return result
