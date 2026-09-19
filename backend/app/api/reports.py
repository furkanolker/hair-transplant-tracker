from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import require_admin
from app.models.case import Case
from app.models.case_bonus_item import CaseBonusItem
from app.models.personnel import Personnel
from app.schemas.report import MonthlyReportSummary, PersonnelReportSummary
from app.services.report_service import build_monthly_report_pdf

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/monthly", response_model=MonthlyReportSummary)
def monthly_report(start_date: date, end_date: date, db: Session = Depends(get_db), _: object = Depends(require_admin)) -> MonthlyReportSummary:
    if start_date > end_date:
        raise HTTPException(status_code=422, detail="Invalid date range")

    cases = db.query(Case).filter(and_(Case.case_date >= start_date, Case.case_date <= end_date)).all()
    total_cases = len(cases)
    total_grafts = sum(c.graft_count for c in cases)

    type_counts: dict[str, int] = {}
    for c in cases:
        key = c.transplant_type.value
        type_counts[key] = type_counts.get(key, 0) + 1

    case_ids = [c.id for c in cases]
    bonus_rows = []
    if case_ids:
        bonus_rows = db.query(CaseBonusItem, Personnel).join(Personnel, Personnel.id == CaseBonusItem.personnel_id).filter(CaseBonusItem.case_id.in_(case_ids)).all()

    personnel_totals: dict[str, Decimal] = {}
    total_bonus = Decimal("0")
    for item, person in bonus_rows:
        amount = Decimal(item.amount_usd)
        total_bonus += amount
        personnel_totals[person.full_name] = personnel_totals.get(person.full_name, Decimal("0")) + amount

    month_label = f"{start_date.year}-{start_date.month:02d}"
    return MonthlyReportSummary(
        month=month_label,
        total_cases=total_cases,
        total_grafts=total_grafts,
        total_bonus=total_bonus,
        case_type_counts=type_counts,
        personnel_bonus_totals=personnel_totals,
    )


@router.get("/personnel", response_model=PersonnelReportSummary)
def personnel_report(personnel_id: int, start_date: date, end_date: date, db: Session = Depends(get_db), _: object = Depends(require_admin)) -> PersonnelReportSummary:
    person = db.get(Personnel, personnel_id)
    if not person:
        raise HTTPException(status_code=404, detail="Personnel not found")

    role_case_counts: dict[str, int] = {"HARVESTER": 0, "PLANTER": 0, "TECHNICIAN1": 0, "TECHNICIAN2": 0}
    cases = (
        db.query(Case)
        .filter(and_(Case.case_date >= start_date, Case.case_date <= end_date))
        .filter(
            (Case.harvester_id == personnel_id)
            | (Case.planter_id == personnel_id)
            | (Case.technician1_id == personnel_id)
            | (Case.technician2_id == personnel_id)
        )
        .all()
    )

    for c in cases:
        if c.harvester_id == personnel_id:
            role_case_counts["HARVESTER"] += 1
        if c.planter_id == personnel_id:
            role_case_counts["PLANTER"] += 1
        if c.technician1_id == personnel_id:
            role_case_counts["TECHNICIAN1"] += 1
        if c.technician2_id == personnel_id:
            role_case_counts["TECHNICIAN2"] += 1

    total_grafts = sum(c.graft_count for c in cases)
    total_bonus = (
        db.query(func.coalesce(func.sum(CaseBonusItem.amount_usd), 0))
        .filter(and_(CaseBonusItem.personnel_id == personnel_id, CaseBonusItem.case_id.in_([c.id for c in cases] or [-1])))
        .scalar()
    )

    return PersonnelReportSummary(
        personnel_id=person.id,
        personnel_name=person.full_name,
        case_count=len(cases),
        role_case_counts=role_case_counts,
        total_grafts=total_grafts,
        total_bonus=Decimal(total_bonus),
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/monthly/pdf")
def monthly_report_pdf(start_date: date, end_date: date, db: Session = Depends(get_db), _: object = Depends(require_admin)) -> Response:
    summary = monthly_report(start_date=start_date, end_date=end_date, db=db)
    pdf_bytes = build_monthly_report_pdf(
        title="Aylık Prim Raporu",
        start_date=start_date,
        end_date=end_date,
        total_cases=summary.total_cases,
        total_grafts=summary.total_grafts,
        personnel_totals=summary.personnel_bonus_totals,
        total_bonus=summary.total_bonus,
    )
    return Response(content=pdf_bytes, media_type="application/pdf")
