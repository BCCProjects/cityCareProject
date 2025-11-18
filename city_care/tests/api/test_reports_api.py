from __future__ import annotations

from datetime import timedelta

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone

from core.reports.models import Category, Department, Report, ReportStatus, Tag


def _create_department_and_category(suffix: str) -> tuple[Department, Category]:
    department = Department.objects.create(
        name=f"Departamento {suffix}",
        email=f"dep{suffix}@city.gov",
        phone="11900000000",
    )
    category = Category.objects.create(
        name=f"Categoria {suffix}",
        slug=f"categoria-{suffix}",
        department=department,
    )
    return department, category


def _create_tag(name: str) -> Tag:
    return Tag.objects.create(name=name, slug=name.lower().replace(" ", "-"))


def _report_payload(category: Category, tags: list[int], **overrides) -> dict[str, object]:
    payload: dict[str, object] = {
        "category_id": category.id,
        "title": overrides.pop("title", "Buraco na via"),
        "description": overrides.pop("description", "Descricao do problema"),
        "priority": overrides.pop("priority", "HIGH"),
        "address": overrides.pop("address", "Rua A, 123"),
        "neighborhood": overrides.pop("neighborhood", "Centro"),
        "latitude": overrides.pop("latitude", "1.234567"),
        "longitude": overrides.pop("longitude", "-45.678901"),
        "tags": tags,
    }
    payload.update(overrides)
    return payload


def _image_file(name: str) -> SimpleUploadedFile:
    return SimpleUploadedFile(name, b"\x89PNG\r\n\x1a\n", content_type="image/png")


def _list_results(response):
    data = response.json()["data"]
    if isinstance(data, dict) and "results" in data:
        return data["results"]
    return data


@pytest.mark.django_db
def test_report_create_success(api_client, citizen_tokens, auth_header):
    _, category = _create_department_and_category("create-success")
    tag = _create_tag("Buraco")
    token_info = citizen_tokens()

    response = api_client.post(
        reverse("report-list"),
        _report_payload(category, [tag.id]),
        format="json",
        **auth_header(token_info["access"]),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["code"] == "reports.create"
    assert body["data"]["category"]["id"] == category.id


@pytest.mark.django_db
def test_report_create_with_attachments(api_client, citizen_tokens, auth_header, settings):
    settings.USE_SUPABASE_ATTACHMENTS = False
    _, category = _create_department_and_category("attachments")
    tag = _create_tag("Anexo")
    token_info = citizen_tokens()
    payload = _report_payload(category, [tag.id])
    payload["attachments"] = [_image_file("foto1.png"), _image_file("foto2.png")]

    response = api_client.post(
        reverse("report-list"),
        payload,
        format="multipart",
        **auth_header(token_info["access"]),
    )

    assert response.status_code == 201
    body = response.json()
    assert len(body["data"]["attachments"]) == 2


@pytest.mark.django_db
def test_report_create_attachment_limit_error(api_client, citizen_tokens, auth_header, settings):
    settings.USE_SUPABASE_ATTACHMENTS = False
    _, category = _create_department_and_category("attach-limit")
    tag = _create_tag("Limite")
    token_info = citizen_tokens()
    payload = _report_payload(category, [tag.id])
    payload["attachments"] = [_image_file(f"f{i}.png") for i in range(6)]

    response = api_client.post(
        reverse("report-list"),
        payload,
        format="multipart",
        **auth_header(token_info["access"]),
    )

    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False
    assert "attachments" in body["errors"]


@pytest.mark.django_db
def test_report_create_attachment_invalid_type(api_client, citizen_tokens, auth_header, settings):
    settings.USE_SUPABASE_ATTACHMENTS = False
    _, category = _create_department_and_category("attach-invalid")
    tag = _create_tag("Arquivo")
    token_info = citizen_tokens()
    payload = _report_payload(category, [tag.id])
    payload["attachments"] = [
        SimpleUploadedFile("doc.txt", b"plain text", content_type="text/plain"),
    ]

    response = api_client.post(
        reverse("report-list"),
        payload,
        format="multipart",
        **auth_header(token_info["access"]),
    )

    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False
    assert "attachments" in body["errors"]


@pytest.mark.django_db
def test_report_create_duplicate_location_same_category(api_client, citizen_tokens, auth_header):
    _, category = _create_department_and_category("duplicate")
    tag = _create_tag("Duplicado")
    token_info = citizen_tokens()
    payload = _report_payload(category, [tag.id], latitude="1.111111", longitude="-1.111111")
    first = api_client.post(
        reverse("report-list"),
        payload,
        format="json",
        **auth_header(token_info["access"]),
    )
    assert first.status_code == 201

    response = api_client.post(
        reverse("report-list"),
        payload,
        format="json",
        **auth_header(token_info["access"]),
    )

    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False
    assert "non_field_errors" in body["errors"]


@pytest.mark.django_db
def test_report_list_filters(api_client, citizen_tokens, auth_header):
    dept_a, category_a = _create_department_and_category("filter-a")
    dept_b, category_b = _create_department_and_category("filter-b")
    tag_a = _create_tag("Filtro A")
    tag_b = _create_tag("Filtro B")
    token_info = citizen_tokens()

    api_client.post(
        reverse("report-list"),
        _report_payload(category_a, [tag_a.id], priority="LOW", latitude="2.000001", longitude="-2.000001"),
        format="json",
        **auth_header(token_info["access"]),
    )
    resp_b = api_client.post(
        reverse("report-list"),
        _report_payload(category_b, [tag_b.id], priority="HIGH", latitude="3.000001", longitude="-3.000001"),
        format="json",
        **auth_header(token_info["access"]),
    )
    report_b = Report.objects.get(pk=resp_b.json()["data"]["id"])
    report_b.status = ReportStatus.CONCLUIDO
    report_b.save(update_fields=["status"])

    status_response = api_client.get(
        reverse("report-list"),
        {"status": ReportStatus.CONCLUIDO},
        **auth_header(token_info["access"]),
    )
    assert len(_list_results(status_response)) == 1

    category_response = api_client.get(
        reverse("report-list"),
        {"category": category_a.id},
        **auth_header(token_info["access"]),
    )
    assert all(item["category"]["id"] == category_a.id for item in _list_results(category_response))

    department_response = api_client.get(
        reverse("report-list"),
        {"department": dept_b.id},
        **auth_header(token_info["access"]),
    )
    assert all(item["category"]["department"]["id"] == dept_b.id for item in _list_results(department_response))

    priority_response = api_client.get(
        reverse("report-list"),
        {"priority": "LOW"},
        **auth_header(token_info["access"]),
    )
    assert all(item["priority"] == "LOW" for item in _list_results(priority_response))

    tag_response = api_client.get(
        reverse("report-list"),
        {"tag": tag_a.id},
        **auth_header(token_info["access"]),
    )
    assert all(tag_a.id in [t["id"] for t in item["tags"]] for item in _list_results(tag_response))


@pytest.mark.django_db
def test_report_list_ordering(api_client, citizen_tokens, auth_header):
    _, category = _create_department_and_category("ordering")
    tag = _create_tag("Ordenacao")
    token_info = citizen_tokens()

    resp_oldest = api_client.post(
        reverse("report-list"),
        _report_payload(category, [tag.id], latitude="4.000001", longitude="-4.000001"),
        format="json",
        **auth_header(token_info["access"]),
    )
    resp_newest = api_client.post(
        reverse("report-list"),
        _report_payload(category, [tag.id], latitude="5.000001", longitude="-5.000001"),
        format="json",
        **auth_header(token_info["access"]),
    )

    oldest = Report.objects.get(pk=resp_oldest.json()["data"]["id"])
    oldest.created_at = timezone.now() - timedelta(days=2)
    oldest.save(update_fields=["created_at"])

    response = api_client.get(
        reverse("report-list"),
        {"ordering": "created_at"},
        **auth_header(token_info["access"]),
    )

    data = _list_results(response)
    assert data[0]["id"] == oldest.id

    response_desc = api_client.get(
        reverse("report-list"),
        {"ordering": "-created_at"},
        **auth_header(token_info["access"]),
    )
    desc_results = _list_results(response_desc)
    assert desc_results[0]["id"] == resp_newest.json()["data"]["id"]


@pytest.mark.django_db
def test_report_list_as_admin_sees_all(api_client, citizen_tokens, admin_tokens, auth_header):
    _, category = _create_department_and_category("list-admin")
    tag = _create_tag("AdminList")
    citizen_one = citizen_tokens()
    citizen_two = citizen_tokens()

    api_client.post(
        reverse("report-list"),
        _report_payload(category, [tag.id], latitude="6.000001", longitude="-6.000001"),
        format="json",
        **auth_header(citizen_one["access"]),
    )
    api_client.post(
        reverse("report-list"),
        _report_payload(category, [tag.id], latitude="7.000001", longitude="-7.000001"),
        format="json",
        **auth_header(citizen_two["access"]),
    )

    admin_info = admin_tokens()
    response = api_client.get(reverse("report-list"), **auth_header(admin_info["access"]))

    assert response.status_code == 200
    assert len(_list_results(response)) >= 2


@pytest.mark.django_db
def test_report_list_as_citizen_only_theirs(api_client, citizen_tokens, auth_header):
    _, category = _create_department_and_category("list-citizen")
    tag = _create_tag("CitizenList")
    token_owner = citizen_tokens()
    token_other = citizen_tokens()

    own_resp = api_client.post(
        reverse("report-list"),
        _report_payload(category, [tag.id], latitude="8.000001", longitude="-8.000001"),
        format="json",
        **auth_header(token_owner["access"]),
    )
    api_client.post(
        reverse("report-list"),
        _report_payload(category, [tag.id], latitude="9.000001", longitude="-9.000001"),
        format="json",
        **auth_header(token_other["access"]),
    )

    response = api_client.get(reverse("report-list"), **auth_header(token_owner["access"]))

    assert response.status_code == 200
    data = _list_results(response)
    assert len(data) == 1
    assert data[0]["id"] == own_resp.json()["data"]["id"]


@pytest.mark.django_db
def test_report_detail_success(api_client, citizen_tokens, auth_header):
    _, category = _create_department_and_category("detail")
    tag = _create_tag("Detail")
    token_info = citizen_tokens()
    create_resp = api_client.post(
        reverse("report-list"),
        _report_payload(category, [tag.id], latitude="10.000001", longitude="-10.000001"),
        format="json",
        **auth_header(token_info["access"]),
    )
    report_id = create_resp.json()["data"]["id"]

    response = api_client.get(reverse("report-detail", args=[report_id]), **auth_header(token_info["access"]))

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["code"] == "reports.detail"
    assert body["data"]["id"] == report_id
