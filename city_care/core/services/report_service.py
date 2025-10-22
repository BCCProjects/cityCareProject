from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from django.db import transaction
from django.utils import timezone

from accounts.models import Administrator, Citizen
from core.repositories import report_repository
from core.reports.models import Report, ReportStatus, StatusHistory, Tag


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
            report = Report(
                citizen=citizen,
                category=category,
                department=department,
                title=title,
                description=description,
                priority=priority,
                address=address,
                neighborhood=neighborhood,
                latitude=latitude,
                longitude=longitude,
            )
            report.full_clean()
            report.save()
            if tags:
                report.tags.set(tags)
            for attachment in attachments or []:
                report.attachments.create(file=attachment, description=getattr(attachment, "description", ""))
        return report

    @classmethod
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

        with transaction.atomic():
            report = (
                Report.objects.select_for_update()
                .select_related("category", "department")
                .get(pk=report_id)
            )
            allowed_targets = cls.ALLOWED_TRANSITIONS.get(report.status, set())
            if new_status not in allowed_targets:
                raise InvalidStatusTransition("Transição não permitida para o status informado.")

            if new_status == ReportStatus.INDEFERIDO and not denied_reason:
                raise InvalidStatusTransition("Motivo é obrigatório para indeferir.")

            now = timezone.now()
            previous_status = report.status
            report.status = new_status
            report.last_status_at = now
            if new_status == ReportStatus.INDEFERIDO:
                report.denied_reason = denied_reason or ""
            elif report.denied_reason and new_status != ReportStatus.INDEFERIDO:
                report.denied_reason = ""
            report.full_clean()
            report.save(update_fields=["status", "last_status_at", "denied_reason"])

            history = StatusHistory.objects.create(
                report=report,
                previous_status=previous_status,
                new_status=new_status,
                changed_by=administrator,
                notes=notes,
            )
        return StatusTransitionResult(report=report, history=history)

    @staticmethod
    def get_reports_eligible_for_ignore(hours: int):
        return report_repository.get_reports_eligible_for_ignore(hours)

    @staticmethod
    def get_average_resolution_time_by_category():
        return report_repository.get_average_resolution_time_by_category()
