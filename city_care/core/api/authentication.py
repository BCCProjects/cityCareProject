from __future__ import annotations

from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken

from accounts.models import Administrator, Citizen


class CitizenJWTAuthentication(BaseAuthentication):
    keyword = b"bearer"

    def authenticate(self, request):
        header = get_authorization_header(request)
        if not header:
            return None
        parts = header.split()
        if parts[0].lower() != self.keyword:
            return None
        if len(parts) != 2:
            raise exceptions.AuthenticationFailed("Cabeçalho de autorização inválido.")
        raw_token = parts[1].decode()
        try:
            token = AccessToken(raw_token)
        except TokenError as exc:  # pragma: no cover - mensagem uniforme
            raise exceptions.AuthenticationFailed(f"Token inválido: {exc}") from exc

        if token.get("scope") != "citizen":
            raise exceptions.AuthenticationFailed("Escopo do token inválido.")

        citizen_id = token.get("sub")
        if not citizen_id:
            raise exceptions.AuthenticationFailed("Token sem identificação de usuário.")

        try:
            citizen = Citizen.objects.get(pk=citizen_id, is_active=True)
        except Citizen.DoesNotExist as exc:
            raise exceptions.AuthenticationFailed("Cidadão não encontrado.") from exc

        return (citizen, None)


class AdminJWTAuthentication(BaseAuthentication):
    keyword = b"bearer"

    def authenticate(self, request):
        header = get_authorization_header(request)
        if not header:
            return None
        parts = header.split()
        if parts[0].lower() != self.keyword:
            return None
        if len(parts) != 2:
            raise exceptions.AuthenticationFailed("Cabeçalho de autorização inválido.")
        raw_token = parts[1].decode()
        try:
            token = AccessToken(raw_token)
        except TokenError as exc:  # pragma: no cover - mensagem uniforme
            raise exceptions.AuthenticationFailed(f"Token inválido: {exc}") from exc

        if token.get("scope") != "admin":
            return None  # não é um token de admin; permite outras autenticações

        admin_id = token.get("sub")
        if not admin_id:
            raise exceptions.AuthenticationFailed("Token sem identificação de usuário.")

        try:
            admin = Administrator.objects.get(pk=admin_id, is_active=True, is_staff=True)
        except Administrator.DoesNotExist as exc:
            raise exceptions.AuthenticationFailed("Administrador não encontrado.") from exc

        return (admin, None)
