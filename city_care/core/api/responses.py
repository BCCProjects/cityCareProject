from __future__ import annotations

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


class ApiResponseMixin:
    default_success_code = "ok"
    response_namespace = ""

    def success(self, *, data=None, code: str | None = None, message: str = "", status_code: int = status.HTTP_200_OK):
        payload = {
            "success": True,
            "code": code or self.default_success_code,
            "message": message,
            "data": data,
            "errors": None,
        }
        return Response(payload, status=status_code)

    def error(self, *, errors=None, code: str | None = None, message: str = "", status_code: int = status.HTTP_400_BAD_REQUEST):
        return Response(
            {
                "success": False,
                "code": code or self.default_success_code,
                "message": message,
                "data": None,
                "errors": errors,
            },
            status=status_code,
        )

    def build_code(self, action: str) -> str:
        namespace = getattr(self, "response_namespace", "") or ""
        if namespace:
            return f"{namespace}.{action}"
        return action

    def wrap_drf_response(self, response: Response, action: str) -> Response:
        data = getattr(response, "data", None)
        if isinstance(data, dict) and {"success", "code", "data", "errors"}.issubset(data.keys()):
            return Response(data, status=response.status_code)
        return self.success(data=data, code=self.build_code(action), status_code=response.status_code)


def custom_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is None:
        return None
    data = response.data
    if not isinstance(data, dict):
        errors = {"detail": data}
    else:
        errors = data
    response.data = {
        "success": False,
        "code": getattr(exc, "__class__", type(exc)).__name__,
        "message": "",
        "data": None,
        "errors": errors,
    }
    return response
