from datetime import date
from decimal import Decimal

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, bonus_rules, cases, personnel, reports
from app.core.config import settings
from app.core.security import get_password_hash
from app.db.base import Base
from app.db.session import engine, SessionLocal
from app.models.bonus_rule import BonusRule
from app.models.enums import PersonnelRole, UserRole
from app.models.user import User

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(cases.router)
app.include_router(personnel.router)
app.include_router(bonus_rules.router)
app.include_router(reports.router)


@app.on_event("startup")
def on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.username == "admin").first():
            db.add(User(username="admin", hashed_password=get_password_hash("admin123"), role=UserRole.ADMIN))
        if not db.query(User).filter(User.username == "viewer").first():
            db.add(User(username="viewer", hashed_password=get_password_hash("viewer123"), role=UserRole.VIEWER))

        defaults = [
            (PersonnelRole.PLANTER, Decimal("1.0"), Decimal("50")),
            (PersonnelRole.PLANTER, Decimal("0.5"), Decimal("25")),
            (PersonnelRole.DHI_TECHNICIAN, Decimal("1.0"), Decimal("25")),
            (PersonnelRole.DHI_TECHNICIAN, Decimal("0.5"), Decimal("15")),
            (PersonnelRole.HARVESTER_DHI, Decimal("1.0"), Decimal("25")),
            (PersonnelRole.HARVESTER_DHI, Decimal("0.5"), Decimal("15")),
        ]
        for role, mult, amount in defaults:
            exists = (
                db.query(BonusRule)
                .filter(BonusRule.personnel_role == role, BonusRule.multiplier == mult, BonusRule.effective_from == date(2024, 1, 1))
                .first()
            )
            if not exists:
                db.add(
                    BonusRule(
                        personnel_role=role,
                        multiplier=mult,
                        amount_usd=amount,
                        effective_from=date(2024, 1, 1),
                        is_active=True,
                    )
                )
        db.commit()
    finally:
        db.close()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
