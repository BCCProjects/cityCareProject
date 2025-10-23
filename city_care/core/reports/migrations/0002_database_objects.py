from __future__ import annotations

from django.db import migrations


def create_function(apps, schema_editor):
    if schema_editor.connection.vendor != "mysql":
        return
    schema_editor.execute(
        """
        CREATE FUNCTION IF NOT EXISTS calculate_sla_hours(due_at DATETIME)
        RETURNS INT
        DETERMINISTIC
        BEGIN
            RETURN TIMESTAMPDIFF(HOUR, UTC_TIMESTAMP(), due_at);
        END;
        """
    )


def drop_function(apps, schema_editor):
    if schema_editor.connection.vendor != "mysql":
        return
    schema_editor.execute("DROP FUNCTION IF EXISTS calculate_sla_hours;")


class Migration(migrations.Migration):
    dependencies = [
        ("core_reports", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_function, drop_function),
        migrations.RunSQL(
            sql="""
            CREATE VIEW IF NOT EXISTS report_status_overview AS
            SELECT
                c.id AS category_id,
                c.name AS category_name,
                r.status,
                COUNT(r.id) AS total
            FROM core_reports_report r
            INNER JOIN core_reports_category c ON c.id = r.category_id
            GROUP BY c.id, c.name, r.status;
            """,
            reverse_sql="DROP VIEW IF EXISTS report_status_overview;",
        ),
    ]
