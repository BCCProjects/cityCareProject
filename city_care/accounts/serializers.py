from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from rest_framework import serializers

from .models import Administrator, Citizen
from core.api.tokens import CitizenRefreshToken


class SecurityHeadersMixin:
    """Valida o trio de cabeçalhos definidos no .env."""

    def validate_headers(self, request) -> None:
        expected_user = settings.API_SECURITY_USER
        expected_app = settings.API_SECURITY_APP
        expected_signature = settings.API_SECURITY_SIGNATURE

        provided_user = request.headers.get("X_USER")
        provided_app = request.headers.get("X_APP")
        provided_signature = request.headers.get("X_SIGNATURE")

        missing = [
            header
            for header, value in {
                "X_USER": provided_user,
                "X_APP": provided_app,
                "X_SIGNATURE": provided_signature,
            }.items()
            if not value
        ]
        if missing:
            raise serializers.ValidationError(
                {"detail": f"Cabeçalhos obrigatórios ausentes: {', '.join(missing)}"}
            )

        if (
            provided_user != expected_user
            or provided_app != expected_app
            or provided_signature != expected_signature
        ):
            raise serializers.ValidationError(
                {"detail": "Cabeçalhos de autorização inválidos."}
            )


class CitizenRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = Citizen
        fields = ("id", "email", "full_name", "phone", "password")
        read_only_fields = ("id",)

    def create(self, validated_data):
        password = validated_data.pop("password")
        citizen = Citizen(**validated_data)
        citizen.set_password(password)
        try:
            citizen.full_clean()
            citizen.save()
        except IntegrityError as exc:
            raise serializers.ValidationError({"detail": "Email já cadastrado."}) from exc
        except ValidationError as exc:
            raise serializers.ValidationError(exc.message_dict) from exc
        return citizen


class CitizenTokenSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    refresh = serializers.CharField(read_only=True)
    access = serializers.CharField(read_only=True)

    def validate(self, attrs):
        email = attrs["email"]
        password = attrs["password"]
        try:
            citizen = Citizen.objects.get(email=email, is_active=True)
        except Citizen.DoesNotExist as exc:  # pragma: no cover - mensagem uniforme
            raise serializers.ValidationError({"detail": "Credenciais inválidas."}) from exc

        if not citizen.check_password(password):
            raise serializers.ValidationError({"detail": "Credenciais inválidas."})

        refresh = CitizenRefreshToken.for_citizen(citizen)
        attrs["refresh"] = str(refresh)
        attrs["access"] = str(refresh.access_token)
        return attrs


class AdministratorRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = Administrator
        fields = ("id", "email", "first_name", "last_name", "password")
        read_only_fields = ("id",)

    def create(self, validated_data):
        password = validated_data.pop("password")
        with transaction.atomic():
            admin = Administrator.objects.create_user(password=password, **validated_data)
        return admin
