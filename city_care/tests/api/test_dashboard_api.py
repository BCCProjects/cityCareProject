from __future__ import annotations

import pytest
from django.urls import reverse

from core.reports.models import Category, Department, Tag


def _setup_category():
    department = Department.objects.create(name="DashboardDept", email="dash@city.gov", phone="11956565656")
    category = Category.objects.create(name="DashboardCat", slug="dashboard-cat", department=department)
    tag = Tag.objects.create(name="DashboardTag", slug="dashboard-tag")
    return category, tag


def _payload(category: Category, tag: Tag, latitude: str, longitude: str) -> dict[str, object]:
    return {
        "category_id": category.id,
        "title": "Ocorrencia dashboard",
        "description": "Descricao",
        "priority": "MEDIUM",
        "address": "Rua do dashboard",
        "neighborhood": "Centro Dashboard",
        "latitude": latitude,
        "longitude": longitude,
        "tags": [tag.id],
    }


@pytest.mark.django_db
def test_dashboard_admin_success(api_client, citizen_tokens, admin_tokens, auth_header):
    category, tag = _setup_category()
    citizen = citizen_tokens()
    api_client.post(
        reverse("report-list"),
        _payload(category, tag, "40.000001", "-40.000001"),
        format="json",
        **auth_header(citizen["access"]),
    )

    admin_info = admin_tokens()
    response = api_client.get(reverse("dashboard-list"), **auth_header(admin_info["access"]))

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["code"] == "dashboard.summary"
    assert "open_by_neighborhood" in body["data"]["results"]
    assert "weekly_series" in body["data"]["results"]


@pytest.mark.django_db
def test_dashboard_citizen_forbidden(api_client, citizen_tokens, auth_header):
    citizen = citizen_tokens()

    response = api_client.get(reverse("dashboard-list"), **auth_header(citizen["access"]))

    assert response.status_code == 403
    assert "detail" in response.json()["errors"]

