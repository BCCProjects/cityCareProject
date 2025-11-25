from __future__ import annotations

import pytest
from django.urls import reverse

from tests.utils import ensure_location


def _admin_payload(email: str, password: str = "AdmSenha123!") -> dict[str, str]:
    _, _, organization = ensure_location("Admin Auth City")
    return {
        "email": email,
        "first_name": "Admin",
        "last_name": "Example",
        "password": password,
        "organization_id": organization.id,
    }


@pytest.mark.django_db
def test_admin_register_success(api_client, security_headers):
    payload = _admin_payload("admin_success@example.com")

    response = api_client.post(reverse("employee-register"), payload, format="json", **security_headers)

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == payload["email"]
    assert data["first_name"] == payload["first_name"]
    assert "id" in data


@pytest.mark.django_db
def test_admin_register_invalid_email(api_client, security_headers):
    payload = _admin_payload("invalid-email")

    response = api_client.post(reverse("employee-register"), payload, format="json", **security_headers)

    assert response.status_code == 400
    assert "email" in response.json()


@pytest.mark.django_db
def test_admin_register_short_password(api_client, security_headers):
    payload = _admin_payload("admin_short@example.com", password="short")

    response = api_client.post(reverse("employee-register"), payload, format="json", **security_headers)

    assert response.status_code == 400
    assert "password" in response.json()


@pytest.mark.django_db
def test_admin_register_missing_headers(api_client):
    payload = _admin_payload("admin_noheader@example.com")

    response = api_client.post(reverse("employee-register"), payload, format="json")

    assert response.status_code == 400
    body = response.json()
    assert "detail" in body


@pytest.mark.django_db
def test_admin_register_duplicate_email(api_client, security_headers):
    payload = _admin_payload("admin_duplicate@example.com")
    first = api_client.post(reverse("employee-register"), payload, format="json", **security_headers)
    assert first.status_code == 201

    response = api_client.post(reverse("employee-register"), payload, format="json", **security_headers)

    assert response.status_code == 400
    data = response.json()
    assert "detail" in data or "email" in data


@pytest.mark.django_db
def test_admin_login_success(api_client, security_headers, create_admin_user):
    payload = create_admin_user(email="admin_login_ok@example.com")

    response = api_client.post(
        reverse("employee-token"),
        {"email": payload["email"], "password": payload["password"]},
        format="json",
        **security_headers,
    )

    assert response.status_code == 200
    body = response.json()
    assert "access" in body and "refresh" in body


@pytest.mark.django_db
def test_admin_login_invalid_credentials(api_client, security_headers, create_admin_user):
    payload = create_admin_user(email="admin_login_invalid@example.com")

    response = api_client.post(
        reverse("employee-token"),
        {"email": payload["email"], "password": "wrongpass"},
        format="json",
        **security_headers,
    )

    assert response.status_code == 400
    body = response.json()
    assert "detail" in body


@pytest.mark.django_db
def test_admin_login_missing_headers(api_client, create_admin_user):
    payload = create_admin_user(email="admin_login_no_header@example.com")

    response = api_client.post(
        reverse("employee-token"),
        {"email": payload["email"], "password": payload["password"]},
        format="json",
    )

    assert response.status_code == 400
    body = response.json()
    assert "detail" in body


@pytest.mark.django_db
def test_admin_login_invalid_email_format(api_client, security_headers):
    response = api_client.post(
        reverse("employee-token"),
        {"email": "not-an-email", "password": "whatever123"},
        format="json",
        **security_headers,
    )

    assert response.status_code == 400
    body = response.json()
    assert "email" in body



