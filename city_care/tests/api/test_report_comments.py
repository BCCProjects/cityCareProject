from __future__ import annotations

import pytest
from django.urls import reverse

from core.reports.models import Category, Department, Tag


def _prepare_category():
    department = Department.objects.create(name="Comentarios", email="comentarios@city.gov", phone="11900000000")
    category = Category.objects.create(name="Comentarios Cat", slug="comentarios-cat", department=department)
    tag = Tag.objects.create(name="Comentarios Tag", slug="comentarios-tag")
    return category, tag


def _report_payload(category: Category, tags: list[int], **overrides) -> dict[str, object]:
    payload: dict[str, object] = {
        "category_id": category.id,
        "title": overrides.pop("title", "Reportagem comentario"),
        "description": overrides.pop("description", "Descricao"),
        "priority": overrides.pop("priority", "MEDIUM"),
        "address": overrides.pop("address", "Rua B, 456"),
        "neighborhood": overrides.pop("neighborhood", "Bairro"),
        "latitude": overrides.pop("latitude", "14.000001"),
        "longitude": overrides.pop("longitude", "-14.000001"),
        "tags": tags,
    }
    payload.update(overrides)
    return payload


@pytest.mark.django_db
def test_add_comment_success(api_client, citizen_tokens, auth_header):
    category, tag = _prepare_category()
    token_info = citizen_tokens()
    create_response = api_client.post(
        reverse("report-list"),
        _report_payload(category, [tag.id], latitude="11.000001", longitude="-11.000001"),
        format="json",
        **auth_header(token_info["access"]),
    )
    assert create_response.status_code == 201, create_response.json()
    report_id = create_response.json()["data"]["id"]

    response = api_client.post(
        reverse("report-add-comment", kwargs={"pk": report_id}),
        {"message": "Comentario teste"},
        format="json",
        **auth_header(token_info["access"]),
    )

    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    assert body["code"] == "reports.comments.create"
    assert body["data"]["message"] == "Comentario teste"
    assert "citizen_name" in body["data"]


@pytest.mark.django_db
def test_add_comment_missing_message(api_client, citizen_tokens, auth_header):
    category, tag = _prepare_category()
    token_info = citizen_tokens()
    create_response = api_client.post(
        reverse("report-list"),
        _report_payload(category, [tag.id], latitude="12.000001", longitude="-12.000001"),
        format="json",
        **auth_header(token_info["access"]),
    )
    assert create_response.status_code == 201, create_response.json()
    report_id = create_response.json()["data"]["id"]

    response = api_client.post(
        reverse("report-add-comment", kwargs={"pk": report_id}),
        {},
        format="json",
        **auth_header(token_info["access"]),
    )

    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False
    assert "errors" in body


@pytest.mark.django_db
def test_add_comment_by_other_citizen_returns_not_found(api_client, citizen_tokens, auth_header):
    category, tag = _prepare_category()
    owner_token = citizen_tokens()
    other_token = citizen_tokens()
    create_response = api_client.post(
        reverse("report-list"),
        _report_payload(category, [tag.id], latitude="13.000001", longitude="-13.000001"),
        format="json",
        **auth_header(owner_token["access"]),
    )
    assert create_response.status_code == 201, create_response.json()
    report_id = create_response.json()["data"]["id"]

    response = api_client.post(
        reverse("report-add-comment", kwargs={"pk": report_id}),
        {"message": "Outro usuario"},
        format="json",
        **auth_header(other_token["access"]),
    )

    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False
