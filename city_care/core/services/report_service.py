from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

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
            if Report.objects.filter(category=category, latitude=latitude, longitude=longitude).exists():
                raise ValidationError({
                    "non_field_errors": [
                        "Ja existe uma ocorrencia para esta categoria neste mesmo ponto (lat/lng).",
                    ]
                })

            try:
                resolved_city = resolve_city_from_coordinates(latitude, longitude)
            except CityNotCoveredError as exc:
                raise ValidationError({"location": str(exc)}) from exc
            except LocationResolutionError as exc:
                raise ValidationError({"location": str(exc)}) from exc

            organization = getattr(resolved_city, "organization", None)
            if organization is None:
                raise ValidationError({"organization": "Nenhuma organizacao vinculada a cidade identificada."})

            default_employee = organization.employees.order_by("id").first()

            attachments_list = list(attachments or [])
            effective_priority = priority
            if not attachments_list:
                effective_priority = ReportPriority.LOW

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
                latitude=latitude,
                longitude=longitude,
            )
            report.full_clean()
            report.save()
            if tags:
                report.tags.set(tags)
            for attachment in attachments_list:
                report.attachments.create(file=attachment, description=getattr(attachment, "description", ""))

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
        employee: Employee,
        notes: str = "",
        denied_reason: str | None = None,
    ) -> StatusTransitionResult:
        if new_status not in ReportStatus.values:
            raise InvalidStatusTransition("Status de destino invalido.")

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
                changed_by=employee,
                notes=notes,
            )
        return StatusTransitionResult(report=report, history=history)

    @staticmethod
    def get_reports_eligible_for_ignore(hours: int):
        return report_repository.get_reports_eligible_for_ignore(hours)

    @staticmethod
    def get_average_resolution_time_by_category():
        return report_repository.get_average_resolution_time_by_category()
