from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import require_admin
from app.models.personnel import Personnel
from app.schemas.personnel import PersonnelAdminResponse, PersonnelCreate, PersonnelResponse, PersonnelStatusPatch, PersonnelUpdate
from app.services.passport_service import decrypt_passport, encrypt_passport, mask_passport

router = APIRouter(prefix="/personnel", tags=["personnel"])


@router.get("", response_model=list[PersonnelAdminResponse])
def list_personnel(db: Session = Depends(get_db), _: object = Depends(require_admin)) -> list[PersonnelAdminResponse]:
    rows = db.query(Personnel).order_by(Personnel.full_name.asc()).all()
    items: list[PersonnelAdminResponse] = []
    for row in rows:
        raw_passport = decrypt_passport(row.passport_number_encrypted)
        items.append(
            PersonnelAdminResponse(
                id=row.id,
                full_name=row.full_name,
                role=row.role,
                arrival_date=row.arrival_date,
                is_active=row.is_active,
                notes=row.notes,
                created_at=row.created_at,
                passport_number_masked=mask_passport(raw_passport),
            )
        )
    return items


@router.post("", response_model=PersonnelResponse, status_code=status.HTTP_201_CREATED)
def create_personnel(payload: PersonnelCreate, db: Session = Depends(get_db), _: object = Depends(require_admin)) -> PersonnelResponse:
    row = Personnel(
        full_name=payload.full_name,
        role=payload.role,
        passport_number_encrypted=encrypt_passport(payload.passport_number),
        arrival_date=payload.arrival_date,
        notes=payload.notes,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return PersonnelResponse.model_validate(row)


@router.put("/{personnel_id}", response_model=PersonnelResponse)
def update_personnel(personnel_id: int, payload: PersonnelUpdate, db: Session = Depends(get_db), _: object = Depends(require_admin)) -> PersonnelResponse:
    row = db.get(Personnel, personnel_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Personnel not found")
    row.full_name = payload.full_name
    row.role = payload.role
    row.passport_number_encrypted = encrypt_passport(payload.passport_number)
    row.arrival_date = payload.arrival_date
    row.notes = payload.notes
    row.is_active = payload.is_active
    db.commit()
    db.refresh(row)
    return PersonnelResponse.model_validate(row)


@router.patch("/{personnel_id}/status", response_model=PersonnelResponse)
def patch_status(personnel_id: int, payload: PersonnelStatusPatch, db: Session = Depends(get_db), _: object = Depends(require_admin)) -> PersonnelResponse:
    row = db.get(Personnel, personnel_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Personnel not found")
    row.is_active = payload.is_active
    db.commit()
    db.refresh(row)
    return PersonnelResponse.model_validate(row)
