from __future__ import annotations

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


class ApiResponseMixin:
    """Helper mixin to standardize API responses."""

    default_success_code = "ok"

    def success(
        self,
        *,
        data=None,
        message: str = "OK",
        code: str | None = None,
        status_code: int = status.HTTP_200_OK,
        errors=None,
    ) -> Response:
        payload = {
            "success": True,
            "code": code or self.default_success_code,
            "message": message,
            "data": data,
            "errors": errors,
        }
        return Response(payload, status=status_code)

    def error(
        self,
        *,
        message: str,
        code: str = "error",
        status_code: int = status.HTTP_400_BAD_REQUEST,
        errors=None,
    ) -> Response:
        payload = {
            "success": False,
            "code": code,
            "message": message,
            "data": None,
            "errors": errors,
        }
        return Response(payload, status=status_code)


def custom_exception_handler(exc, context):
    """Ensure Django REST Framework exceptions also respect the standard payload."""

    response = exception_handler(exc, context)
    if response is None:
        return response

    detail = response.data
    message = ""
    if isinstance(detail, dict):
        message = detail.get("detail") or ""
    if not message:
        message = "Ocorreu um erro."

    response.data = {
        "success": False,
        "code": exc.__class__.__name__,
        "message": message,
        "data": None,
        "errors": detail,
    }
    return response
