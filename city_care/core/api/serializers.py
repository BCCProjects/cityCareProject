from __future__ import annotations

from typing import Iterable

from django.core.exceptions import ValidationError
from rest_framework import serializers

from accounts.models import Citizen
from accounts.serializers import CitySerializer
from core.reports.models import Attachment, Category, Department, Report, ReportComment, Tag
from core.services.report_service import ReportService


class MultipleFileField(serializers.ListField):
    """
    ListField helper that knows how to pull multiple uploaded files out of a
    Django QueryDict (request.data/request.FILES) using getlist so mobile
    clients can send repeated `attachments` keys in multipart requests.
    """

    def get_value(self, dictionary):
        if hasattr(dictionary, "getlist"):
            if self.field_name in dictionary:
                return dictionary.getlist(self.field_name)
            return serializers.empty
        return super().get_value(dictionary)


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


class ReportCommentSerializer(serializers.ModelSerializer):
    citizen_name = serializers.SerializerMethodField()
    employee_name = serializers.SerializerMethodField()

    class Meta:
        model = ReportComment
        fields = ("id", "message", "citizen_name", "employee_name", "created_at")
        read_only_fields = fields

    def get_citizen_name(self, obj):
        if obj.citizen_id:
            return obj.citizen.get_full_name()
        return None

    def get_employee_name(self, obj):
        if obj.employee_id:
            return obj.employee.get_full_name() if hasattr(obj.employee, "get_full_name") else obj.employee.email
        return None


class ReportCommentCreateSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=500)


class ReportListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(read_only=True, many=True)
    city = CitySerializer(read_only=True)

    class Meta:
        model = Report
        fields = (
            "id",
            "title",
            "status",
            "priority",
            "created_at",
            "city",
            "category",
            "tags",
        )


class ReportDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    department = DepartmentSerializer(read_only=True)
    tags = TagSerializer(read_only=True, many=True)
    attachments = AttachmentSerializer(read_only=True, many=True)
    organization = serializers.StringRelatedField(read_only=True)
    city = CitySerializer(read_only=True)

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
            "city",
            "organization",
            "tags",
            "attachments",
        )


class ReportCreateSerializer(serializers.Serializer):
    category_id = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), source="category")
    title = serializers.CharField(max_length=200)
    description = serializers.CharField()
    priority = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    address = serializers.CharField(max_length=255)
    neighborhood = serializers.CharField(max_length=150)
    latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    longitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True, required=False)
    attachments = MultipleFileField(
        child=serializers.FileField(max_length=5 * 1024 * 1024),
        allow_empty=True,
        required=False,
    )

    def validate_attachments(self, value: Iterable):
        max_files = 5
        if len(value) > max_files:
            raise serializers.ValidationError("Limite de 5 anexos por ocorrencia.")
        for file in value:
            if file.size > 5 * 1024 * 1024:
                raise serializers.ValidationError("Cada anexo deve ter no maximo 5MB.")
            if file.content_type not in {"image/jpeg", "image/png", "image/webp"}:
                raise serializers.ValidationError("Formato de anexo nao permitido.")
        return value

    def create(self, validated_data):
        citizen: Citizen = self.context["citizen"]
        attachments = validated_data.pop("attachments", [])
        tags = validated_data.pop("tags", [])
        category = validated_data["category"]
        department = category.department
        priority = validated_data.pop("priority", None)
        try:
            report = ReportService.create_report(
                citizen,
                tags=tags,
                attachments=attachments,
                department=department,
                priority=priority,
                **validated_data,
            )
        except ValidationError as exc:
            if hasattr(exc, "message_dict"):
                raise serializers.ValidationError(exc.message_dict)
            raise serializers.ValidationError(exc.messages)
        return report
