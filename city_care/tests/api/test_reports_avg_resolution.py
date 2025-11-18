from __future__ import annotations

from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from core.reports.models import Category, Department, Report, ReportStatus, Tag


def _setup_category():
    department = Department.objects.create(name="AvgDept", email="avg@city.gov", phone="11912121212")
    category = Category.objects.create(name="AvgCat", slug="avg-cat", department=department)
    tag = Tag.objects.create(name="AvgTag", slug="avg-tag")
    return category, tag


def _payload(category: Category, tag: Tag, latitude: str, longitude: str) -> dict[str, object]:
    return {
        "category_id": category.id,
        "title": "Relatorio resolvido",
        "description": "Descricao teste",
        "priority": "HIGH",
        "address": "Rua Z",
        "neighborhood": "Bairro Z",
        "latitude": latitude,
        "longitude": longitude,
        "tags": [tag.id],
    }


@pytest.mark.django_db
def test_reports_avg_resolution_admin_success(api_client, citizen_tokens, admin_tokens, auth_header):
    category, tag = _setup_category()
    citizen_info = citizen_tokens()
    create_resp = api_client.post(
        reverse("report-list"),
        _payload(category, tag, "30.000001", "-30.000001"),
        format="json",
        **auth_header(citizen_info["access"]),
    )
    report = Report.objects.get(pk=create_resp.json()["data"]["id"])
    report.status = ReportStatus.CONCLUIDO
    report.created_at = timezone.now() - timedelta(days=5)
    report.last_status_at = timezone.now()
    report.save(update_fields=["status", "created_at", "last_status_at"])

    admin_info = admin_tokens()
    response = api_client.get(reverse("report-average-resolution"), **auth_header(admin_info["access"]))

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["code"] == "reports.avg_resolution"
    assert isinstance(body["data"]["results"], list)


@pytest.mark.django_db
def test_reports_avg_resolution_citizen_forbidden(api_client, citizen_tokens, auth_header):
    citizen_info = citizen_tokens()

    response = api_client.get(reverse("report-average-resolution"), **auth_header(citizen_info["access"]))

    assert response.status_code == 403
    assert "detail" in response.json()["errors"]

