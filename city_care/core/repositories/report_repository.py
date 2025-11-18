from __future__ import annotations

from django.db import connection, models
from django.db.models.functions import TruncWeek
from django.db.models import Count

from core.reports.models import Report, ReportStatus


# ------------------------------------------------------------
# Helper interno (não mexer)
# ------------------------------------------------------------
def _dictfetchall(cursor):
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


# ------------------------------------------------------------
# Classe oficial usada por ReportService.list_reports_ignore
# E também referenciada indiretamente pelos testes
# ------------------------------------------------------------
class ReportRepository:
    """
    Repositório oficial esperado pelos testes.
    Todas as funções são métodos estáticos dentro de uma classe.
    """

    @staticmethod
    def get_reports_eligible_for_ignore(hours: int):
        if hours <= 0:
            raise ValueError("Horas deve ser positivo.")

        allowed_status = [
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
            # SQLite (testes usam sqlite!)
            sql = """
                SELECT r.id, r.title, r.status, r.last_status_at
                FROM core_reports_report r
                WHERE r.status IN (%s, %s, %s, %s)
                  AND ((julianday('now') - julianday(r.last_status_at)) * 24) >= %s
                ORDER BY r.last_status_at ASC
            """

        with connection.cursor() as cursor:
            cursor.execute(sql, [*allowed_status, hours])
            return _dictfetchall(cursor)

    @staticmethod
    def get_average_resolution_time_by_category():
        vendor = connection.vendor
        concluded = ReportStatus.CONCLUIDO

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
        else:
            # SQLite
            sql = """
                SELECT c.name AS category_name,
                       AVG((julianday(r.last_status_at) - julianday(r.created_at)) * 24) AS average_hours
                FROM core_reports_report r
                INNER JOIN core_reports_category c ON c.id = r.category_id
                WHERE r.status = %s
                GROUP BY c.name
                ORDER BY average_hours ASC
            """

        with connection.cursor() as cursor:
            cursor.execute(sql, [concluded])
            return _dictfetchall(cursor)

    @staticmethod
    def get_open_reports_grouped_by_neighborhood():
        queryset = (
            Report.objects.filter(status=ReportStatus.ABERTO)
            .values("neighborhood", "priority")
            .annotate(total=models.Count("id"))
            .order_by("neighborhood")
        )
        return list(queryset)



    @staticmethod
    def get_weekly_series_by_status():
        qs = (
            Report.objects.all()
            .annotate(week=TruncWeek("created_at"))
            .values("week", "status")
            .annotate(total=Count("id"))
            .order_by("week", "status")
        )
        return list(qs)


# ------------------------------------------------------------
# WRAPPERS NECESSÁRIOS PARA PASSAR NOS TESTES
# Os testes chamam repo.<função>, não ReportRepository.<função>
# ------------------------------------------------------------
def get_reports_eligible_for_ignore(hours: int):
    return ReportRepository.get_reports_eligible_for_ignore(hours)


def get_average_resolution_time_by_category():
    return ReportRepository.get_average_resolution_time_by_category()


def get_open_reports_grouped_by_neighborhood():
    return ReportRepository.get_open_reports_grouped_by_neighborhood()


def get_weekly_series_by_status():
    return ReportRepository.get_weekly_series_by_status()
