from __future__ import annotations

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.test import APIClient
from rest_framework.views import exception_handler as drf_exception_handler

from accounts.models import Employee
from tests.utils import ensure_location

Administrator = Employee


class ApiResponseMixin:
    def success(self, data=None, message: str | None = None, code: str | None = None, status_code: int = status.HTTP_200_OK):
        return Response(
            {
                "success": True,
                "code": code,
                "message": message,
                "data": data,
                "errors": None,
            },
            status=status_code,
        )

    def error(self, *, message: str, code: str | None = None, status_code: int = status.HTTP_400_BAD_REQUEST, errors=None):
        return Response(
            {
                "success": False,
                "code": code,
                "message": message,
                "data": None,
                "errors": errors,
            },
            status=status_code,
        )


def custom_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is None:
        return response
    response.data = {
        "success": False,
        "code": exc.__class__.__name__,
        "message": None,
        "data": None,
        "errors": response.data,
    }
    return response


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
    _, _, organization = ensure_location("Dashboard City")
    admin = Administrator.objects.create_superuser(
        email="admin@example.com",
        password="Senha123!",
        first_name="Admin",
        organization=organization,
    )
    client = APIClient()
    client.force_authenticate(user=admin)

    response = client.get(reverse("dashboard-list"))

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert "open_by_neighborhood" in body
    assert "weekly_series" in body
