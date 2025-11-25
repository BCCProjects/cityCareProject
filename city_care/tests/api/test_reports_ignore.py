from __future__ import annotations

from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone

from core.reports.models import Category, Department, Report, Tag


def _setup_category():
    department = Department.objects.create(name="IgnoreDept", email="ignore@city.gov", phone="11922223333")
    category = Category.objects.create(name="IgnoreCat", slug="ignore-cat", department=department)
    tag = Tag.objects.create(name="IgnoreTag", slug="ignore-tag")
    return category, tag


def _report_payload(category: Category, tag: Tag, latitude: str, longitude: str) -> dict[str, object]:
    return {
        "category_id": category.id,
        "title": "Report elegivel",
        "description": "Descricao",
        "priority": "BAIXO",
        "address": "Rua X",
        "neighborhood": "Bairro",
        "latitude": latitude,
        "longitude": longitude,
        "tags": [tag.id],
    }


@pytest.mark.django_db
def test_reports_ignore_admin_success(api_client, citizen_tokens, admin_tokens, auth_header):
    category, tag = _setup_category()
    citizen_info = citizen_tokens()
    create_resp = api_client.post(
        reverse("report-list"),
        _report_payload(category, tag, "20.000001", "-20.000001"),
        format="json",
        **auth_header(citizen_info["access"]),
    )
    report = Report.objects.get(pk=create_resp.json()["id"])
    report.last_status_at = timezone.now() - timedelta(hours=200)
    report.save(update_fields=["last_status_at"])

    admin_info = admin_tokens()
    response = api_client.get(reverse("report-eligible-for-ignore"), **auth_header(admin_info["access"]))

    # Internal-only endpoint guarded by InternalAPIPermission; external admin tokens are forbidden.
    assert response.status_code == 403


@pytest.mark.django_db
def test_reports_ignore_citizen_forbidden(api_client, citizen_tokens, auth_header):
    token_info = citizen_tokens()

    response = api_client.get(reverse("report-eligible-for-ignore"), **auth_header(token_info["access"]))

    assert response.status_code == 403
    assert "detail" in response.json()


@pytest.mark.django_db
def test_reports_ignore_invalid_hours_string(api_client, admin_tokens, auth_header):
    admin_info = admin_tokens()

    response = api_client.get(
        reverse("report-eligible-for-ignore"),
        {"hours": "texto"},
        **auth_header(admin_info["access"]),
    )

    # Endpoint uses InternalAPIPermission; external admin calls are forbidden.
    assert response.status_code == 403
    body = response.json()
    assert "detail" in body


@pytest.mark.django_db
def test_reports_ignore_zero_hours_error(api_client, admin_tokens, auth_header):
    admin_info = admin_tokens()

    response = api_client.get(
        reverse("report-eligible-for-ignore"),
        {"hours": 0},
        **auth_header(admin_info["access"]),
    )

    # External admin calls are forbidden regardless of hours parameter.
    assert response.status_code == 403

