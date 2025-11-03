from __future__ import annotations

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from .models import City, Citizen, Employee, Organization, State
from core.api.tokens import CitizenRefreshToken, EmployeeRefreshToken


class SecurityHeadersMixin:
    """Valida o trio de cabecalhos definidos no .env."""

    def _get_header(self, request, name: str) -> str | None:
        value = request.headers.get(name)
        if value:
            return value
        meta_key = "HTTP_" + name.upper().replace("-", "_")
        return request.META.get(meta_key)

    def validate_headers(self, request) -> None:
        expected_user = settings.API_SECURITY_USER
        expected_app = settings.API_SECURITY_APP
        expected_signature = settings.API_SECURITY_SIGNATURE

        provided_user = self._get_header(request, "X-USER")
        provided_app = self._get_header(request, "X-APP")
        provided_signature = self._get_header(request, "X-SIGNATURE")

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
            raise serializers.ValidationError({"detail": f"Cabecalhos obrigatorios ausentes: {', '.join(missing)}"})

        if (
            provided_user != expected_user
            or provided_app != expected_app
            or provided_signature != expected_signature
        ):
            raise serializers.ValidationError({"detail": "Cabecalhos de autorizacao invalidos."})


class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = State
        fields = ["id", "name", "abbreviation"]
        read_only_fields = ["id"]


class CitySerializer(serializers.ModelSerializer):
    state = StateSerializer(read_only=True)
    state_id = serializers.PrimaryKeyRelatedField(
        source="state",
        queryset=State.objects.all(),
        write_only=True,
        required=True,
    )

    class Meta:
        model = City
        fields = ["id", "name", "state", "state_id"]
        read_only_fields = ["id", "state"]


class OrganizationSerializer(serializers.ModelSerializer):
    city = CitySerializer(read_only=True)
    city_id = serializers.PrimaryKeyRelatedField(
        source="city",
        queryset=City.objects.select_related("state"),
        write_only=True,
        required=True,
    )
    state = StateSerializer(source="city.state", read_only=True)

    class Meta:
        model = Organization
        fields = ["id", "name", "city", "city_id", "state", "created_at", "updated_at"]
        read_only_fields = ["id", "city", "state", "created_at", "updated_at"]


class CitizenRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    email = serializers.CharField(
        validators=[
            UniqueValidator(queryset=Citizen.objects.all(), message="Email ja cadastrado."),
        ]
    )
    city = CitySerializer(read_only=True)
    city_id = serializers.PrimaryKeyRelatedField(
        source="city",
        queryset=City.objects.select_related("state"),
        write_only=True,
    )

    class Meta:
        model = Citizen
        fields = ("id", "email", "first_name", "last_name", "phone", "password", "city", "city_id")
        read_only_fields = ("id", "city")

    def validate_email(self, value: str) -> str:
        import re

        value = (value or "").strip()
        pattern = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
        if not pattern.match(value):
            raise serializers.ValidationError("Insira um endereco de email valido.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        citizen = Citizen(**validated_data)
        citizen.set_password(password)
        try:
            citizen.full_clean(exclude=["email"])
            citizen.save()
        except IntegrityError as exc:
            raise serializers.ValidationError({"detail": "Email ja cadastrado."}) from exc
        except ValidationError as exc:
            raise serializers.ValidationError(exc.message_dict) from exc
        return citizen


class CitizenTokenSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField(write_only=True, min_length=8)
    refresh = serializers.CharField(read_only=True)
    access = serializers.CharField(read_only=True)

    def validate(self, attrs):
        import re

        email = (attrs.get("email") or "").strip()
        pattern = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
        if not pattern.match(email):
            raise serializers.ValidationError({"email": "Insira um endereco de email valido."})
        password = attrs["password"]
        try:
            citizen = Citizen.objects.get(email=email, is_active=True)
        except Citizen.DoesNotExist as exc:
            raise serializers.ValidationError({"detail": "Credenciais invalidas."}) from exc

        if not citizen.check_password(password):
            raise serializers.ValidationError({"detail": "Credenciais invalidas."})

        refresh = CitizenRefreshToken.for_citizen(citizen)
        attrs["refresh"] = str(refresh)
        attrs["access"] = str(refresh.access_token)
        return attrs


class EmployeeRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    organization_id = serializers.PrimaryKeyRelatedField(
        source="organization",
        queryset=Organization.objects.select_related("city__state"),
        write_only=True,
    )
    organization = OrganizationSerializer(read_only=True)
    groups = serializers.SlugRelatedField(many=True, slug_field="name", read_only=True)
    group_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Group.objects.all(),
        write_only=True,
        source="groups",
    )

    class Meta:
        model = Employee
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "password",
            "organization",
            "organization_id",
            "groups",
            "group_ids",
        )
        read_only_fields = ("id", "organization")

    def create(self, validated_data):
        groups = validated_data.pop("groups", [])
        password = validated_data.pop("password")
        with transaction.atomic():
            employee = Employee.objects.create_superuser(password=password, **validated_data)
            if not groups:
                raise serializers.ValidationError({"group_ids": "Informe ao menos um grupo."})
            employee.groups.set(groups)
            employee.refresh_from_db()
        return employee


class EmployeeTokenSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField(write_only=True, min_length=8)
    refresh = serializers.CharField(read_only=True)
    access = serializers.CharField(read_only=True)

    def validate(self, attrs):
        import re

        email = (attrs.get("email") or "").strip()
        pattern = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
        if not pattern.match(email):
            raise serializers.ValidationError({"email": "Insira um endereco de email valido."})
        password = attrs["password"]
        try:
            employee = Employee.objects.get(email=email, is_active=True, is_staff=True)
        except Employee.DoesNotExist as exc:
            raise serializers.ValidationError({"detail": "Credenciais invalidas."}) from exc

        if not employee.check_password(password):
            raise serializers.ValidationError({"detail": "Credenciais invalidas."})

        refresh = EmployeeRefreshToken.for_employee(employee)
        attrs["refresh"] = str(refresh)
        attrs["access"] = str(refresh.access_token)
        return attrs
