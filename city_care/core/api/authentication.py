from __future__ import annotations

from rest_framework import exceptions
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import AccessToken

from accounts.models import Citizen, Employee


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
            raise exceptions.AuthenticationFailed("Cabecalho de autorizacao invalido.")
        raw_token = parts[1].decode()
        try:
            token = AccessToken(raw_token)
        except TokenError as exc:  # pragma: no cover - mensagem uniforme
            raise exceptions.AuthenticationFailed(f"Token invalido: {exc}") from exc

        if token.get("scope") != "citizen":
            raise exceptions.AuthenticationFailed("Escopo do token invalido.")

        citizen_id = token.get("sub")
        if not citizen_id:
            raise exceptions.AuthenticationFailed("Token sem identificacao de usuario.")

        try:
            citizen = Citizen.objects.get(pk=citizen_id, is_active=True)
        except Citizen.DoesNotExist as exc:
            raise exceptions.AuthenticationFailed("Cidadao nao encontrado.") from exc

        return (citizen, None)


class EmployeeJWTAuthentication(BaseAuthentication):
    keyword = b"bearer"

    def authenticate(self, request):
        header = get_authorization_header(request)
        if not header:
            return None
        parts = header.split()
        if parts[0].lower() != self.keyword:
            return None
        if len(parts) != 2:
            raise exceptions.AuthenticationFailed("Cabecalho de autorizacao invalido.")
        raw_token = parts[1].decode()
        try:
            token = AccessToken(raw_token)
        except TokenError as exc:  # pragma: no cover - mensagem uniforme
            raise exceptions.AuthenticationFailed(f"Token invalido: {exc}") from exc

        if token.get("scope") != "employee":
            return None

        employee_id = token.get("sub")
        if not employee_id:
            raise exceptions.AuthenticationFailed("Token sem identificacao de usuario.")

        try:
            employee = Employee.objects.get(pk=employee_id, is_active=True, is_staff=True)
        except Employee.DoesNotExist as exc:
            raise exceptions.AuthenticationFailed("Employee nao encontrado.") from exc

        return (employee, None)
