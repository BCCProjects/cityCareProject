from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils import timezone


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:  # pragma: no cover - human readable helper
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True)
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="categories")

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:  # pragma: no cover
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=80, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:  # pragma: no cover
        return self.name


class Report(models.Model):
    class Priority(models.TextChoices):
        LOW = "BAIXA", "Baixa"
        MEDIUM = "MEDIA", "Média"
        HIGH = "ALTA", "Alta"

    class Status(models.TextChoices):
        OPEN = "ABERTO", "Aberto"
        ANALYZING = "ANALISANDO", "Analisando"
        APPROVED = "DEFERIDO", "Deferido"
        REJECTED = "INDEFERIDO", "Indeferido"
        IN_PROGRESS = "EM_ANDAMENTO", "Em andamento"
        COMPLETED = "CONCLUIDO", "Concluído"
        IGNORED = "IGNORADO", "Ignorado"

    citizen = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reports")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="reports")
    title = models.CharField(max_length=120)
    description = models.TextField()
    priority = models.CharField(max_length=12, choices=Priority.choices, default=Priority.MEDIUM)
    address = models.CharField(max_length=255)
    neighborhood = models.CharField(max_length=120)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    indeferment_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_status_at = models.DateTimeField(default=timezone.now)
    due_at = models.DateTimeField(null=True, blank=True)

    tags = models.ManyToManyField("Tag", through="ReportTag", related_name="reports")

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                check=models.Q(priority__in=[choice.value for choice in Priority]),
                name="report_priority_valid",
            ),
            models.CheckConstraint(
                check=models.Q(status__in=[choice.value for choice in Status]),
                name="report_status_valid",
            ),
            models.CheckConstraint(
                check=models.Q(latitude__gte=-90) & models.Q(latitude__lte=90),
                name="report_latitude_range",
            ),
            models.CheckConstraint(
                check=models.Q(longitude__gte=-180) & models.Q(longitude__lte=180),
                name="report_longitude_range",
            ),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.title} ({self.get_status_display()})"

    def mark_last_status_now(self) -> None:
        self.last_status_at = timezone.now()

    def is_eligible_for_ignore(self, hours: int = 168) -> bool:
        return (
            self.status != self.Status.IGNORED
            and timezone.now() - self.last_status_at >= timedelta(hours=hours)
        )


class ReportTag(models.Model):
    report = models.ForeignKey(Report, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["report", "tag"], name="unique_report_tag"),
        ]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.report_id}-{self.tag_id}"


class Comment(models.Model):
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="report_comments")
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:  # pragma: no cover
        return f"Comentário de {self.author_id} em {self.report_id}"


class Attachment(models.Model):
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(
        upload_to="attachments/",
        validators=[FileExtensionValidator(allowed_extensions=["png", "jpg", "jpeg", "gif"])],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self) -> str:  # pragma: no cover
        return f"Anexo {self.id}"


class StatusHistory(models.Model):
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="status_history")
    from_status = models.CharField(max_length=20, choices=Report.Status.choices)
    to_status = models.CharField(max_length=20, choices=Report.Status.choices)
    reason = models.TextField(blank=True)
    changed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-changed_at"]

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.report_id}: {self.from_status} -> {self.to_status}"
