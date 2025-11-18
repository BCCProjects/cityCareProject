from __future__ import annotations

from django.conf import settings
from rest_framework.permissions import BasePermission


class InternalAPIPermission(BasePermission):
    """Permissão que aceita apenas chamadas internas com cabeçalhos X-USER/X-APP/X-SIGNATURE.

    - Lê preferencialmente via request.headers (case-insensitive, com hifens)
    - Faz fallback para request.META com underscores
    """

    header_user = "X-USER"
    header_app = "X-APP"
    header_signature = "X-SIGNATURE"

    @staticmethod
    def _get_header(request, name: str) -> str | None:
        value = request.headers.get(name)
        if value:
            return value
        meta_key = "HTTP_" + name.upper().replace("-", "_")
        return request.META.get(meta_key)

    def has_permission(self, request, view) -> bool:  # type: ignore[override]
        # Staff/administrator JWTs can call internal endpoints
        user = getattr(request, "user", None)
        if getattr(user, "is_authenticated", False) and getattr(user, "is_staff", False):
            return True

        expected_user = getattr(settings, "API_SECURITY_USER", None)
        expected_app = getattr(settings, "API_SECURITY_APP", None)
        expected_signature = getattr(settings, "API_SECURITY_SIGNATURE", None)

        provided_user = self._get_header(request, self.header_user)
        provided_app = self._get_header(request, self.header_app)
        provided_signature = self._get_header(request, self.header_signature)

        if not all([expected_user, expected_app, expected_signature]):
            return False
        if not all([provided_user, provided_app, provided_signature]):
            return False
        return (
            provided_user == expected_user
            and provided_app == expected_app
            and provided_signature == expected_signature
        )

