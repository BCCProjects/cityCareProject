from __future__ import annotations

from typing import Iterable

from django.core.exceptions import ValidationError
from django.db import transaction
from rest_framework import serializers

from accounts.models import Citizen
from core.reports.models import Attachment, Category, Comment, Department, Report, Tag
from core.services.report_service import ReportService


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ("id", "name", "email", "phone", "description")


class CategorySerializer(serializers.ModelSerializer):
    department = DepartmentSerializer(read_only=True)

    class Meta:
        model = Category
        fields = ("id", "name", "slug", "description", "department")


class CategoryCreateSerializer(serializers.ModelSerializer):
    department_id = serializers.PrimaryKeyRelatedField(
        queryset=Department.objects.all(), source="department", write_only=True
    )

    class Meta:
        model = Category
        fields = ("id", "name", "slug", "description", "department_id")
        read_only_fields = ("id",)


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ("id", "name", "slug")


class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = ("id", "file", "description")
        read_only_fields = ("id",)


class CommentSerializer(serializers.ModelSerializer):
    citizen_name = serializers.CharField(source="citizen.full_name", read_only=True)

    class Meta:
        model = Comment
        fields = ("id", "message", "created_at", "citizen_name")
        read_only_fields = ("id", "created_at", "citizen_name")


class ReportListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(read_only=True, many=True)

    class Meta:
        model = Report
        fields = (
            "id",
            "title",
            "status",
            "priority",
            "created_at",
            "category",
            "tags",
        )


class ReportDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    department = DepartmentSerializer(read_only=True)
    tags = TagSerializer(read_only=True, many=True)
    attachments = AttachmentSerializer(read_only=True, many=True)
    comments = CommentSerializer(read_only=True, many=True)

    class Meta:
        model = Report
        fields = (
            "id",
            "title",
            "description",
            "priority",
            "status",
            "denied_reason",
            "address",
            "neighborhood",
            "latitude",
            "longitude",
            "created_at",
            "last_status_at",
            "category",
            "department",
            "tags",
            "attachments",
            "comments",
        )


class ReportCreateSerializer(serializers.Serializer):
    category_id = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), source="category")
    title = serializers.CharField(max_length=200)
    description = serializers.CharField()
    priority = serializers.CharField()
    address = serializers.CharField(max_length=255)
    neighborhood = serializers.CharField(max_length=150)
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)
    attachments = serializers.ListField(
        child=serializers.FileField(max_length=5 * 1024 * 1024),
        allow_empty=True,
        required=False,
    )

    def validate_attachments(self, value: Iterable):
        max_files = 5
        if len(value) > max_files:
            raise serializers.ValidationError("Limite de 5 anexos por ocorrÃªncia.")
        for file in value:
            if file.size > 5 * 1024 * 1024:
                raise serializers.ValidationError("Cada anexo deve ter no mÃ¡ximo 5MB.")
            if file.content_type not in {"image/jpeg", "image/png", "image/webp"}:
                raise serializers.ValidationError("Formato de anexo nÃ£o permitido.")
        return value

    def validate_priority(self, value: str):
        normalized = ReportService.normalize_priority(value)
        valid_values = {choice[0] for choice in Report._meta.get_field('priority').choices}
        if normalized not in valid_values:
            raise serializers.ValidationError('Prioridade invalida.')
        return normalized

    def create(self, validated_data):
        citizen: Citizen = self.context["citizen"]
        attachments = validated_data.pop("attachments", [])
        tags = validated_data.pop("tags", [])
        category = validated_data["category"]
        department = category.department
        try:
            report = ReportService.create_report(
                citizen,
                tags=tags,
                attachments=attachments,
                department=department,
                **validated_data,
            )
        except ValidationError as exc:
            raise serializers.ValidationError(exc.message_dict if hasattr(exc, "message_dict") else exc.messages)
        return report


class CommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ("id", "message")
        read_only_fields = ("id",)

    def create(self, validated_data):
        report: Report = self.context["report"]
        citizen: Citizen = self.context["citizen"]
        with transaction.atomic():
            comment = Comment.objects.create(report=report, citizen=citizen, **validated_data)
        return comment






