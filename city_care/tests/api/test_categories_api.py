from __future__ import annotations

import pytest
from django.urls import reverse

from core.reports.models import Category, Department


def _create_department(name: str) -> Department:
    return Department.objects.create(name=name, email=f"{name.lower()}@city.gov", phone="11900000000")


def _category_payload(department: Department, suffix: str) -> dict[str, str]:
    return {
        "name": f"Categoria {suffix}",
        "slug": f"categoria-{suffix}",
        "description": "Categoria de testes",
        "department_id": department.id,
    }


@pytest.mark.django_db
def test_category_list_as_citizen(api_client, citizen_tokens, auth_header):
    department = _create_department("ObrasCat")
    Category.objects.create(name="Buracos", slug="buracos", department=department)
    token_info = citizen_tokens()

    response = api_client.get(reverse("category-list"), **auth_header(token_info["access"]))

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["code"] == "categories.list"
    assert len(body["data"]) >= 1


@pytest.mark.django_db
def test_category_filter_by_department(api_client, citizen_tokens, auth_header):
    dep_a = _create_department("DeptA")
    dep_b = _create_department("DeptB")
    Category.objects.create(name="CatA", slug="cata", department=dep_a)
    Category.objects.create(name="CatB", slug="catb", department=dep_b)
    token_info = citizen_tokens()

    response = api_client.get(
        reverse("category-list"),
        {"department": dep_a.id},
        **auth_header(token_info["access"]),
    )

    assert response.status_code == 200
    body = response.json()
    assert all(item["department"]["id"] == dep_a.id for item in body["data"])


@pytest.mark.django_db
def test_category_create_as_admin(api_client, admin_tokens, auth_header):
    department = _create_department("Infra")
    token_info = admin_tokens()

    response = api_client.post(
        reverse("category-list"),
        _category_payload(department, "infra"),
        format="json",
        **auth_header(token_info["access"]),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["code"] == "categories.create"
    assert body["data"]["name"] == "Categoria infra"


@pytest.mark.django_db
def test_category_create_as_citizen_forbidden(api_client, citizen_tokens, auth_header):
    department = _create_department("Social")
    token_info = citizen_tokens()

    response = api_client.post(
        reverse("category-list"),
        _category_payload(department, "social"),
        format="json",
        **auth_header(token_info["access"]),
    )

    assert response.status_code == 403
    assert "detail" in response.json()["errors"]


@pytest.mark.django_db
def test_category_update_as_admin(api_client, admin_tokens, auth_header):
    department = _create_department("Parks")
    category = Category.objects.create(name="Arvores", slug="arvores", department=department)
    token_info = admin_tokens()

    response = api_client.patch(
        reverse("category-detail", args=[category.id]),
        {"name": "Arvores Rev"},
        format="json",
        **auth_header(token_info["access"]),
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Arvores Rev"


@pytest.mark.django_db
def test_category_update_as_citizen_forbidden(api_client, citizen_tokens, auth_header):
    department = _create_department("Clean")
    category = Category.objects.create(name="Lixo", slug="lixo", department=department)
    token_info = citizen_tokens()

    response = api_client.patch(
        reverse("category-detail", args=[category.id]),
        {"name": "Novo nome"},
        format="json",
        **auth_header(token_info["access"]),
    )

    assert response.status_code == 403
    assert Category.objects.get(id=category.id).name == "Lixo"


@pytest.mark.django_db
def test_category_delete_as_admin(api_client, admin_tokens, auth_header):
    department = _create_department("Transito")
    category = Category.objects.create(name="Semaforos", slug="semaforos", department=department)
    token_info = admin_tokens()

    response = api_client.delete(
        reverse("category-detail", args=[category.id]),
        **auth_header(token_info["access"]),
    )

    assert response.status_code == 204
    assert not Category.objects.filter(id=category.id).exists()


@pytest.mark.django_db
def test_category_delete_as_citizen_forbidden(api_client, citizen_tokens, auth_header):
    department = _create_department("Energia")
    category = Category.objects.create(name="Iluminacao", slug="iluminacao", department=department)
    token_info = citizen_tokens()

    response = api_client.delete(
        reverse("category-detail", args=[category.id]),
        **auth_header(token_info["access"]),
    )

    assert response.status_code == 403
    assert Category.objects.filter(id=category.id).exists()

