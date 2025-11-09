from __future__ import annotations

from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from accounts.models import Citizen, City, Employee, Organization, State
from accounts.serializers import CitySerializer, OrganizationSerializer, StateSerializer
from core.api.serializers import (
    CategorySerializer,
    CategoryCreateSerializer,
    DepartmentSerializer,
    ReportCreateSerializer,
    ReportDetailSerializer,
    ReportListSerializer,
    TagSerializer,
)
from core.repositories import report_repository
from core.reports.models import Category, Department, Report, ReportStatus, Tag
from core.api.authentication import CitizenJWTAuthentication, EmployeeJWTAuthentication
from core.api.permissions import InternalAPIPermission


class StateViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = State.objects.all()
    serializer_class = StateSerializer
    permission_classes = [AllowAny]
    authentication_classes = (EmployeeJWTAuthentication, CitizenJWTAuthentication, SessionAuthentication)
    pagination_class = None

    def get_permissions(self):
        if self.action in {"list", "retrieve"}:
            return [AllowAny()]
        return [InternalAPIPermission()]


class CityViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = City.objects.select_related("state").all()
    serializer_class = CitySerializer
    permission_classes = [AllowAny]
    authentication_classes = (EmployeeJWTAuthentication, CitizenJWTAuthentication, SessionAuthentication)
    pagination_class = None

    def get_permissions(self):
        if self.action in {"list", "retrieve"}:
            return [AllowAny()]
        return [InternalAPIPermission()]

    def get_queryset(self):
        qs = super().get_queryset()
        state = self.request.query_params.get("state")
        if state:
            qs = qs.filter(state_id=state)
        return qs


class OrganizationViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Organization.objects.select_related("city", "city__state").all()
    serializer_class = OrganizationSerializer
    permission_classes = [InternalAPIPermission]
    authentication_classes: tuple = ()
    pagination_class = None

    def get_queryset(self):
        qs = super().get_queryset()
        city = self.request.query_params.get("city")
        state = self.request.query_params.get("state")
        if city:
            qs = qs.filter(city_id=city)
        if state:
            qs = qs.filter(city__state_id=state)
        return qs


class CategoryViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Category.objects.select_related("department").all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = (EmployeeJWTAuthentication, CitizenJWTAuthentication, SessionAuthentication)
    pagination_class = None

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action in {"create", "update", "partial_update"}:
            return CategoryCreateSerializer
        return CategorySerializer

    def list(self, request, *args, **kwargs):
        department = request.query_params.get("department")
        qs = self.get_queryset()
        if department:
            qs = qs.filter(department_id=department)
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(qs, many=True)
        return Response(serializer.data)
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        category = serializer.save()
        output = CategorySerializer(category, context=self.get_serializer_context())
        headers = self.get_success_headers(output.data)
        return Response(output.data, status=status.HTTP_201_CREATED, headers=headers)


class TagViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = (EmployeeJWTAuthentication, CitizenJWTAuthentication, SessionAuthentication)
    pagination_class = None

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tag = serializer.save()
        output = TagSerializer(tag, context=self.get_serializer_context())
        headers = self.get_success_headers(output.data)
        return Response(output.data, status=status.HTTP_201_CREATED, headers=headers)


class DepartmentViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = (EmployeeJWTAuthentication, CitizenJWTAuthentication, SessionAuthentication)
    pagination_class = None

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        department = serializer.save()
        output = DepartmentSerializer(department, context=self.get_serializer_context())
        headers = self.get_success_headers(output.data)
        return Response(output.data, status=status.HTTP_201_CREATED, headers=headers)


class ReportViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["created_at", "priority"]
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user
        base_qs = (
            Report.objects.select_related("category", "category__department", "department")
            .prefetch_related("tags", "attachments")
        )

        if isinstance(user, Employee) and getattr(user, "is_staff", False):
            queryset = base_qs
        else:
            queryset = base_qs.filter(citizen=user)

        qp = self.request.query_params
        status_param = qp.get("status")
        category_param = qp.get("category")
        department_param = qp.get("department")
        priority_param = qp.get("priority")
        tag_param = qp.get("tag")

        if status_param in ReportStatus.values:
            queryset = queryset.filter(status=status_param)
        if category_param:
            queryset = queryset.filter(category_id=category_param)
        if department_param:
            queryset = queryset.filter(department_id=department_param)
        if priority_param:
            queryset = queryset.filter(priority=priority_param)
        if tag_param:
            queryset = queryset.filter(tags__id=tag_param)
        return queryset

    def get_serializer_class(self):
        if self.action == "create":
            return ReportCreateSerializer
        if self.action == "retrieve":
            return ReportDetailSerializer
        return ReportListSerializer

    def perform_create(self, serializer):
        serializer.context["citizen"] = self.request.user
        report = serializer.save()
        return report

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.context["citizen"] = request.user
        serializer.is_valid(raise_exception=True)
        report = serializer.save()
        output = ReportDetailSerializer(report, context=self.get_serializer_context())
        headers = self.get_success_headers(output.data)
        return Response(output.data, status=status.HTTP_201_CREATED, headers=headers)

    # Comments feature removed

    @action(detail=False, methods=["get"], url_path="eligibles-ignore", permission_classes=[InternalAPIPermission])
    def eligible_for_ignore(self, request, *args, **kwargs):
        try:
            hours = int(request.query_params.get("hours", 168))
        except (TypeError, ValueError):
            return Response({"detail": "Parâmetro de horas inválido."}, status=status.HTTP_400_BAD_REQUEST)
        data = report_repository.get_reports_eligible_for_ignore(hours)
        return Response({"results": data})

    @action(detail=False, methods=["get"], url_path="avg-resolution", permission_classes=[IsAdminUser])
    def average_resolution(self, request, *args, **kwargs):
        data = report_repository.get_average_resolution_time_by_category()
        return Response({"results": data})


class DashboardViewSet(viewsets.ViewSet):
    permission_classes = [IsAdminUser]

    def list(self, request, *args, **kwargs):
        open_by_neighborhood = report_repository.get_open_reports_grouped_by_neighborhood()
        weekly_series = report_repository.get_weekly_series_by_status()
        return Response(
            {
                "open_by_neighborhood": open_by_neighborhood,
                "weekly_series": weekly_series,
            }
        )


class SystemOpsViewSet(viewsets.ViewSet):
    permission_classes = [InternalAPIPermission]

    @action(detail=False, methods=["post"], url_path="backup/full")
    def backup_full(self, request, *args, **kwargs):
        from io import StringIO
        from django.core.management import call_command

        buf = StringIO()
        try:
            call_command("backup_full", stdout=buf)
            return Response({"detail": "Backup completo disparado com sucesso.", "output": buf.getvalue()})
        except Exception as exc:
            return Response(
                {"detail": f"Falha ao executar backup completo: {exc}", "output": buf.getvalue()},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["post"], url_path="backup/diff")
    def backup_diff(self, request, *args, **kwargs):
        from io import StringIO
        from django.core.management import call_command

        buf = StringIO()
        try:
            call_command("backup_diff", stdout=buf)
            return Response({"detail": "Backup diferencial disparado com sucesso.", "output": buf.getvalue()})
        except Exception as exc:
            return Response(
                {"detail": f"Falha ao executar backup diferencial: {exc}", "output": buf.getvalue()},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
