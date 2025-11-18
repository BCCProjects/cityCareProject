from __future__ import annotations

import pytest
from django.urls import reverse

from core.reports.models import Department


def _department_payload(name: str = "Obras") -> dict[str, str]:
    return {
        "name": name,
        "email": f"{name.lower()}@city.gov",
        "phone": "11988887777",
        "description": "Responsável por obras.",
    }


@pytest.mark.django_db
def test_department_list_as_citizen(api_client, citizen_tokens, auth_header):
    Department.objects.create(name="Obras", email="obras@city.gov", phone="11988887777")
    token_info = citizen_tokens()

    response = api_client.get(reverse("department-list"), **auth_header(token_info["access"]))

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["code"] == "departments.list"
    assert isinstance(body["data"], list)
    assert "message" in body and "data" in body and "errors" in body


@pytest.mark.django_db
def test_department_list_as_admin(api_client, admin_tokens, auth_header):
    Department.objects.create(name="Manutenção", email="manutencao@city.gov", phone="11977776666")
    token_info = admin_tokens()

    response = api_client.get(reverse("department-list"), **auth_header(token_info["access"]))

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["code"] == "departments.list"


@pytest.mark.django_db
def test_department_create_as_admin(api_client, admin_tokens, auth_header):
    token_info = admin_tokens()

    response = api_client.post(
        reverse("department-list"),
        _department_payload("Saude"),
        format="json",
        **auth_header(token_info["access"]),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["code"] == "departments.create"
    assert body["data"]["name"] == "Saude"


@pytest.mark.django_db
def test_department_create_as_citizen_forbidden(api_client, citizen_tokens, auth_header):
    token_info = citizen_tokens()

    response = api_client.post(
        reverse("department-list"),
        _department_payload("Iluminacao"),
        format="json",
        **auth_header(token_info["access"]),
    )

    assert response.status_code == 403
    assert "detail" in response.json()["errors"]


@pytest.mark.django_db
def test_department_update_as_admin(api_client, admin_tokens, auth_header):
    Department.objects.create(name="Limpeza", email="limpeza@city.gov", phone="11966665555")
    department = Department.objects.first()
    token_info = admin_tokens()

    response = api_client.patch(
        reverse("department-detail", args=[department.id]),
        {"phone": "11911112222"},
        format="json",
        **auth_header(token_info["access"]),
    )

    assert response.status_code == 200
    assert response.json()["phone"] == "11911112222"


@pytest.mark.django_db
def test_department_update_as_citizen_forbidden(api_client, citizen_tokens, auth_header):
    Department.objects.create(name="Jardim", email="jardim@city.gov", phone="11944443333")
    department = Department.objects.first()
    token_info = citizen_tokens()

    response = api_client.patch(
        reverse("department-detail", args=[department.id]),
        {"phone": "000"},
        format="json",
        **auth_header(token_info["access"]),
    )

    assert response.status_code == 403
    assert "detail" in response.json()["errors"]


@pytest.mark.django_db
def test_department_delete_as_admin(api_client, admin_tokens, auth_header):
    department = Department.objects.create(name="Transito", email="transito@city.gov", phone="11912341234")
    token_info = admin_tokens()

    response = api_client.delete(reverse("department-detail", args=[department.id]), **auth_header(token_info["access"]))

    assert response.status_code == 204
    assert Department.objects.count() == 0


@pytest.mark.django_db
def test_department_delete_as_citizen_forbidden(api_client, citizen_tokens, auth_header):
    department = Department.objects.create(name="Esportes", email="esportes@city.gov", phone="11988886666")
    token_info = citizen_tokens()

    response = api_client.delete(reverse("department-detail", args=[department.id]), **auth_header(token_info["access"]))

    assert response.status_code == 403
    assert Department.objects.filter(id=department.id).exists()

