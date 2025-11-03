from __future__ import annotations

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import Employee
from core.reports.models import Report, ReportStatus, StatusHistory


class Command(BaseCommand):
    help = (
        "Marca como IGNORADO os relatorios sem atualizacao ha N horas "
        "e registra historico de status."
    )

    def add_arguments(self, parser):  # type: ignore[override]
        parser.add_argument(
            "--hours",
            type=int,
            default=72,
            help="Janela de inatividade em horas (padrao: 72h).",
        )

    def handle(self, *args, **options):  # type: ignore[override]
        hours: int = options.get("hours", 72)
        if hours <= 0:
            self.stderr.write(self.style.ERROR("--hours deve ser positivo."))
            return

        cutoff = timezone.now() - timedelta(hours=hours)
        eligible_status = [
            ReportStatus.ABERTO,
            ReportStatus.ANALISANDO,
            ReportStatus.DEFERIDO,
            ReportStatus.EM_ANDAMENTO,
        ]

        qs = (
            Report.objects.select_for_update()
            .filter(status__in=eligible_status, last_status_at__lte=cutoff)
            .only("id", "status", "last_status_at")
        )

        count = 0
        now = timezone.now()
        employee = Employee.objects.order_by("id").first()

        with transaction.atomic():
            for report in qs.iterator(chunk_size=200):
                previous = report.status
                report.status = ReportStatus.IGNORADO
                report.last_status_at = now
                report.save(update_fields=["status", "last_status_at"])

                StatusHistory.objects.create(
                    report=report,
                    previous_status=previous,
                    new_status=ReportStatus.IGNORADO,
                    changed_by=employee,
                    notes=f"Marcado automaticamente como IGNORADO apos {hours}h sem atualizacao.",
                )
                count += 1

        self.stdout.write(self.style.SUCCESS(f"Relatorios marcados como IGNORADO: {count}"))
