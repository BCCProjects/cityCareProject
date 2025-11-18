from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Iterable

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.core.files.base import ContentFile

from accounts.models import Citizen, Employee
from core.repositories import report_repository
from core.reports.models import Report, ReportPriority, ReportStatus, StatusHistory, Tag
from core.services.location_service import (
    CityNotCoveredError,
    LocationResolutionError,
    resolve_city_from_coordinates,
)


class InvalidStatusTransition(Exception):
    pass


@dataclass
class StatusTransitionResult:
    report: Report
    history: StatusHistory


class ReportService:
    ALLOWED_TRANSITIONS: dict[str, set[str]] = {
        ReportStatus.ABERTO: {ReportStatus.ANALISANDO, ReportStatus.IGNORADO},
        ReportStatus.ANALISANDO: {ReportStatus.DEFERIDO, ReportStatus.INDEFERIDO, ReportStatus.IGNORADO},
        ReportStatus.DEFERIDO: {ReportStatus.EM_ANDAMENTO, ReportStatus.INDEFERIDO, ReportStatus.IGNORADO},
        ReportStatus.INDEFERIDO: set(),
        ReportStatus.EM_ANDAMENTO: {ReportStatus.CONCLUIDO, ReportStatus.INDEFERIDO, ReportStatus.IGNORADO},
        ReportStatus.CONCLUIDO: set(),
        ReportStatus.IGNORADO: set(),
    }
    PRIORITY_NORMALIZATION = {
        ReportPriority.LOW: {"BAIXO", "BAIXA", "BAIXAS", "LOW"},
        ReportPriority.MEDIUM: {"MEDIO", "MEDIA", "MEDIAS", "MODERADO", "MODERADA"},
        ReportPriority.HIGH: {"ALTO", "ALTA", "ALTAS", "HIGH"},
    }

    @staticmethod
    def _quantize_coordinate(value) -> Decimal:
        try:
            decimal_value = Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError):
            return Decimal("0.000000")
        return decimal_value.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)

    @staticmethod
    def _normalize_text(value: str) -> str:
        import unicodedata

        normalized = unicodedata.normalize("NFKD", value or "")
        normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
        return normalized.strip().upper()

    @classmethod
    def normalize_priority(cls, value):
        if value is None:
            return None
        normalized = cls._normalize_text(str(value))
        for target, aliases in cls.PRIORITY_NORMALIZATION.items():
            if normalized in aliases:
                return target
        return normalized

    @staticmethod
    def _as_django_file(attachment):
        description = getattr(attachment, "description", "")
        source = getattr(attachment, "file", attachment)
        original_name = getattr(attachment, "name", None)

        if isinstance(source, (str, Path)):
            path = Path(source)
            if not path.exists():
                return None, description
            data = path.read_bytes()
            return ContentFile(data, name=path.name), description

        if hasattr(source, "read"):
            name = getattr(source, "name", None) or original_name or "attachment"
            if hasattr(source, "seek"):
                try:
                    source.seek(0)
                except OSError:
                    pass
            return ContentFile(source.read(), name=name), description

        return None, description

    @staticmethod
    def _attach_files(report: Report, attachments: Iterable) -> None:
        for attachment in attachments:
            file_obj, description = ReportService._as_django_file(attachment)
            if file_obj is None:
                continue
            report.attachments.create(file=file_obj, description=description or "")

    @staticmethod
    def create_report(
        citizen: Citizen,
        *,
        category,
        department,
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
        with transaction.atomic():
            latitude_dec = ReportService._quantize_coordinate(latitude)
            longitude_dec = ReportService._quantize_coordinate(longitude)

            normalized_priority = ReportService.normalize_priority(priority) or ReportPriority.MEDIUM
            if normalized_priority not in ReportPriority.values:
                normalized_priority = ReportPriority.MEDIUM

            if Report.objects.filter(category=category, latitude=latitude_dec, longitude=longitude_dec).exists():
                raise ValidationError({
                    "non_field_errors": [
                        "Ja existe uma ocorrencia para esta categoria neste mesmo ponto (lat/lng).",
                    ]
                })

            try:
                resolved_city = resolve_city_from_coordinates(latitude_dec, longitude_dec)
            except CityNotCoveredError as exc:
                raise ValidationError({"location": str(exc)}) from exc
            except LocationResolutionError as exc:
                raise ValidationError({"location": str(exc)}) from exc

            organization = getattr(resolved_city, "organization", None)
            if organization is None:
                raise ValidationError({"organization": "Nenhuma organizacao vinculada a cidade identificada."})

            default_employee = organization.employees.order_by("id").first()

            attachments_list = list(attachments or [])
            effective_priority = normalized_priority

            report = Report(
                citizen=citizen,
                category=category,
                department=department,
                organization=organization,
                city=resolved_city,
                assigned_to=default_employee,
                title=title,
                description=description,
                priority=effective_priority,
                address=address,
                neighborhood=neighborhood,
                latitude=latitude_dec,
                longitude=longitude_dec,
            )
            report.full_clean()
            report.save()
            if tags:
                report.tags.set(tags)
            ReportService._attach_files(report, attachments_list)

            StatusHistory.objects.create(
                report=report,
                previous_status=ReportStatus.ABERTO,
                new_status=ReportStatus.ABERTO,
                changed_by=default_employee,
                notes="Atribuicao inicial",
            )
        return report

    @classmethod
    def transition_status(
        cls,
        report_id: int,
        new_status: str,
        *,
        employee: Employee | None = None,
        administrator: Employee | None = None,
        notes: str = "",
        denied_reason: str | None = None,
    ) -> StatusTransitionResult:
        if new_status not in ReportStatus.values:
            raise InvalidStatusTransition("Status de destino invalido.")
        actor = administrator or employee
        if actor is None:
            raise InvalidStatusTransition("Responsavel pela mudanca nao informado.")

        with transaction.atomic():
            report = (
                Report.objects.select_for_update()
                .select_related("category", "department")
                .get(pk=report_id)
            )
            allowed_targets = cls.ALLOWED_TRANSITIONS.get(report.status, set())
            if new_status not in allowed_targets:
                raise InvalidStatusTransition("Transicao nao permitida para o status informado.")

            if new_status == ReportStatus.INDEFERIDO and not denied_reason:
                raise InvalidStatusTransition("Motivo e obrigatorio para indeferir.")

            now = timezone.now()
            previous_status = report.status
            report.status = new_status
            report.last_status_at = now
            if new_status == ReportStatus.INDEFERIDO:
                report.denied_reason = denied_reason or ""
            elif report.denied_reason and new_status != ReportStatus.INDEFERIDO:
                report.denied_reason = ""
            report.full_clean()
            report._skip_auto_history = True
            report.save(update_fields=["status", "last_status_at", "denied_reason"])

            history = StatusHistory.objects.create(
                report=report,
                previous_status=previous_status,
                new_status=new_status,
                changed_by=actor,
                notes=notes,
            )
        return StatusTransitionResult(report=report, history=history)

    @staticmethod
    def get_reports_eligible_for_ignore(hours: int):
        return report_repository.get_reports_eligible_for_ignore(hours)

    @staticmethod
    def get_average_resolution_time_by_category():
        return report_repository.get_average_resolution_time_by_category()
