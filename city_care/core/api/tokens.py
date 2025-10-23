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


class AdminRefreshToken(RefreshToken):
    @classmethod
    def for_admin(cls, admin):
        token = cls()
        token["sub"] = str(admin.pk)
        token["email"] = admin.email
        token["scope"] = "admin"
        token["type"] = "admin"
        token.access_token["sub"] = str(admin.pk)
        token.access_token["email"] = admin.email
        token.access_token["scope"] = "admin"
        token.access_token["type"] = "admin"
        return token


class AdminAccessToken(AccessToken):
    pass
