from __future__ import annotations

from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator
from django.db import models
from django.utils import timezone

from accounts.models import Administrator, Citizen
from django.conf import settings
from .storage import AttachmentStorage


class Department(models.Model):
    name = models.CharField(max_length=150, unique=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:  # pragma: no cover
        return self.name


class Category(models.Model):
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="categories")
    name = models.CharField(max_length=150, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:  # pragma: no cover
        return self.name


class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:  # pragma: no cover
        return self.name


class ReportPriority(models.TextChoices):
    LOW = "BAIXO", "Baixo"
    MEDIUM = "MODERADO", "Moderado"
    HIGH = "ALTO", "Alto"


class ReportStatus(models.TextChoices):
    ABERTO = "ABERTO", "Aberto"
    ANALISANDO = "ANALISANDO", "Analisando"
    DEFERIDO = "DEFERIDO", "Deferido"
    INDEFERIDO = "INDEFERIDO", "Indeferido"
    EM_ANDAMENTO = "EM_ANDAMENTO", "Em andamento"
    CONCLUIDO = "CONCLUIDO", "Concluído"
    IGNORADO = "IGNORADO", "Ignorado"


class Report(models.Model):
    citizen = models.ForeignKey(Citizen, on_delete=models.PROTECT, related_name="reports")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="reports")
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="reports")
    assigned_to = models.ForeignKey(
        Administrator,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assigned_reports",
    )
    title = models.CharField(max_length=200, validators=[MinLengthValidator(10)])
    description = models.TextField()
    priority = models.CharField(max_length=12, choices=ReportPriority.choices, default=ReportPriority.MEDIUM)
    address = models.CharField(max_length=255)
    neighborhood = models.CharField(max_length=150)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    status = models.CharField(max_length=20, choices=ReportStatus.choices, default=ReportStatus.ABERTO)
    denied_reason = models.TextField(blank=True)
    last_status_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    tags = models.ManyToManyField(Tag, through="ReportTag", related_name="reports")

    class Meta:
        ordering = ("-created_at",)
        constraints = [
            models.CheckConstraint(
                name="check_latitude_range",
                check=models.Q(latitude__gte=-90) & models.Q(latitude__lte=90),
            ),
            models.CheckConstraint(
                name="check_longitude_range",
                check=models.Q(longitude__gte=-180) & models.Q(longitude__lte=180),
            ),
            models.UniqueConstraint(
                fields=("category", "latitude", "longitude"),
                name="unique_report_category_lat_lng",
            ),
        ]

    def clean(self):
        super().clean()
        if self.category and self.department and self.category.department_id != self.department_id:
            raise ValidationError("Categoria informada nÃ£o pertence ao departamento selecionado.")
        if self.status == ReportStatus.INDEFERIDO and not self.denied_reason:
            raise ValidationError({"denied_reason": "Informe o motivo de indeferimento."})

    def __str__(self) -> str:  # pragma: no cover
        return self.title


class ReportTag(models.Model):
    report = models.ForeignKey(Report, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("report", "tag")

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.report_id}-{self.tag_id}"


class Attachment(models.Model):
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="attachments")
    file = models.FileField(
        upload_to="",
        storage=AttachmentStorage() if getattr(settings, "USE_SUPABASE_ATTACHMENTS", True) else None,
    )
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ("created_at",)


class Comment(models.Model):
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="comments")
    citizen = models.ForeignKey(Citizen, on_delete=models.CASCADE, related_name="comments")
    message = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ("created_at",)


class StatusHistory(models.Model):
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name="status_history")
    previous_status = models.CharField(max_length=20, choices=ReportStatus.choices)
    new_status = models.CharField(max_length=20, choices=ReportStatus.choices)
    changed_by = models.ForeignKey(
        Administrator,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="status_changes",
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ("-created_at",)
