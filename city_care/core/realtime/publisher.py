from __future__ import annotations

from typing import Iterable

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from core.reports.models import Report, StatusHistory


def emit_report_created(report: Report) -> None:
    _broadcast(
        report,
        {
            "type": "report.created",
            "report": _serialize_report(report),
        },
    )


def emit_report_status_changed(report: Report, history: StatusHistory) -> None:
    payload = _serialize_report(report)
    payload.update(
        {
            "previous_status": history.previous_status,
            "new_status": history.new_status,
            "history_id": history.id,
            "history_created_at": history.created_at.isoformat(),
        }
    )
    _broadcast(
        report,
        {
            "type": "report.status_changed",
            "report": payload,
        },
    )


def _broadcast(report: Report, message: dict) -> None:
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    for group in _groups_for_report(report):
        async_to_sync(channel_layer.group_send)(
            group,
            {
                "type": "report.event",
                "data": message,
            },
        )


def _groups_for_report(report: Report) -> Iterable[str]:
    if report.citizen_id:
        yield f"citizen_{report.citizen_id}"
    if report.organization_id:
        yield f"organization_{report.organization_id}"


def _serialize_report(report: Report) -> dict:
    return {
        "id": report.id,
        "title": report.title,
        "status": report.status,
        "priority": report.priority,
        "citizen_id": report.citizen_id,
        "organization_id": report.organization_id,
        "category_id": report.category_id,
        "department_id": report.department_id,
        "created_at": report.created_at.isoformat() if report.created_at else None,
        "last_status_at": report.last_status_at.isoformat() if report.last_status_at else None,
    }

