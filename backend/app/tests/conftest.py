import os
from datetime import date
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["SECRET_KEY"] = "test-secret"

from app.core.security import get_password_hash
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.bonus_rule import BonusRule
from app.models.enums import PersonnelRole, UserRole
from app.models.user import User

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_database() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        db.add(User(username="admin", hashed_password=get_password_hash("admin123"), role=UserRole.ADMIN, is_active=True))
        db.add(User(username="viewer", hashed_password=get_password_hash("viewer123"), role=UserRole.VIEWER, is_active=True))

        rules = [
            (PersonnelRole.PLANTER, Decimal("1.0"), Decimal("50")),
            (PersonnelRole.PLANTER, Decimal("0.5"), Decimal("25")),
            (PersonnelRole.DHI_TECHNICIAN, Decimal("1.0"), Decimal("25")),
            (PersonnelRole.DHI_TECHNICIAN, Decimal("0.5"), Decimal("15")),
            (PersonnelRole.HARVESTER_DHI, Decimal("1.0"), Decimal("25")),
            (PersonnelRole.HARVESTER_DHI, Decimal("0.5"), Decimal("15")),
        ]
        for role, mult, amount in rules:
            db.add(BonusRule(personnel_role=role, multiplier=mult, amount_usd=amount, effective_from=date(2024, 1, 1), is_active=True))

        db.commit()
    finally:
        db.close()


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def login_token(client: TestClient, username: str, password: str) -> str:
    response = client.post("/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture()
def admin_token(client: TestClient) -> str:
    return login_token(client, "admin", "admin123")


@pytest.fixture()
def viewer_token(client: TestClient) -> str:
    return login_token(client, "viewer", "viewer123")


def auth_header(token: str) -> dict[str, str]:
    scheme = "Bearer"
    return {"Authorization": scheme + " " + token}
