from __future__ import annotations

from typing import Any, List

from rest_framework import serializers

from core.reports.models import Attachment, Category, Comment, Report, Tag


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "description", "department"]


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ["id", "name"]


class AttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Attachment
        fields = ["id", "file", "created_at"]


class CommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.get_full_name", read_only=True)

    class Meta:
        model = Comment
        fields = ["id", "author", "author_name", "content", "created_at"]
        read_only_fields = ["id", "author", "author_name", "created_at"]


class ReportListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Report
        fields = [
            "id",
            "title",
            "priority",
            "status",
            "category",
            "category_name",
            "created_at",
            "last_status_at",
            "neighborhood",
            "tags",
        ]


class ReportDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    attachments = AttachmentSerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)

    class Meta:
        model = Report
        fields = [
            "id",
            "title",
            "description",
            "priority",
            "status",
            "indeferment_reason",
            "address",
            "neighborhood",
            "latitude",
            "longitude",
            "created_at",
            "last_status_at",
            "category",
            "tags",
            "attachments",
            "comments",
        ]


class ReportCreateSerializer(serializers.ModelSerializer):
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)
    attachments = serializers.ListField(
        child=serializers.FileField(allow_empty_file=False, use_url=False),
        required=False,
        write_only=True,
    )

    class Meta:
        model = Report
        fields = [
            "id",
            "title",
            "description",
            "priority",
            "address",
            "neighborhood",
            "latitude",
            "longitude",
            "category",
            "tags",
            "attachments",
        ]
        read_only_fields = ["id"]

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        if not attrs.get("tags"):
            raise serializers.ValidationError({"tags": "Selecione ao menos uma tag."})
        return attrs

    def validate_attachments(self, value):
        allowed_types = {"image/jpeg", "image/png", "image/gif"}
        max_size = 5 * 1024 * 1024
        for uploaded in value:
            content_type = getattr(uploaded, "content_type", None)
            if content_type and content_type not in allowed_types:
                raise serializers.ValidationError("Tipo de arquivo não permitido.")
            if uploaded.size > max_size:
                raise serializers.ValidationError("Arquivo excede o tamanho máximo de 5MB.")
        return value

    def create(self, validated_data: dict[str, Any]) -> Report:
        tags = validated_data.pop("tags", [])
        attachments: List[Any] = validated_data.pop("attachments", [])
        user = self.context["request"].user
        report = Report.objects.create(citizen=user, **validated_data)
        report.tags.set(tags)
        for uploaded in attachments:
            Attachment.objects.create(report=report, file=uploaded)
        return report


class CommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ["content"]

    def create(self, validated_data: dict[str, Any]) -> Comment:
        report: Report = self.context["report"]
        user = self.context["request"].user
        return Comment.objects.create(report=report, author=user, **validated_data)
