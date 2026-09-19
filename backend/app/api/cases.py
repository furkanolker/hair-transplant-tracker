from calendar import monthrange
from datetime import date, datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import get_current_user, require_admin
from app.models.case import Case
from app.models.case_bonus_item import CaseBonusItem
from app.models.enums import PersonnelRole, UserRole
from app.models.personnel import Personnel
from app.models.user import User
from app.repositories.case_repository import CaseRepository
from app.schemas.case import CaseCreate, CaseResponse, CaseUpdate
from app.services.bonus_service import BonusAssignment, BonusCalculator
from app.services.multiplier_service import get_default_multiplier, validate_multiplier

router = APIRouter(prefix="/cases", tags=["cases"])


def _current_month_range() -> tuple[date, date]:
    now = datetime.utcnow().date()
    start = date(now.year, now.month, 1)
    end = date(now.year, now.month, monthrange(now.year, now.month)[1])
    return start, end


def _validate_distinct_personnel(payload: CaseCreate | CaseUpdate) -> None:
    values = [payload.harvester_id, payload.planter_id, payload.technician1_id, payload.technician2_id]
    values = [v for v in values if v is not None]
    if len(values) != len(set(values)):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Same person cannot be assigned to multiple case positions")


def _validate_active_personnel(db: Session, ids: list[int]) -> dict[int, Personnel]:
    if not ids:
        return {}
    rows = db.query(Personnel).filter(Personnel.id.in_(ids)).all()
    found = {r.id: r for r in rows}
    for pid in ids:
        person = found.get(pid)
        if not person:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Personnel {pid} does not exist")
        if not person.is_active:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Personnel {pid} is inactive")
    return found


def _build_assignments(c: Case, personnel_map: dict[int, Personnel]) -> list[BonusAssignment]:
    assignments: list[BonusAssignment] = []
    if c.planter_id:
        assignments.append(BonusAssignment(c.planter_id, PersonnelRole.PLANTER, Decimal(c.multiplier)))
    if c.technician1_id:
        role = personnel_map[c.technician1_id].role
        if role in {PersonnelRole.DHI_TECHNICIAN, PersonnelRole.HARVESTER_DHI}:
            assignments.append(BonusAssignment(c.technician1_id, role, Decimal(c.multiplier)))
    if c.technician2_id:
        role = personnel_map[c.technician2_id].role
        if role in {PersonnelRole.DHI_TECHNICIAN, PersonnelRole.HARVESTER_DHI}:
            assignments.append(BonusAssignment(c.technician2_id, role, Decimal(c.multiplier)))
    return assignments


def _sync_bonus_snapshot(db: Session, c: Case, personnel_map: dict[int, Personnel]) -> None:
    db.query(CaseBonusItem).filter(CaseBonusItem.case_id == c.id).delete()
    calc = BonusCalculator(db)
    for item in calc.calculate_case_bonus(_build_assignments(c, personnel_map), c.case_date):
        db.add(CaseBonusItem(case_id=c.id, **item))


@router.get("", response_model=list[CaseResponse])
def list_cases(
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[CaseResponse]:
    repo = CaseRepository(db)
    if user.role == UserRole.VIEWER:
        cur_start, cur_end = _current_month_range()
        if start_date or end_date:
            if start_date != cur_start or end_date != cur_end:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Viewer can only access current month")
        start_date, end_date = cur_start, cur_end
    else:
        if not start_date or not end_date:
            now = datetime.utcnow().date()
            start_date = start_date or date(now.year, now.month, 1)
            end_date = end_date or now
    rows = repo.list_by_date_range(start_date, end_date)
    return [CaseResponse.model_validate(row) for row in rows]


@router.post("", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
def create_case(payload: CaseCreate, db: Session = Depends(get_db), _: object = Depends(require_admin)) -> CaseResponse:
    _validate_distinct_personnel(payload)
    multiplier = payload.multiplier or get_default_multiplier(payload.transplant_type)
    validate_multiplier(multiplier)
    personnel_ids = [pid for pid in [payload.harvester_id, payload.planter_id, payload.technician1_id, payload.technician2_id] if pid is not None]
    personnel_map = _validate_active_personnel(db, personnel_ids)

    repo = CaseRepository(db)
    row = Case(
        case_number=repo.next_case_number(),
        case_date=payload.case_date,
        patient_name=payload.patient_name,
        transplant_type=payload.transplant_type,
        multiplier=multiplier,
        graft_count=payload.graft_count,
        harvester_id=payload.harvester_id,
        planter_id=payload.planter_id,
        technician1_id=payload.technician1_id,
        technician2_id=payload.technician2_id,
        notes=payload.notes,
    )
    repo.create(row)
    _sync_bonus_snapshot(db, row, personnel_map)
    db.commit()
    db.refresh(row)
    return CaseResponse.model_validate(row)


@router.get("/{case_id}", response_model=CaseResponse)
def get_case(case_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> CaseResponse:
    row = db.get(Case, case_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    if user.role == UserRole.VIEWER:
        cur_start, cur_end = _current_month_range()
        if not (cur_start <= row.case_date <= cur_end):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Viewer can only access current month")
    return CaseResponse.model_validate(row)


@router.put("/{case_id}", response_model=CaseResponse)
def update_case(case_id: int, payload: CaseUpdate, db: Session = Depends(get_db), _: object = Depends(require_admin)) -> CaseResponse:
    row = db.get(Case, case_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    _validate_distinct_personnel(payload)

    multiplier = payload.multiplier or get_default_multiplier(payload.transplant_type)
    validate_multiplier(multiplier)
    personnel_ids = [pid for pid in [payload.harvester_id, payload.planter_id, payload.technician1_id, payload.technician2_id] if pid is not None]
    personnel_map = _validate_active_personnel(db, personnel_ids)

    for key, value in payload.model_dump().items():
        setattr(row, key, value)
    row.multiplier = multiplier

    _sync_bonus_snapshot(db, row, personnel_map)
    db.commit()
    db.refresh(row)
    return CaseResponse.model_validate(row)


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_case(case_id: int, db: Session = Depends(get_db), _: object = Depends(require_admin)) -> None:
    row = db.get(Case, case_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")
    db.delete(row)
    db.commit()
    return None
