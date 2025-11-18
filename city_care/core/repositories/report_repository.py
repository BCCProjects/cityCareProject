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
                   AVG(fn_report_resolution_hours(r.created_at, r.last_status_at)) AS average_hours
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


def get_weekly_series_by_status(start_date=None, end_date=None):
    vendor = connection.vendor

    if vendor == "mysql" and not start_date and not end_date:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT week, status, total
                FROM vw_weekly_reports_by_status
                ORDER BY week ASC
                """
            )
            return _dictfetchall(cursor)

    from django.db.models import Count
    from django.db.models.functions import TruncWeek
    from core.reports.models import Report

    queryset = Report.objects.all()
    if start_date:
        queryset = queryset.filter(created_at__date__gte=start_date)
    if end_date:
        queryset = queryset.filter(created_at__date__lte=end_date)

    queryset = (
        queryset.annotate(week=TruncWeek("created_at"))
        .values("week", "status")
        .order_by("week")
        .annotate(total=Count("id"))
    )
    return list(queryset)
