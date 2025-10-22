from __future__ import annotations

from rest_framework import filters, mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from accounts.models import Citizen
from core.api.serializers import (
    CategorySerializer,
    CommentCreateSerializer,
    CommentSerializer,
    ReportCreateSerializer,
    ReportDetailSerializer,
    ReportListSerializer,
    TagSerializer,
)
from core.repositories import report_repository
from core.reports.models import Category, Report, ReportStatus, Tag


class CategoryViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Category.objects.select_related("department").all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None


class TagViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None


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
        citizen: Citizen = self.request.user
        queryset = (
            Report.objects.filter(citizen=citizen)
            .select_related("category", "category__department", "department")
            .prefetch_related("tags", "attachments", "comments__citizen")
        )
        status_param = self.request.query_params.get("status")
        category_param = self.request.query_params.get("category")
        if status_param in ReportStatus.values:
            queryset = queryset.filter(status=status_param)
        if category_param:
            queryset = queryset.filter(category_id=category_param)
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

    @action(detail=True, methods=["post"], url_path="comments")
    def add_comment(self, request, *args, **kwargs):
        report = self.get_object()
        serializer = CommentCreateSerializer(data=request.data)
        serializer.context.update({"report": report, "citizen": request.user})
        serializer.is_valid(raise_exception=True)
        comment = serializer.save()
        return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], url_path="eligibles-ignore")
    def eligible_for_ignore(self, request, *args, **kwargs):
        try:
            hours = int(request.query_params.get("hours", 168))
        except (TypeError, ValueError):
            return Response({"detail": "Parâmetro de horas inválido."}, status=status.HTTP_400_BAD_REQUEST)
        data = report_repository.get_reports_eligible_for_ignore(hours)
        return Response({"results": data})

    @action(detail=False, methods=["get"], url_path="avg-resolution")
    def average_resolution(self, request, *args, **kwargs):
        data = report_repository.get_average_resolution_time_by_category()
        return Response({"results": data})


class DashboardViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request, *args, **kwargs):
        open_by_neighborhood = report_repository.get_open_reports_grouped_by_neighborhood()
        weekly_series = report_repository.get_weekly_series_by_status()
        return Response(
            {
                "open_by_neighborhood": open_by_neighborhood,
                "weekly_series": weekly_series,
            }
        )
