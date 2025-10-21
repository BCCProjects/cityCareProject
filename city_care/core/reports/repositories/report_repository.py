from __future__ import annotations

from typing import Any, Dict, Iterable, List

from django.db import connection
from django.db.models import Count, F
from django.db.models.functions import TruncWeek

from core.reports.models import Report


class ReportRepository:
    """Data access helpers that showcase parametrised raw SQL queries."""

    @staticmethod
    def _dictfetchall(cursor) -> List[Dict[str, Any]]:
        columns = [col[0] for col in cursor.description]
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_reports_eligible_for_ignore(self, hours: int) -> List[Dict[str, Any]]:
        if connection.vendor == "mysql":
            query = """
                SELECT r.id, r.title, r.status, r.last_status_at, r.category_id
                FROM core_reports_report AS r
                WHERE r.status NOT IN (%s, %s)
                  AND TIMESTAMPDIFF(HOUR, r.last_status_at, NOW()) >= %s
                ORDER BY r.last_status_at ASC
            """
            params = [Report.Status.IGNORED, Report.Status.COMPLETED, hours]
        else:
            query = """
                SELECT r.id, r.title, r.status, r.last_status_at, r.category_id
                FROM core_reports_report AS r
                WHERE r.status NOT IN (%s, %s)
                  AND ((julianday('now') - julianday(r.last_status_at)) * 24) >= %s
                ORDER BY r.last_status_at ASC
            """
            params = [Report.Status.IGNORED, Report.Status.COMPLETED, hours]
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            return self._dictfetchall(cursor)

    def get_average_resolution_time_by_category(self) -> List[Dict[str, Any]]:
        if connection.vendor == "mysql":
            query = """
                SELECT c.id AS category_id,
                       c.name AS category_name,
                       AVG(TIMESTAMPDIFF(HOUR, r.created_at, r.updated_at)) AS avg_resolution_hours
                FROM core_reports_report AS r
                INNER JOIN core_reports_category AS c ON c.id = r.category_id
                WHERE r.status = %s
                GROUP BY c.id, c.name
                ORDER BY avg_resolution_hours ASC
            """
        else:
            query = """
                SELECT c.id AS category_id,
                       c.name AS category_name,
                       AVG((julianday(r.updated_at) - julianday(r.created_at)) * 24) AS avg_resolution_hours
                FROM core_reports_report AS r
                INNER JOIN core_reports_category AS c ON c.id = r.category_id
                WHERE r.status = %s
                GROUP BY c.id, c.name
                ORDER BY avg_resolution_hours ASC
            """
        params = [Report.Status.COMPLETED]
        with connection.cursor() as cursor:
            cursor.execute(query, params)
            return self._dictfetchall(cursor)

    def get_open_reports_by_neighborhood_and_priority(self) -> Iterable[Dict[str, Any]]:
        queryset = (
            Report.objects.filter(status=Report.Status.OPEN)
            .values("neighborhood", "priority")
            .annotate(total=Count("id"))
            .order_by("neighborhood", "priority")
        )
        return list(queryset)

    def get_weekly_status_series(self) -> Iterable[Dict[str, Any]]:
        queryset = (
            Report.objects.all()
            .annotate(week=TruncWeek("created_at"))
            .values("week", status=F("status"))
            .annotate(total=Count("id"))
            .order_by("week", "status")
        )
        return list(queryset)
