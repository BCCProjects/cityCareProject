from __future__ import annotations

from django.db import migrations


def create_mysql_objects(apps, schema_editor):
    """
    Create MySQL-specific helper function and view used by the report repository.

    - fn_report_resolution_hours: calculates resolution time in hours.
    - vw_weekly_reports_by_status: aggregates reports per ISO week and status.
    """
    if schema_editor.connection.vendor != "mysql":
        return

    with schema_editor.connection.cursor() as cursor:
        cursor.execute("DROP FUNCTION IF EXISTS fn_report_resolution_hours;")
        cursor.execute(
            """
            CREATE FUNCTION fn_report_resolution_hours(created_at DATETIME, last_status_at DATETIME)
            RETURNS INT
            DETERMINISTIC
            RETURN TIMESTAMPDIFF(HOUR, created_at, last_status_at);
            """
        )

        cursor.execute("DROP VIEW IF EXISTS vw_weekly_reports_by_status;")
        cursor.execute(
            """
            CREATE VIEW vw_weekly_reports_by_status AS
            SELECT
                YEARWEEK(created_at, 1) AS week,
                status,
                COUNT(*) AS total
            FROM core_reports_report
            GROUP BY YEARWEEK(created_at, 1), status;
            """
        )


def drop_mysql_objects(apps, schema_editor):
    if schema_editor.connection.vendor != "mysql":
        return

    with schema_editor.connection.cursor() as cursor:
        cursor.execute("DROP VIEW IF EXISTS vw_weekly_reports_by_status;")
        cursor.execute("DROP FUNCTION IF EXISTS fn_report_resolution_hours;")


class Migration(migrations.Migration):
    dependencies = [
        ("core_reports", "0002_report_city"),
    ]

    operations = [
        migrations.RunPython(create_mysql_objects, drop_mysql_objects),
    ]
