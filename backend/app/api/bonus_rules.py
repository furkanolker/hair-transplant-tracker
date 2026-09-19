from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.deps import require_admin
from app.models.bonus_rule import BonusRule
from app.schemas.bonus_rule import BonusRuleCreate, BonusRuleResponse, BonusRuleUpdate

router = APIRouter(prefix="/bonus-rules", tags=["bonus-rules"])


@router.get("", response_model=list[BonusRuleResponse])
def list_rules(db: Session = Depends(get_db), _: object = Depends(require_admin)) -> list[BonusRuleResponse]:
    rows = db.query(BonusRule).order_by(BonusRule.effective_from.desc(), BonusRule.id.desc()).all()
    return [BonusRuleResponse.model_validate(r) for r in rows]


@router.post("", response_model=BonusRuleResponse, status_code=status.HTTP_201_CREATED)
def create_rule(payload: BonusRuleCreate, db: Session = Depends(get_db), _: object = Depends(require_admin)) -> BonusRuleResponse:
    row = BonusRule(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return BonusRuleResponse.model_validate(row)


@router.put("/{rule_id}", response_model=BonusRuleResponse)
def update_rule(rule_id: int, payload: BonusRuleUpdate, db: Session = Depends(get_db), _: object = Depends(require_admin)) -> BonusRuleResponse:
    row = db.get(BonusRule, rule_id)
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bonus rule not found")
    for key, value in payload.model_dump().items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return BonusRuleResponse.model_validate(row)
