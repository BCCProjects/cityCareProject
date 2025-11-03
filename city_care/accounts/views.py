from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    CitizenRegistrationSerializer,
    CitizenTokenSerializer,
    EmployeeRegistrationSerializer,
    EmployeeTokenSerializer,
    SecurityHeadersMixin,
)


class CitizenRegistrationView(SecurityHeadersMixin, APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        self.validate_headers(request)
        serializer = CitizenRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        citizen = serializer.save()
        return Response(CitizenRegistrationSerializer(citizen).data, status=status.HTTP_201_CREATED)


class CitizenTokenObtainView(SecurityHeadersMixin, APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        self.validate_headers(request)
        serializer = CitizenTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({"refresh": serializer.validated_data["refresh"], "access": serializer.validated_data["access"]})


class EmployeeRegistrationView(SecurityHeadersMixin, APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        self.validate_headers(request)
        serializer = EmployeeRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        employee = serializer.save()
        return Response(
            EmployeeRegistrationSerializer(employee).data,
            status=status.HTTP_201_CREATED,
        )


class EmployeeTokenObtainView(SecurityHeadersMixin, APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        self.validate_headers(request)
        serializer = EmployeeTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({"refresh": serializer.validated_data["refresh"], "access": serializer.validated_data["access"]})
