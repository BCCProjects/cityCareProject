from __future__ import annotations

import pytest
from django.urls import reverse

from tests.utils import ensure_location


def _citizen_payload(email: str, password: str = "Senha123!") -> dict[str, str]:
    _, city, _ = ensure_location("Citizen Auth City")
    return {
        "email": email,
        "first_name": "Citizen",
        "last_name": "Example",
        "phone": "11999999999",
        "password": password,
        "city_id": city.id,
    }


@pytest.mark.django_db
def test_citizen_register_success(api_client, security_headers):
    payload = _citizen_payload("citizen_success@example.com")

    response = api_client.post(reverse("citizen-register"), payload, format="json", **security_headers)

    assert response.status_code == 201
    body = response.json()
    data = body["data"]
    assert data["email"] == payload["email"]
    assert data["first_name"] == payload["first_name"]
    assert data["city"]["id"] == payload["city_id"]
    assert "id" in data


@pytest.mark.django_db
def test_citizen_register_invalid_email(api_client, security_headers):
    payload = _citizen_payload("invalid-email")

    response = api_client.post(reverse("citizen-register"), payload, format="json", **security_headers)

    assert response.status_code == 400
    body = response.json()
    assert "email" in body["errors"]


@pytest.mark.django_db
def test_citizen_register_short_password(api_client, security_headers):
    payload = _citizen_payload("shortpass@example.com", password="short")

    response = api_client.post(reverse("citizen-register"), payload, format="json", **security_headers)

    assert response.status_code == 400
    body = response.json()
    assert "password" in body["errors"]


@pytest.mark.django_db
def test_citizen_register_missing_headers(api_client):
    payload = _citizen_payload("noheaders@example.com")

    response = api_client.post(reverse("citizen-register"), payload, format="json")

    assert response.status_code == 400
    body = response.json()
    assert "detail" in body["errors"]
    assert "Cabecalhos obrigatorios" in body["errors"]["detail"]


@pytest.mark.django_db
def test_citizen_register_duplicate_email(api_client, security_headers):
    payload = _citizen_payload("duplicate@example.com")
    first = api_client.post(reverse("citizen-register"), payload, format="json", **security_headers)
    assert first.status_code == 201

    response = api_client.post(reverse("citizen-register"), payload, format="json", **security_headers)

    assert response.status_code == 400
    body = response.json()
    errors = body["errors"]
    assert "email" in errors or "detail" in errors


@pytest.mark.django_db
def test_citizen_register_invalid_phone(api_client, security_headers):
    payload = _citizen_payload("badphone@example.com")
    payload["phone"] = "abc123"

    response = api_client.post(reverse("citizen-register"), payload, format="json", **security_headers)

    assert response.status_code == 400
    body = response.json()
    assert "phone" in body["errors"]


@pytest.mark.django_db
def test_citizen_login_success(api_client, security_headers, create_citizen_user):
    payload = create_citizen_user(email="login_success@example.com")

    response = api_client.post(
        reverse("citizen-token"),
        {"email": payload["email"], "password": payload["password"]},
        format="json",
        **security_headers,
    )

    assert response.status_code == 200
    body = response.json()["data"]
    assert "access" in body
    assert "refresh" in body


@pytest.mark.django_db
def test_citizen_login_invalid_credentials(api_client, security_headers, create_citizen_user):
    payload = create_citizen_user(email="login_invalid@example.com")

    response = api_client.post(
        reverse("citizen-token"),
        {"email": payload["email"], "password": "wrongpass"},
        format="json",
        **security_headers,
    )

    assert response.status_code == 400
    assert "detail" in response.json()["errors"]


@pytest.mark.django_db
def test_citizen_login_missing_headers(api_client, create_citizen_user):
    payload = create_citizen_user(email="login_no_header@example.com")

    response = api_client.post(
        reverse("citizen-token"),
        {"email": payload["email"], "password": payload["password"]},
        format="json",
    )

    assert response.status_code == 400
    assert "detail" in response.json()["errors"]


@pytest.mark.django_db
def test_citizen_login_invalid_email_format(api_client, security_headers):
    response = api_client.post(
        reverse("citizen-token"),
        {"email": "not-an-email", "password": "whatever123"},
        format="json",
        **security_headers,
    )

    assert response.status_code == 400
    assert "email" in response.json()["errors"]



