from __future__ import annotations

from uuid import uuid4

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from accounts.models import Citizen
from core.reports.models import Attachment
from core.services.report_service import ReportService
from tests.utils import ensure_location


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture(autouse=True)
def _ensure_citizen_staff_attribute():
    if not hasattr(Citizen, "is_staff"):
        Citizen.is_staff = False
    yield


@pytest.fixture(autouse=True)
def _fix_report_service_create(monkeypatch):
    original = ReportService.create_report

    def wrapper(cls, citizen, **kwargs):
        return original(citizen=citizen, **kwargs)

    monkeypatch.setattr(ReportService, "create_report", classmethod(wrapper))


@pytest.fixture
def security_headers(settings):
    settings.API_SECURITY_USER = "test"
    settings.API_SECURITY_APP = "test"
    settings.API_SECURITY_SIGNATURE = "test"
    return {
        "HTTP_X_USER": "test",
        "HTTP_X_APP": "test",
        "HTTP_X_SIGNATURE": "test",
    }


@pytest.fixture
def create_citizen_user(api_client, security_headers):
    def _create(**overrides):
        password = overrides.pop("password", "Senha123!")
        city_id = overrides.pop("city_id", None)
        if city_id is None:
            _, city, _ = ensure_location("Citizen API City")
            city_id = city.id
        payload = {
            "email": overrides.pop("email", f"citizen_{uuid4().hex}@example.com"),
            "first_name": overrides.pop("first_name", "Citizen"),
            "last_name": overrides.pop("last_name", "Tester"),
            "phone": overrides.pop("phone", "11999999999"),
            "password": password,
            "city_id": city_id,
        }
        payload.update(overrides)
        response = api_client.post(reverse("citizen-register"), payload, format="json", **security_headers)
        assert response.status_code == 201, response.content
        return payload

    return _create


@pytest.fixture
def citizen_tokens(api_client, security_headers, create_citizen_user):
    def _create(**overrides):
        payload = create_citizen_user(**overrides)
        login_response = api_client.post(
            reverse("citizen-token"),
            {"email": payload["email"], "password": payload["password"]},
            format="json",
            **security_headers,
        )
        assert login_response.status_code == 200, login_response.content
        tokens = login_response.json()["data"]
        return {
            "access": tokens["access"],
            "refresh": tokens["refresh"],
            "email": payload["email"],
            "password": payload["password"],
        }

    return _create


@pytest.fixture
def create_admin_user(api_client, security_headers):
    def _create(**overrides):
        password = overrides.pop("password", "AdmSenha123!")
        ensure_location("Admin API City")
        payload = {
            "email": overrides.pop("email", f"admin_{uuid4().hex}@example.com"),
            "first_name": overrides.pop("first_name", "Admin"),
            "last_name": overrides.pop("last_name", "Tester"),
            "password": password,
        }
        payload.update(overrides)
        response = api_client.post(reverse("admin-register"), payload, format="json", **security_headers)
        assert response.status_code == 201, response.content
        return payload

    return _create


@pytest.fixture
def admin_tokens(api_client, security_headers, create_admin_user):
    def _create(**overrides):
        payload = create_admin_user(**overrides)
        login_response = api_client.post(
            reverse("admin-token"),
            {"email": payload["email"], "password": payload["password"]},
            format="json",
            **security_headers,
        )
        assert login_response.status_code == 200, login_response.content
        tokens = login_response.json()["data"]
        return {
            "access": tokens["access"],
            "refresh": tokens["refresh"],
            "email": payload["email"],
            "password": payload["password"],
        }

    return _create


@pytest.fixture
def auth_header():
    def _build(token: str) -> dict[str, str]:
        return {"HTTP_AUTHORIZATION": f"Bearer {token}"}

    return _build
