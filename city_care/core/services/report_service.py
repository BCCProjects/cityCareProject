from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Iterable

from django.core.exceptions import ValidationError
from django.core.files import File
from django.db import transaction
from django.utils import timezone

from accounts.models import Administrator, Citizen
from core.reports.models import (
    Category,
    Department,
    Report,
    ReportPriority,
    ReportStatus,
    StatusHistory,
    Tag,
)
from core.services.exceptions import InvalidStatusTransition


@dataclass
class StatusTransitionResult:
    report: Report
    history: StatusHistory


class ReportService:
    PRIORITY_CANONICAL_VALUES: dict[str, str] = {
        ReportPriority.LOW: ReportPriority.LOW,
        ReportPriority.MEDIUM: ReportPriority.MEDIUM,
        ReportPriority.HIGH: ReportPriority.HIGH,
        "BAIXA": ReportPriority.LOW,
        "BAIXAS": ReportPriority.LOW,
        "BAIXO": ReportPriority.LOW,
        "MEDIA": ReportPriority.MEDIUM,
        "MÉDIA": ReportPriority.MEDIUM,
        "MEDIAS": ReportPriority.MEDIUM,
        "MÉDIAS": ReportPriority.MEDIUM,
        "ALTA": ReportPriority.HIGH,
        "ALTAS": ReportPriority.HIGH,
        "ALTO": ReportPriority.HIGH,
    }

    ALLOWED_TRANSITIONS: dict[str, set[str]] = {
        ReportStatus.ABERTO: {ReportStatus.ANALISANDO, ReportStatus.IGNORADO},
        ReportStatus.ANALISANDO: {
            ReportStatus.DEFERIDO,
            ReportStatus.INDEFERIDO,
            ReportStatus.IGNORADO,
        },
        ReportStatus.DEFERIDO: {
            ReportStatus.EM_ANDAMENTO,
            ReportStatus.INDEFERIDO,
            ReportStatus.IGNORADO,
        },
        ReportStatus.EM_ANDAMENTO: {
            ReportStatus.CONCLUIDO,
            ReportStatus.INDEFERIDO,
            ReportStatus.IGNORADO,
        },
        ReportStatus.INDEFERIDO: set(),
        ReportStatus.CONCLUIDO: set(),
        ReportStatus.IGNORADO: set(),
    }

    @classmethod
    def normalize_priority(cls, priority: str | None) -> str | None:
        if priority is None:
            return None
        normalized = str(priority).strip().upper()
        return cls.PRIORITY_CANONICAL_VALUES.get(normalized, normalized)

    @staticmethod
    def _get_default_admin() -> Administrator | None:
        return Administrator.objects.order_by("id").first()

    @staticmethod
    def _quantize_coordinate(value) -> Decimal:
        if isinstance(value, Decimal):
            return value.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
        return Decimal(str(value)).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)

    @classmethod
    def _attach_files(cls, report: Report, attachments: Iterable) -> None:
        for attachment in attachments or []:
            description = getattr(attachment, "description", "")

            if isinstance(attachment, (str, Path)):
                path = Path(attachment)
                with path.open("rb") as fh:
                    report.attachments.create(file=File(fh, name=path.name), description=description)
                continue

            if isinstance(attachment, File):
                report.attachments.create(file=attachment, description=description)
                continue

            file_attr = getattr(attachment, "file", None)
            if isinstance(file_attr, (str, Path)):
                path = Path(file_attr)
                with path.open("rb") as fh:
                    report.attachments.create(file=File(fh, name=path.name), description=description)
                continue

            if isinstance(file_attr, File):
                report.attachments.create(file=file_attr, description=description)
                continue

            if hasattr(attachment, "read"):
                name = getattr(attachment, "name", "attachment")
                if hasattr(attachment, "seek"):
                    attachment.seek(0)
                report.attachments.create(file=File(attachment, name=name), description=description)
                continue

            if file_attr and hasattr(file_attr, "read"):
                if hasattr(file_attr, "seek"):
                    file_attr.seek(0)
                name = getattr(file_attr, "name", getattr(attachment, "name", "attachment"))
                report.attachments.create(file=File(file_attr, name=name), description=description)
                continue

            report.attachments.create(file=attachment, description=description)

    @classmethod
    @transaction.atomic
    def create_report(
        cls,
        *,
        citizen: Citizen,
        category: Category,
        department: Department,
        title: str,
        description: str,
        priority: str,
        address: str,
        neighborhood: str,
        latitude,
        longitude,
        tags: Iterable[Tag],
        attachments: Iterable,
    ) -> Report:
        normalized_priority = cls.normalize_priority(priority) or ReportPriority.MEDIUM

        if Report.objects.filter(category=category, latitude=latitude, longitude=longitude).exists():
            raise ValidationError(
                {
                    "non_field_errors": [
                        "Já existe uma ocorrência para esta categoria neste mesmo ponto (lat/lng).",
                    ]
                }
            )

        default_admin = cls._get_default_admin()

        report = Report(
            citizen=citizen,
            category=category,
            department=department,
            assigned_to=default_admin,
            title=title,
            description=description,
            priority=normalized_priority,
            address=address,
            neighborhood=neighborhood,
            latitude=cls._quantize_coordinate(latitude),
            longitude=cls._quantize_coordinate(longitude),
        )
        report.full_clean()
        report.save()

        if tags:
            report.tags.set(tags)

        cls._attach_files(report, attachments)

        StatusHistory.objects.create(
            report=report,
            old_status=None,
            new_status=report.status,
            administrator=default_admin,
            reason="Criação do relatório",
        )
        return report

    @classmethod
    @transaction.atomic
    def transition_status(
        cls,
        report_id: int,
        new_status: str,
        *,
        administrator: Administrator,
        notes: str = "",
        denied_reason: str | None = None,
    ) -> StatusTransitionResult:
        if new_status not in ReportStatus.values:
            raise InvalidStatusTransition("Status de destino inválido.")

        report = (
            Report.objects.select_for_update()
            .select_related("category", "department")
            .get(pk=report_id)
        )

        allowed = cls.ALLOWED_TRANSITIONS.get(report.status, set())
        if new_status not in allowed:
            raise InvalidStatusTransition("Transição não permitida para o status informado.")

        if new_status == ReportStatus.INDEFERIDO and not denied_reason:
            raise InvalidStatusTransition("Motivo é obrigatório para indeferir.")

        previous_status = report.status
        report.status = new_status
        report.last_status_at = timezone.now()
        if new_status == ReportStatus.INDEFERIDO:
            report.denied_reason = denied_reason or ""
        elif report.denied_reason and new_status != ReportStatus.INDEFERIDO:
            report.denied_reason = ""
        report.full_clean()
        report.save(update_fields=["status", "last_status_at", "denied_reason"])

        history = StatusHistory.objects.create(
            report=report,
            old_status=previous_status,
            new_status=new_status,
            administrator=administrator,
            reason=notes,
        )
        return StatusTransitionResult(report=report, history=history)


__all__ = [
    "ReportService",
    "ReportPriority",
    "StatusTransitionResult",
]
