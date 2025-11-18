from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from .serializers import (
    AdministratorRegistrationSerializer,
    AdministratorTokenSerializer,
    CitizenRegistrationSerializer,
    CitizenTokenSerializer,
    EmployeeRegistrationSerializer,
    EmployeeTokenSerializer,
    SecurityHeadersMixin,
)
from core.api.authentication import CitizenJWTAuthentication
from core.api.responses import ApiResponseMixin


class CitizenRegistrationView(SecurityHeadersMixin, ApiResponseMixin, APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        self.validate_headers(request)
        serializer = CitizenRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        citizen = serializer.save()
        return self.success(
            data=CitizenRegistrationSerializer(citizen).data,
            code="citizens.register",
            status_code=status.HTTP_201_CREATED,
        )


class CitizenTokenObtainView(SecurityHeadersMixin, ApiResponseMixin, APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        self.validate_headers(request)
        serializer = CitizenTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self.success(
            data={"refresh": serializer.validated_data["refresh"], "access": serializer.validated_data["access"]},
            code="citizens.token",
        )


class EmployeeRegistrationView(SecurityHeadersMixin, ApiResponseMixin, APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        self.validate_headers(request)
        serializer = EmployeeRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        employee = serializer.save()
        return self.success(
            data=EmployeeRegistrationSerializer(employee).data,
            code="employees.register",
            status_code=status.HTTP_201_CREATED,
        )


class EmployeeTokenObtainView(SecurityHeadersMixin, ApiResponseMixin, APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        self.validate_headers(request)
        serializer = EmployeeTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self.success(
            data={"refresh": serializer.validated_data["refresh"], "access": serializer.validated_data["access"]},
            code="employees.token",
        )


class AdministratorRegistrationView(SecurityHeadersMixin, ApiResponseMixin, APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        self.validate_headers(request)
        serializer = AdministratorRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        admin = serializer.save()
        return self.success(
            data=AdministratorRegistrationSerializer(admin).data,
            code="admins.register",
            status_code=status.HTTP_201_CREATED,
        )


class AdministratorTokenObtainView(SecurityHeadersMixin, ApiResponseMixin, APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        self.validate_headers(request)
        serializer = AdministratorTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self.success(
            data={"refresh": serializer.validated_data["refresh"], "access": serializer.validated_data["access"]},
            code="admins.token",
        )


class CitizenProfileView(SecurityHeadersMixin, ApiResponseMixin, APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = (CitizenJWTAuthentication,)

    def get(self, request, *args, **kwargs):
        self.validate_headers(request)
        serializer = CitizenRegistrationSerializer(request.user)
        return self.success(data=serializer.data, code="citizens.profile")
