from __future__ import annotations

from rest_framework_simplejwt.tokens import AccessToken, RefreshToken


class CitizenRefreshToken(RefreshToken):
    @classmethod
    def for_citizen(cls, citizen):
        token = cls()
        token["sub"] = str(citizen.pk)
        token["email"] = citizen.email
        token["scope"] = "citizen"
        token["type"] = "citizen"
        token.access_token["sub"] = str(citizen.pk)
        token.access_token["email"] = citizen.email
        token.access_token["scope"] = "citizen"
        token.access_token["type"] = "citizen"
        return token


class CitizenAccessToken(AccessToken):
    pass


class EmployeeRefreshToken(RefreshToken):
    @classmethod
    def for_employee(cls, employee):
        token = cls()
        token["sub"] = str(employee.pk)
        token["email"] = employee.email
        token["scope"] = "employee"
        token["type"] = "employee"
        token.access_token["sub"] = str(employee.pk)
        token.access_token["email"] = employee.email
        token.access_token["scope"] = "employee"
        token.access_token["type"] = "employee"
        return token


class EmployeeAccessToken(AccessToken):
    pass
