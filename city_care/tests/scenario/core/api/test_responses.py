from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIClient

from accounts.models import Administrator
from core.api.responses import ApiResponseMixin, custom_exception_handler


class DummyView(ApiResponseMixin):
    pass


def test_success_payload_structure():
    view = DummyView()
    response = view.success(data={"foo": "bar"}, message="Tudo certo", code="dummy.ok")
    assert response.status_code == status.HTTP_200_OK
    assert response.data == {
        "success": True,
        "code": "dummy.ok",
        "message": "Tudo certo",
        "data": {"foo": "bar"},
        "errors": None,
    }


def test_error_payload_structure():
    view = DummyView()
    response = view.error(message="Algo deu errado", code="dummy.error", status_code=status.HTTP_418_IM_A_TEAPOT)
    assert response.status_code == status.HTTP_418_IM_A_TEAPOT
    assert response.data["success"] is False
    assert response.data["message"] == "Algo deu errado"
    assert response.data["data"] is None


def test_custom_exception_handler_wraps_validation_error(rf):
    exc = ValidationError({"field": ["Inválido"]})
    response = custom_exception_handler(exc, {"request": rf.get("/fake"), "view": object()})
    assert response.data["success"] is False
    assert response.data["errors"] == {"field": ["Inválido"]}
    assert response.data["code"] == "ValidationError"


@pytest.mark.django_db
def test_dashboard_view_returns_standard_response():
    admin = Administrator.objects.create_superuser(
        email="admin@example.com",
        password="Senha123!",
        first_name="Admin",
    )
    client = APIClient()
    client.force_authenticate(user=admin)

    response = client.get(reverse("dashboard-list"))

    assert response.status_code == status.HTTP_200_OK
    assert response.data["success"] is True
    assert "results" in response.data["data"]
