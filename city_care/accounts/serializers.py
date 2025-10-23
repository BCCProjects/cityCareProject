from __future__ import annotations

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from .models import Administrator, Citizen
from core.api.tokens import AdminRefreshToken, CitizenRefreshToken


class SecurityHeadersMixin:
    """Valida o trio de cabeçalhos definidos no .env.

    Observação: o Django/DRF normaliza nomes de cabeçalho para o formato com hífens
    (ex.: "X-USER"). Para evitar falsos negativos, aceitamos tanto "X-USER" quanto
    a variante com underscore ("X_USER").
    """

    def _get_header(self, request, name: str) -> str | None:
        """Obtém um cabeçalho de forma robusta.

        - Tenta o nome com hífen via `request.headers` (case-insensitive).
        - Faz fallback para a variante com underscore via `request.META`.
        """
        # Preferido: formato com hífen em `request.headers`
        value = request.headers.get(name)
        if value:
            return value
        # Fallback: tentar variante com underscore em META
        meta_key = "HTTP_" + name.upper().replace("-", "_")
        return request.META.get(meta_key)

    def validate_headers(self, request) -> None:
        expected_user = settings.API_SECURITY_USER
        expected_app = settings.API_SECURITY_APP
        expected_signature = settings.API_SECURITY_SIGNATURE

        # Leia nos formatos com hífen (preferido); aceita underscore como fallback
        provided_user = self._get_header(request, "X-USER")
        provided_app = self._get_header(request, "X-APP")
        provided_signature = self._get_header(request, "X-SIGNATURE")

        # Mantemos a nomenclatura com underscore na mensagem para
        # consistência com a documentação existente (README/Postman).
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
    # Aceita emails com Unicode e mantém unicidade
    email = serializers.CharField(
        validators=[
            UniqueValidator(queryset=Citizen.objects.all(), message="Email já cadastrado."),
        ]
    )

    class Meta:
        model = Citizen
        fields = ("id", "email", "full_name", "phone", "password")
        read_only_fields = ("id",)

    def validate_email(self, value: str) -> str:
        import re

        value = (value or "").strip()
        # Validação mínima e permissiva (Unicode): <algo>@<algo>.<algo>
        pattern = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
        if not pattern.match(value):
            raise serializers.ValidationError("Insira um endereço de email válido.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        citizen = Citizen(**validated_data)
        citizen.set_password(password)
        try:
            # Evita reprovar emails com Unicode pelo EmailField do Model; os
            # demais campos continuam validados.
            citizen.full_clean(exclude=["email"])
            citizen.save()
        except IntegrityError as exc:
            raise serializers.ValidationError({"detail": "Email já cadastrado."}) from exc
        except ValidationError as exc:
            raise serializers.ValidationError(exc.message_dict) from exc
        return citizen


class CitizenTokenSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField(write_only=True, min_length=8)
    refresh = serializers.CharField(read_only=True)
    access = serializers.CharField(read_only=True)

    def validate(self, attrs):
        # Normaliza e valida email com verificação mínima (Unicode permitido)
        import re

        email = (attrs.get("email") or "").strip()
        pattern = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
        if not pattern.match(email):
            raise serializers.ValidationError({"email": "Insira um endereço de email válido."})
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
            # Cria como superuser para acesso completo ao Django Admin
            admin = Administrator.objects.create_superuser(password=password, **validated_data)
        return admin


class AdministratorTokenSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField(write_only=True, min_length=8)
    refresh = serializers.CharField(read_only=True)
    access = serializers.CharField(read_only=True)

    def validate(self, attrs):
        import re

        email = (attrs.get("email") or "").strip()
        pattern = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
        if not pattern.match(email):
            raise serializers.ValidationError({"email": "Insira um endereço de email válido."})
        password = attrs["password"]
        try:
            admin = Administrator.objects.get(email=email, is_active=True, is_staff=True)
        except Administrator.DoesNotExist as exc:  # pragma: no cover - mensagem uniforme
            raise serializers.ValidationError({"detail": "Credenciais inválidas."}) from exc

        if not admin.check_password(password):
            raise serializers.ValidationError({"detail": "Credenciais inválidas."})

        refresh = AdminRefreshToken.for_admin(admin)
        attrs["refresh"] = str(refresh)
        attrs["access"] = str(refresh.access_token)
        return attrs
