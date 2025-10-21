from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Optional

from django.db import transaction
from django.utils import timezone

from core.reports.models import Report, StatusHistory


class InvalidStatusTransition(Exception):
    """Raised when an invalid status transition is requested."""


class MissingIndefermentReason(Exception):
    """Raised when a reason is required but not supplied."""


class IgnoreEligibilityError(Exception):
    """Raised when attempting to ignore a report that is not eligible."""


@dataclass(frozen=True)
class TransitionRule:
    current: str
    allowed: Iterable[str]


class ReportStatusService:
    """Transactional service coordinating status transitions and audit trail."""

    transition_rules: Mapping[str, TransitionRule] = {
        Report.Status.OPEN: TransitionRule(Report.Status.OPEN, [Report.Status.ANALYZING]),
        Report.Status.ANALYZING: TransitionRule(
            Report.Status.ANALYZING,
            [Report.Status.APPROVED, Report.Status.REJECTED],
        ),
        Report.Status.APPROVED: TransitionRule(
            Report.Status.APPROVED,
            [Report.Status.IN_PROGRESS, Report.Status.COMPLETED],
        ),
        Report.Status.IN_PROGRESS: TransitionRule(
            Report.Status.IN_PROGRESS,
            [Report.Status.COMPLETED],
        ),
        Report.Status.REJECTED: TransitionRule(Report.Status.REJECTED, []),
        Report.Status.COMPLETED: TransitionRule(Report.Status.COMPLETED, []),
        Report.Status.IGNORED: TransitionRule(Report.Status.IGNORED, []),
    }

    def __init__(self, *, user) -> None:
        self.user = user

    def transition(self, report_id: int, new_status: str, *, reason: Optional[str] = None) -> Report:
        with transaction.atomic():
            report = Report.objects.select_for_update().get(pk=report_id)
            old_status = report.status

            allowed_statuses = self.transition_rules.get(old_status, TransitionRule(old_status, [])).allowed
            if new_status not in allowed_statuses:
                if not (new_status == Report.Status.IGNORED and report.is_eligible_for_ignore()):
                    raise InvalidStatusTransition(f"Cannot transition from {old_status} to {new_status}.")

            if new_status == Report.Status.REJECTED and not reason:
                raise MissingIndefermentReason("Rejeições exigem o preenchimento de um motivo.")

            if new_status == Report.Status.IGNORED and not report.is_eligible_for_ignore():
                raise IgnoreEligibilityError("Ocorrência ainda não completou o prazo para ser ignorada.")

            indeferment_reason = reason if new_status == Report.Status.REJECTED else ""

            report.status = new_status
            report.indeferment_reason = indeferment_reason
            report.last_status_at = timezone.now()
            report.save(update_fields=["status", "indeferment_reason", "last_status_at", "updated_at"])

            StatusHistory.objects.create(
                report=report,
                from_status=old_status,
                to_status=new_status,
                reason=reason or "",
                changed_by=self.user,
            )

            return report
