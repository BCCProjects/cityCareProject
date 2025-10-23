from __future__ import annotations

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    AdministratorRegistrationSerializer,
    AdministratorTokenSerializer,
    CitizenRegistrationSerializer,
    CitizenTokenSerializer,
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


class AdministratorRegistrationView(SecurityHeadersMixin, APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        self.validate_headers(request)
        serializer = AdministratorRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        admin = serializer.save()
        return Response(
            AdministratorRegistrationSerializer(admin).data,
            status=status.HTTP_201_CREATED,
        )


class AdministratorTokenObtainView(SecurityHeadersMixin, APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        self.validate_headers(request)
        serializer = AdministratorTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({"refresh": serializer.validated_data["refresh"], "access": serializer.validated_data["access"]})
