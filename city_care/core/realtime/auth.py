from __future__ import annotations

from typing import Any
from urllib.parse import parse_qs

from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken

from accounts.models import Citizen, Employee


class JWTAuthMiddleware:
    """
    Middleware that authenticates websocket connections using the same JWTs employed by the API.
    Falls back to the default AuthMiddlewareStack session handling for Django Admin users.
    """

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope: dict[str, Any], receive, send):
        user = scope.get("user")
        if getattr(user, "is_authenticated", False):
            return await self.inner(scope, receive, send)
        scope["user"] = await self._get_user_from_scope(scope)
        return await self.inner(scope, receive, send)

    @database_sync_to_async
    def _get_user_from_scope(self, scope: dict[str, Any]):
        token = self._extract_token(scope)
        if not token:
            return AnonymousUser()
        try:
            access = AccessToken(token)
        except TokenError:
            return AnonymousUser()

        scope_value = access.get("scope")
        user_id = access.get("sub")
        if not user_id:
            return AnonymousUser()

        if scope_value == "citizen":
            return Citizen.objects.filter(pk=user_id, is_active=True).first() or AnonymousUser()
        if scope_value == "employee":
            return Employee.objects.filter(pk=user_id, is_active=True).first() or AnonymousUser()
        return AnonymousUser()

    @staticmethod
    def _extract_token(scope: dict[str, Any]) -> str | None:
        query_string = scope.get("query_string", b"")
        if query_string:
            query_params = parse_qs(query_string.decode())
            token_param = query_params.get("token")
            if token_param:
                return token_param[0]

        headers = dict(scope.get("headers") or [])
        raw_header = headers.get(b"authorization")
        if not raw_header:
            return None
        try:
            header_value = raw_header.decode()
        except UnicodeDecodeError:
            return None
        parts = header_value.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            return parts[1]
        return None


def JWTAuthMiddlewareStack(inner):
    return JWTAuthMiddleware(AuthMiddlewareStack(inner))

