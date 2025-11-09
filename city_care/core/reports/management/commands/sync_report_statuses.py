from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from core.reports.models import Report, ReportStatus


class Command(BaseCommand):
    help = "Realinha Report.status, last_status_at e denied_reason com o ultimo StatusHistory"

    def handle(self, *args, **options):
        updated = 0
        missing_history = 0

        with transaction.atomic():
            reports = (
                Report.objects.select_related(None)
                .prefetch_related("status_history")
                .order_by("id")
            )
            for report in reports:
                history = report.status_history.order_by("-created_at").first()
                if history is None:
                    missing_history += 1
                    continue
                desired_denied_reason = history.notes if history.new_status == ReportStatus.INDEFERIDO else ""
                if (
                    report.status == history.new_status
                    and report.last_status_at == history.created_at
                    and (report.denied_reason or "") == desired_denied_reason
                ):
                    continue
                report.status = history.new_status
                report.last_status_at = history.created_at
                report.denied_reason = desired_denied_reason
                report.save(update_fields=["status", "last_status_at", "denied_reason"])
                updated += 1

        self.stdout.write(self.style.SUCCESS(f"Reports sincronizados: {updated}"))
        if missing_history:
            self.stdout.write(self.style.WARNING(f"Reports sem StatusHistory: {missing_history}"))
