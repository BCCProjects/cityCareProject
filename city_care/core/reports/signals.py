from __future__ import annotations

from django.db.models.signals import post_save
from django.dispatch import receiver

from core.realtime.publisher import emit_report_created, emit_report_status_changed
from core.reports.models import Report, ReportStatus, StatusHistory


@receiver(post_save, sender=Report)
def notify_report_created(sender, instance: Report, created: bool, **kwargs):
    if created:
        emit_report_created(instance)


@receiver(post_save, sender=StatusHistory)
def notify_status_history_saved(sender, instance: StatusHistory, created: bool, **kwargs):
    report = Report.objects.only("status").get(pk=instance.report_id)
    status_will_change = report.status != instance.new_status
    _sync_status_from_history(instance)
    instance.report.refresh_from_db(fields=["status", "last_status_at", "denied_reason"])
    if created or status_will_change:
        emit_report_status_changed(instance.report, instance)


def _sync_status_from_history(history: StatusHistory) -> None:
    update_kwargs = {
        "status": history.new_status,
        "last_status_at": history.created_at,
    }
    if history.new_status == ReportStatus.INDEFERIDO:
        update_kwargs["denied_reason"] = history.notes or ""
    else:
        update_kwargs["denied_reason"] = ""

    Report.objects.filter(pk=history.report_id).update(**update_kwargs)
