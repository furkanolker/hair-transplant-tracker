from datetime import date
from decimal import Decimal

import pytest

from app.models.enums import PersonnelRole, TransplantType
from app.services.multiplier_service import get_default_multiplier, validate_multiplier

from .conftest import auth_header


def test_default_multiplier_rules():
    assert get_default_multiplier(TransplantType.BEARD) == Decimal("0.5")
    assert get_default_multiplier(TransplantType.EYEBROW) == Decimal("0.5")
    assert get_default_multiplier(TransplantType.HAIR) == Decimal("1.0")
    assert get_default_multiplier(TransplantType.HAIR_BEARD) == Decimal("1.0")


def test_invalid_multiplier_rejected():
    with pytest.raises(ValueError):
        validate_multiplier(Decimal("0.7"))


def _seed_personnel(client, admin_token):
    planter = client.post("/personnel", json={"full_name": "Ekimci", "role": PersonnelRole.PLANTER.value}, headers=auth_header(admin_token)).json()
    tech1 = client.post("/personnel", json={"full_name": "Dizimci 1", "role": PersonnelRole.DHI_TECHNICIAN.value}, headers=auth_header(admin_token)).json()
    tech2 = client.post("/personnel", json={"full_name": "Dizimci 2", "role": PersonnelRole.DHI_TECHNICIAN.value}, headers=auth_header(admin_token)).json()
    inactive = client.post("/personnel", json={"full_name": "Pasif", "role": PersonnelRole.PLANTER.value}, headers=auth_header(admin_token)).json()
    client.patch(f"/personnel/{inactive['id']}/status", json={"is_active": False}, headers=auth_header(admin_token))
    return planter["id"], tech1["id"], tech2["id"], inactive["id"]


def test_two_technicians_bonus_calculated_separately(client, admin_token):
    planter_id, tech1_id, tech2_id, _ = _seed_personnel(client, admin_token)
    res = client.post(
        "/cases",
        json={
            "case_date": str(date.today()),
            "transplant_type": TransplantType.HAIR.value,
            "multiplier": "1.0",
            "graft_count": 2000,
            "planter_id": planter_id,
            "technician1_id": tech1_id,
            "technician2_id": tech2_id,
        },
        headers=auth_header(admin_token),
    )
    assert res.status_code == 201

    report = client.get(
        f"/reports/monthly?start_date={date.today().replace(day=1)}&end_date={date.today()}",
        headers=auth_header(admin_token),
    )
    assert report.status_code == 200
    assert Decimal(report.json()["total_bonus"]) == Decimal("100")


def test_planter_and_technician_bonus_for_half_multiplier(client, admin_token):
    planter_id, tech1_id, tech2_id, _ = _seed_personnel(client, admin_token)
    res = client.post(
        "/cases",
        json={
            "case_date": str(date.today()),
            "transplant_type": TransplantType.BEARD.value,
            "multiplier": "0.5",
            "graft_count": 900,
            "planter_id": planter_id,
            "technician1_id": tech1_id,
            "technician2_id": tech2_id,
        },
        headers=auth_header(admin_token),
    )
    assert res.status_code == 201

    report = client.get(
        f"/reports/monthly?start_date={date.today().replace(day=1)}&end_date={date.today()}",
        headers=auth_header(admin_token),
    )
    assert report.status_code == 200
    assert Decimal(report.json()["total_bonus"]) == Decimal("55")


def test_inactive_personnel_cannot_be_selected(client, admin_token):
    _, tech1_id, tech2_id, inactive_id = _seed_personnel(client, admin_token)
    res = client.post(
        "/cases",
        json={
            "case_date": str(date.today()),
            "transplant_type": TransplantType.HAIR.value,
            "graft_count": 1000,
            "planter_id": inactive_id,
            "technician1_id": tech1_id,
            "technician2_id": tech2_id,
        },
        headers=auth_header(admin_token),
    )
    assert res.status_code == 422
