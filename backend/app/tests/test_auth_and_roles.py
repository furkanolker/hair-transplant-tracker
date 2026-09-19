from datetime import date, timedelta

from app.models.enums import PersonnelRole, TransplantType

from .conftest import auth_header


def create_personnel(client, admin_token):
    p1 = client.post(
        "/personnel",
        json={"full_name": "Ekimci One", "role": PersonnelRole.PLANTER.value, "passport_number": "P1234"},
        headers=auth_header(admin_token),
    )
    p2 = client.post(
        "/personnel",
        json={"full_name": "Dizimci One", "role": PersonnelRole.DHI_TECHNICIAN.value, "passport_number": "P5678"},
        headers=auth_header(admin_token),
    )
    p3 = client.post(
        "/personnel",
        json={"full_name": "Dizimci Two", "role": PersonnelRole.HARVESTER_DHI.value, "passport_number": "P9911"},
        headers=auth_header(admin_token),
    )
    assert p1.status_code == 201
    assert p2.status_code == 201
    assert p3.status_code == 201
    return p1.json()["id"], p2.json()["id"], p3.json()["id"]


def test_admin_login(client):
    res = client.post("/auth/login", json={"username": "admin", "password": "admin123"})
    assert res.status_code == 200
    assert "access_token" in res.json()


def test_viewer_login(client):
    res = client.post("/auth/login", json={"username": "viewer", "password": "viewer123"})
    assert res.status_code == 200


def test_viewer_cannot_create_case(client, admin_token, viewer_token):
    planter_id, t1_id, t2_id = create_personnel(client, admin_token)
    res = client.post(
        "/cases",
        json={
            "case_date": str(date.today()),
            "transplant_type": TransplantType.HAIR.value,
            "graft_count": 1000,
            "planter_id": planter_id,
            "technician1_id": t1_id,
            "technician2_id": t2_id,
        },
        headers=auth_header(viewer_token),
    )
    assert res.status_code == 403


def test_viewer_cannot_delete_case(client, admin_token, viewer_token):
    planter_id, t1_id, t2_id = create_personnel(client, admin_token)
    create_res = client.post(
        "/cases",
        json={
            "case_date": str(date.today()),
            "transplant_type": TransplantType.HAIR.value,
            "graft_count": 1000,
            "planter_id": planter_id,
            "technician1_id": t1_id,
            "technician2_id": t2_id,
        },
        headers=auth_header(admin_token),
    )
    assert create_res.status_code == 201
    case_id = create_res.json()["id"]

    delete_res = client.delete(f"/cases/{case_id}", headers=auth_header(viewer_token))
    assert delete_res.status_code == 403


def test_viewer_only_current_month_cases(client, admin_token, viewer_token):
    planter_id, t1_id, t2_id = create_personnel(client, admin_token)
    old_date = date.today() - timedelta(days=40)
    current_date = date.today()

    old_case = client.post(
        "/cases",
        json={
            "case_date": str(old_date),
            "transplant_type": TransplantType.HAIR.value,
            "graft_count": 1200,
            "planter_id": planter_id,
            "technician1_id": t1_id,
            "technician2_id": t2_id,
        },
        headers=auth_header(admin_token),
    )
    now_case = client.post(
        "/cases",
        json={
            "case_date": str(current_date),
            "transplant_type": TransplantType.BEARD.value,
            "graft_count": 600,
            "planter_id": planter_id,
            "technician1_id": t1_id,
            "technician2_id": t2_id,
        },
        headers=auth_header(admin_token),
    )
    assert old_case.status_code == 201
    assert now_case.status_code == 201

    list_res = client.get("/cases", headers=auth_header(viewer_token))
    assert list_res.status_code == 200
    assert len(list_res.json()) == 1


def test_viewer_cannot_get_past_data_with_query(client, admin_token, viewer_token):
    start = (date.today() - timedelta(days=60)).replace(day=1)
    end = start + timedelta(days=20)
    res = client.get(f"/cases?start_date={start}&end_date={end}", headers=auth_header(viewer_token))
    assert res.status_code == 403


def test_viewer_cannot_access_personnel_endpoint(client, viewer_token):
    res = client.get("/personnel", headers=auth_header(viewer_token))
    assert res.status_code == 403


def test_viewer_cannot_see_passport_number(client, admin_token, viewer_token):
    create_personnel(client, admin_token)
    res = client.get("/personnel", headers=auth_header(viewer_token))
    assert res.status_code == 403
