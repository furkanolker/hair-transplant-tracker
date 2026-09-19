from datetime import date

from app.models.enums import PersonnelRole, TransplantType

from .conftest import auth_header


def test_monthly_pdf_report_generated(client, admin_token):
    planter = client.post("/personnel", json={"full_name": "Ekimci", "role": PersonnelRole.PLANTER.value}, headers=auth_header(admin_token)).json()
    tech1 = client.post("/personnel", json={"full_name": "Dizimci 1", "role": PersonnelRole.DHI_TECHNICIAN.value}, headers=auth_header(admin_token)).json()
    tech2 = client.post("/personnel", json={"full_name": "Dizimci 2", "role": PersonnelRole.DHI_TECHNICIAN.value}, headers=auth_header(admin_token)).json()

    create_case = client.post(
        "/cases",
        json={
            "case_date": str(date.today()),
            "transplant_type": TransplantType.HAIR.value,
            "graft_count": 1000,
            "planter_id": planter["id"],
            "technician1_id": tech1["id"],
            "technician2_id": tech2["id"],
        },
        headers=auth_header(admin_token),
    )
    assert create_case.status_code == 201

    res = client.get(
        f"/reports/monthly/pdf?start_date={date.today().replace(day=1)}&end_date={date.today()}",
        headers=auth_header(admin_token),
    )
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("application/pdf")
    assert res.content.startswith(b"%PDF")
