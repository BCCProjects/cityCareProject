from __future__ import annotations

from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.authentication import SessionAuthentication
from accounts.models import Citizen, Administrator
from core.api.serializers import (
    CategorySerializer,
    CategoryCreateSerializer,
    CommentCreateSerializer,
    CommentSerializer,
    DepartmentSerializer,
    ReportCreateSerializer,
    ReportDetailSerializer,
    ReportListSerializer,
    TagSerializer,
)
from core.repositories import report_repository
from core.reports.models import Category, Department, Report, ReportStatus, Tag
from core.api.authentication import AdminJWTAuthentication, CitizenJWTAuthentication
from core.api.responses import ApiResponseMixin


class CategoryViewSet(
    ApiResponseMixin,
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
    authentication_classes = (AdminJWTAuthentication, CitizenJWTAuthentication, SessionAuthentication)
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
            paginated = self.get_paginated_response(serializer.data)
            return self.success(data=paginated.data, code="categories.list")
        serializer = self.get_serializer(qs, many=True)
        return self.success(data=serializer.data, code="categories.list")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        category = serializer.save()
        output = CategorySerializer(category, context=self.get_serializer_context())
        return self.success(
            data=output.data,
            status_code=status.HTTP_201_CREATED,
            code="categories.create",
            message="Categoria criada com sucesso.",
        )

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return self.success(data=response.data, code="categories.detail")


class TagViewSet(
    ApiResponseMixin,
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
    authentication_classes = (AdminJWTAuthentication, CitizenJWTAuthentication, SessionAuthentication)
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
        return self.success(
            data=output.data,
            status_code=status.HTTP_201_CREATED,
            code="tags.create",
            message="Tag criada com sucesso.",
        )

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return self.success(data=response.data, code="tags.list")

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return self.success(data=response.data, code="tags.detail")


class DepartmentViewSet(
    ApiResponseMixin,
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
    authentication_classes = (AdminJWTAuthentication, CitizenJWTAuthentication, SessionAuthentication)
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
        return self.success(
            data=output.data,
            status_code=status.HTTP_201_CREATED,
            code="departments.create",
            message="Departamento criado com sucesso.",
        )

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return self.success(data=response.data, code="departments.list")

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return self.success(data=response.data, code="departments.detail")


class ReportViewSet(
    ApiResponseMixin,
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
            .prefetch_related("tags", "attachments", "comments__citizen")
        )

        if isinstance(user, Administrator) and getattr(user, "is_staff", False):
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

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return self.success(data=response.data, code="reports.list")

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return self.success(data=response.data, code="reports.detail")

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
            status_code=status.HTTP_201_CREATED,
            code="reports.create",
            message="Ocorrência registrada.",
        )

    @action(detail=True, methods=["post"], url_path="comments")
    def add_comment(self, request, *args, **kwargs):
        report = self.get_object()
        serializer = CommentCreateSerializer(data=request.data)
        serializer.context.update({"report": report, "citizen": request.user})
        serializer.is_valid(raise_exception=True)
        comment = serializer.save()
        return self.success(
            data=CommentSerializer(comment).data,
            status_code=status.HTTP_201_CREATED,
            code="reports.comments.create",
            message="Comentário adicionado.",
        )

    @action(
        detail=False,
        methods=["get"],
        url_path="eligibles-ignore",
        permission_classes=[IsAdminUser],
    )
    def eligible_for_ignore(self, request, *args, **kwargs):
        try:
            hours = int(request.query_params.get("hours", 168))
        except (TypeError, ValueError):
            return self.error(
                message="Parâmetro de horas inválido.",
                code="reports.eligible.invalid_hours",
            )
        data = report_repository.get_reports_eligible_for_ignore(hours)
        return self.success(data={"results": data}, code="reports.eligible.list")

    @action(detail=False, methods=["get"], url_path="avg-resolution", permission_classes=[IsAdminUser])
    def average_resolution(self, request, *args, **kwargs):
        data = report_repository.get_average_resolution_time_by_category()
        return self.success(data={"results": data}, code="reports.avg_resolution")


class DashboardViewSet(ApiResponseMixin, viewsets.ViewSet):
    permission_classes = [IsAdminUser]

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
