from __future__ import annotations

from django.shortcuts import get_object_or_404
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from core.reports.models import Category, Report, Tag
from core.reports.serializers import (
    CategorySerializer,
    CommentCreateSerializer,
    ReportCreateSerializer,
    ReportDetailSerializer,
    ReportListSerializer,
    TagSerializer,
)


class CategoryViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Category.objects.select_related("department")
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated]


class TagViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticated]


class ReportViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, JSONParser]

    def get_queryset(self):
        queryset = (
            Report.objects.filter(citizen=self.request.user)
            .select_related("category", "category__department")
            .prefetch_related("tags", "attachments", "comments__author")
        )
        status_param = self.request.query_params.get("status")
        category_param = self.request.query_params.get("category")
        if status_param:
            queryset = queryset.filter(status=status_param)
        if category_param:
            queryset = queryset.filter(category_id=category_param)
        return queryset

    def get_serializer_class(self):
        if self.action == "retrieve":
            return ReportDetailSerializer
        if self.action == "create":
            return ReportCreateSerializer
        return ReportListSerializer


class ReportCommentCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, report_pk: int) -> Response:
        report = get_object_or_404(Report, pk=report_pk, citizen=request.user)
        serializer = CommentCreateSerializer(data=request.data, context={"request": request, "report": report})
        serializer.is_valid(raise_exception=True)
        comment = serializer.save()
        return Response({"id": comment.id, "content": comment.content}, status=status.HTTP_201_CREATED)
