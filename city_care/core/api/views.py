from __future__ import annotations

from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from accounts.models import Citizen, City, Employee, Organization, State
from accounts.serializers import CitySerializer, OrganizationSerializer, StateSerializer
from core.api.responses import ApiResponseMixin
from core.api.serializers import (
    CategorySerializer,
    CategoryCreateSerializer,
    DepartmentSerializer,
    ReportCreateSerializer,
    ReportDetailSerializer,
    ReportListSerializer,
    ReportCommentCreateSerializer,
    ReportCommentSerializer,
    TagSerializer,
)
from core.repositories import report_repository
from core.reports.models import Category, Department, Report, ReportStatus, Tag
from core.api.authentication import CitizenJWTAuthentication, EmployeeJWTAuthentication
from core.api.permissions import InternalAPIPermission


class BaseApiViewSet(ApiResponseMixin, viewsets.GenericViewSet):
    response_namespace = ""

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return self.wrap_drf_response(response, "list")

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return self.wrap_drf_response(response, "detail")

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        return self.wrap_drf_response(response, "create")

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        return self.wrap_drf_response(response, "update")

    def partial_update(self, request, *args, **kwargs):
        response = super().partial_update(request, *args, **kwargs)
        return self.wrap_drf_response(response, "update")

    def destroy(self, request, *args, **kwargs):
        response = super().destroy(request, *args, **kwargs)
        return self.wrap_drf_response(response, "delete")


class StateViewSet(
    BaseApiViewSet,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
):
    queryset = State.objects.all()
    serializer_class = StateSerializer
    permission_classes = [AllowAny]
    authentication_classes = (EmployeeJWTAuthentication, CitizenJWTAuthentication, SessionAuthentication)
    pagination_class = None
    response_namespace = "states"

    def get_permissions(self):
        if self.action in {"list", "retrieve"}:
            return [AllowAny()]
        return [InternalAPIPermission()]


class CityViewSet(
    BaseApiViewSet,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
):
    queryset = City.objects.select_related("state").all()
    serializer_class = CitySerializer
    permission_classes = [AllowAny]
    authentication_classes = (EmployeeJWTAuthentication, CitizenJWTAuthentication, SessionAuthentication)
    pagination_class = None
    response_namespace = "cities"

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
    BaseApiViewSet,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
):
    queryset = Organization.objects.select_related("city", "city__state").all()
    serializer_class = OrganizationSerializer
    permission_classes = [InternalAPIPermission]
    authentication_classes: tuple = ()
    pagination_class = None
    response_namespace = "organizations"

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
    BaseApiViewSet,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
):
    queryset = Category.objects.select_related("department").all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = (EmployeeJWTAuthentication, CitizenJWTAuthentication, SessionAuthentication)
    pagination_class = None
    response_namespace = "categories"

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
            paginated = self.get_paginated_response(serializer.data)
            return self.wrap_drf_response(paginated, "list")
        serializer = self.get_serializer(qs, many=True)
        return self.success(data=serializer.data, code=self.build_code("list"))

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        category = serializer.save()
        output = CategorySerializer(category, context=self.get_serializer_context())
        return self.success(
            data=output.data,
            code=self.build_code("create"),
            status_code=status.HTTP_201_CREATED,
        )


class TagViewSet(
    BaseApiViewSet,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = (EmployeeJWTAuthentication, CitizenJWTAuthentication, SessionAuthentication)
    pagination_class = None
    response_namespace = "tags"

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tag = serializer.save()
        output = TagSerializer(tag, context=self.get_serializer_context())
        return self.success(
            data=output.data,
            code=self.build_code("create"),
            status_code=status.HTTP_201_CREATED,
        )


class DepartmentViewSet(
    BaseApiViewSet,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = (EmployeeJWTAuthentication, CitizenJWTAuthentication, SessionAuthentication)
    pagination_class = None
    response_namespace = "departments"

    def get_permissions(self):
        if self.action in {"create", "update", "partial_update", "destroy"}:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        department = serializer.save()
        output = DepartmentSerializer(department, context=self.get_serializer_context())
        return self.success(
            data=output.data,
            code=self.build_code("create"),
            status_code=status.HTTP_201_CREATED,
        )


class ReportViewSet(
    BaseApiViewSet,
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
):
    permission_classes = [IsAuthenticated]
    authentication_classes = (EmployeeJWTAuthentication, CitizenJWTAuthentication, SessionAuthentication)
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["created_at", "priority"]
    ordering = ["-created_at"]
    response_namespace = "reports"

    def get_queryset(self):
        user = self.request.user
        base_qs = (
            Report.objects.select_related(
                "category",
                "category__department",
                "department",
                "city",
                "city__state",
                "organization",
            )
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
        return self.success(
            data=output.data,
            code=self.build_code("create"),
            status_code=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["get"], url_path="eligibles-ignore", permission_classes=[InternalAPIPermission])
    def eligible_for_ignore(self, request, *args, **kwargs):
        try:
            hours = int(request.query_params.get("hours", 168))
        except (TypeError, ValueError):
            return self.error(
                errors={"detail": "Parametro de horas invalido."},
                code=self.build_code("eligible.invalid_hours"),
                status_code=status.HTTP_400_BAD_REQUEST,
            )
        data = report_repository.get_reports_eligible_for_ignore(hours)
        return self.success(
            data={"results": data},
            code=self.build_code("eligible.list"),
        )

    @action(detail=False, methods=["get"], url_path="avg-resolution", permission_classes=[IsAdminUser])
    def average_resolution(self, request, *args, **kwargs):
        data = report_repository.get_average_resolution_time_by_category()
        return self.success(
            data={"results": data},
            code=self.build_code("avg_resolution"),
        )

    @action(detail=True, methods=["post"], url_path="comment", permission_classes=[IsAuthenticated])
    def add_comment(self, request, *args, **kwargs):
        report = self.get_object()
        serializer = ReportCommentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        message = serializer.validated_data["message"]
        user = request.user
        citizen = user if isinstance(user, Citizen) else None
        employee = user if isinstance(user, Employee) else None
        if citizen and report.citizen_id != citizen.id:
            return self.error(
                errors={"detail": "Ocorrencia nao encontrada."},
                code=self.build_code("comments.not_found"),
                status_code=status.HTTP_404_NOT_FOUND,
            )
        comment = report.comments.create(message=message, citizen=citizen, employee=employee)
        data = ReportCommentSerializer(comment).data
        return self.success(
            data=data,
            code=self.build_code("comments.create"),
            status_code=status.HTTP_201_CREATED,
        )


class DashboardViewSet(ApiResponseMixin, viewsets.ViewSet):
    permission_classes = [IsAdminUser]
    authentication_classes = (EmployeeJWTAuthentication, SessionAuthentication)
    response_namespace = "dashboard"

    def list(self, request, *args, **kwargs):
        open_by_neighborhood = report_repository.get_open_reports_grouped_by_neighborhood()
        weekly_series = report_repository.get_weekly_series_by_status()
        return self.success(
            data={
                "results": {
                    "open_by_neighborhood": open_by_neighborhood,
                    "weekly_series": weekly_series,
                }
            },
            code="dashboard.summary",
        )

    @action(detail=False, methods=["post"], url_path="export")
    def export(self, request, *args, **kwargs):
        """
        Export dashboard data as JSON or CSV for admins.

        Body parameters (JSON):
        - format: "json" (default) or "csv"
        - start_date, end_date: optional, YYYY-MM-DD, filter by report.created_at
        """
        from datetime import datetime
        from django.http import HttpResponse
        import csv

        data = request.data or {}
        export_format = str(data.get("format", "json")).lower()
        start_date_raw = data.get("start_date")
        end_date_raw = data.get("end_date")

        start_date = end_date = None
        for label, raw in (("start_date", start_date_raw), ("end_date", end_date_raw)):
            if raw:
                try:
                    parsed = datetime.strptime(raw, "%Y-%m-%d").date()
                    if label == "start_date":
                        start_date = parsed
                    else:
                        end_date = parsed
                except ValueError:
                    return self.error(
                        errors={"detail": f"Formato invalido para {label}. Use YYYY-MM-DD."},
                        code="dashboard.export.invalid_date",
                        status_code=status.HTTP_400_BAD_REQUEST,
                    )

        open_by_neighborhood = report_repository.get_open_reports_grouped_by_neighborhood()
        weekly_series = report_repository.get_weekly_series_by_status(start_date=start_date, end_date=end_date)

        payload = {
            "open_by_neighborhood": open_by_neighborhood,
            "weekly_series": weekly_series,
        }

        if export_format == "json":
            return self.success(
                data={"results": payload},
                code="dashboard.export",
            )

        if export_format == "csv":
            response = HttpResponse(content_type="text/csv")
            response["Content-Disposition"] = 'attachment; filename="dashboard_report.csv"'

            writer = csv.writer(response)

            writer.writerow(["Open reports by neighborhood"])
            writer.writerow(["neighborhood", "priority", "total"])
            for item in open_by_neighborhood:
                writer.writerow([item.get("neighborhood") or "", item.get("priority") or "", item.get("total") or 0])

            writer.writerow([])
            writer.writerow(["Weekly series by status"])
            writer.writerow(["week", "status", "total"])
            for item in weekly_series:
                week = item.get("week")
                writer.writerow([week, item.get("status") or "", item.get("total") or 0])

            return response

        return self.error(
            errors={"detail": "Formato invalido. Use 'json' ou 'csv'."},
            code="dashboard.export.invalid_format",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
class SystemOpsViewSet(ApiResponseMixin, viewsets.ViewSet):
    permission_classes = [InternalAPIPermission]
    response_namespace = "system"

    @action(detail=False, methods=["post"], url_path="backup/full")
    def backup_full(self, request, *args, **kwargs):
        from io import StringIO
        from django.core.management import call_command

        buf = StringIO()
        try:
            call_command("backup_full", stdout=buf)
            return self.success(
                data={"detail": "Backup completo disparado com sucesso.", "output": buf.getvalue()},
                code="system.backup_full",
            )
        except Exception as exc:
            return self.error(
                errors={"detail": f"Falha ao executar backup completo: {exc}", "output": buf.getvalue()},
                code="system.backup_full.error",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["post"], url_path="backup/diff")
    def backup_diff(self, request, *args, **kwargs):
        from io import StringIO
        from django.core.management import call_command

        buf = StringIO()
        try:
            call_command("backup_diff", stdout=buf)
            return self.success(
                data={"detail": "Backup diferencial disparado com sucesso.", "output": buf.getvalue()},
                code="system.backup_diff",
            )
        except Exception as exc:
            return self.error(
                errors={"detail": f"Falha ao executar backup diferencial: {exc}", "output": buf.getvalue()},
                code="system.backup_diff.error",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
