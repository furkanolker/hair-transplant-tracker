from datetime import date

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.models.case import Case


class CaseRepository:
    def __init__(self, db: Session):
        self.db = db

    def next_case_number(self) -> int:
        max_num = self.db.execute(select(func.max(Case.case_number))).scalar_one_or_none()
        return (max_num or 0) + 1

    def get(self, case_id: int) -> Case | None:
        return self.db.get(Case, case_id)

    def list_by_date_range(self, start_date: date, end_date: date) -> list[Case]:
        stmt = select(Case).where(and_(Case.case_date >= start_date, Case.case_date <= end_date)).order_by(Case.case_date.desc(), Case.id.desc())
        return list(self.db.execute(stmt).scalars().all())

    def create(self, case: Case) -> Case:
        self.db.add(case)
        self.db.flush()
        self.db.refresh(case)
        return case

    def delete(self, case: Case) -> None:
        self.db.delete(case)
