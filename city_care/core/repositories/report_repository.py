from __future__ import annotations

from django.db import connection, models

from core.reports.models import ReportStatus


def _dictfetchall(cursor):
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def get_reports_eligible_for_ignore(hours: int):
    if hours <= 0:
        raise ValueError("Horas deve ser positivo.")

    status_filter = [
        ReportStatus.ABERTO,
        ReportStatus.ANALISANDO,
        ReportStatus.DEFERIDO,
        ReportStatus.EM_ANDAMENTO,
    ]
    vendor = connection.vendor
    if vendor == "mysql":
        sql = """
            SELECT r.id, r.title, r.status, r.last_status_at
            FROM core_reports_report r
            WHERE r.status IN (%s, %s, %s, %s)
              AND TIMESTAMPDIFF(HOUR, r.last_status_at, UTC_TIMESTAMP()) >= %s
            ORDER BY r.last_status_at ASC
        """
    else:
        sql = """
            SELECT r.id, r.title, r.status, r.last_status_at
            FROM core_reports_report r
            WHERE r.status IN (%s, %s, %s, %s)
              AND ((julianday('now') - julianday(r.last_status_at)) * 24) >= %s
            ORDER BY r.last_status_at ASC
        """
    with connection.cursor() as cursor:
        cursor.execute(sql, [*status_filter, hours])
        return _dictfetchall(cursor)


def get_average_resolution_time_by_category():
    vendor = connection.vendor
    concluded_status = ReportStatus.CONCLUIDO
    if vendor == "mysql":
        sql = """
            SELECT c.name AS category_name,
                   AVG(TIMESTAMPDIFF(HOUR, r.created_at, r.last_status_at)) AS average_hours
            FROM core_reports_report r
            INNER JOIN core_reports_category c ON c.id = r.category_id
            WHERE r.status = %s
            GROUP BY c.name
            ORDER BY average_hours ASC
        """
        params = [concluded_status]
    else:
        sql = """
            SELECT c.name AS category_name,
                   AVG((julianday(r.last_status_at) - julianday(r.created_at)) * 24) AS average_hours
            FROM core_reports_report r
            INNER JOIN core_reports_category c ON c.id = r.category_id
            WHERE r.status = %s
            GROUP BY c.name
            ORDER BY average_hours ASC
        """
        params = [concluded_status]

    with connection.cursor() as cursor:
        cursor.execute(sql, params)
        return _dictfetchall(cursor)


def get_open_reports_grouped_by_neighborhood():
    from core.reports.models import Report

    queryset = (
        Report.objects.filter(status=ReportStatus.ABERTO)
        .values("neighborhood", "priority")
        .order_by("neighborhood")
        .annotate(total=models.Count("id"))
    )
    return list(queryset)


def get_weekly_series_by_status():
    from django.db.models import Count
    from django.db.models.functions import TruncWeek
    from core.reports.models import Report

    queryset = (
        Report.objects.all()
        .annotate(week=TruncWeek("created_at"))
        .values("week", "status")
        .order_by("week")
        .annotate(total=Count("id"))
    )
    return list(queryset)
