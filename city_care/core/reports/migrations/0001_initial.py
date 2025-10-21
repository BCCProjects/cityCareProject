from __future__ import annotations

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class ConditionalRunSQL(migrations.RunSQL):
    """Run SQL only for a specific vendor to keep SQLite migrations green."""

    def __init__(self, sql, reverse_sql=None, *, vendor=None, **kwargs):
        self.vendor = vendor
        super().__init__(sql, reverse_sql, **kwargs)

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        if self.vendor and schema_editor.connection.vendor != self.vendor:
            return
        super().database_forwards(app_label, schema_editor, from_state, to_state)

    def database_backwards(self, app_label, schema_editor, from_state, to_state):
        if self.vendor and schema_editor.connection.vendor != self.vendor:
            return
        super().database_backwards(app_label, schema_editor, from_state, to_state)


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Department",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, unique=True)),
                ("description", models.TextField(blank=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Category",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120, unique=True)),
                ("description", models.TextField(blank=True)),
                (
                    "department",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="categories", to="reports.department"),
                ),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Tag",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=80, unique=True)),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Report",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=120)),
                ("description", models.TextField()),
                (
                    "priority",
                    models.CharField(
                        choices=[("BAIXA", "Baixa"), ("MEDIA", "Média"), ("ALTA", "Alta")],
                        default="MEDIA",
                        max_length=12,
                    ),
                ),
                ("address", models.CharField(max_length=255)),
                ("neighborhood", models.CharField(max_length=120)),
                ("latitude", models.DecimalField(decimal_places=6, max_digits=9)),
                ("longitude", models.DecimalField(decimal_places=6, max_digits=9)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("ABERTO", "Aberto"),
                            ("ANALISANDO", "Analisando"),
                            ("DEFERIDO", "Deferido"),
                            ("INDEFERIDO", "Indeferido"),
                            ("EM_ANDAMENTO", "Em andamento"),
                            ("CONCLUIDO", "Concluído"),
                            ("IGNORADO", "Ignorado"),
                        ],
                        default="ABERTO",
                        max_length=20,
                    ),
                ),
                ("indeferment_reason", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("last_status_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("due_at", models.DateTimeField(blank=True, null=True)),
                (
                    "category",
                    models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="reports", to="reports.category"),
                ),
                (
                    "citizen",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="reports", to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={
                "ordering": ["-created_at"],
                "constraints": [
                    models.CheckConstraint(check=models.Q(priority__in=["BAIXA", "MEDIA", "ALTA"]), name="report_priority_valid"),
                    models.CheckConstraint(
                        check=models.Q(status__in=[
                            "ABERTO",
                            "ANALISANDO",
                            "DEFERIDO",
                            "INDEFERIDO",
                            "EM_ANDAMENTO",
                            "CONCLUIDO",
                            "IGNORADO",
                        ]),
                        name="report_status_valid",
                    ),
                    models.CheckConstraint(check=models.Q(latitude__gte=-90) & models.Q(latitude__lte=90), name="report_latitude_range"),
                    models.CheckConstraint(
                        check=models.Q(longitude__gte=-180) & models.Q(longitude__lte=180),
                        name="report_longitude_range",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="Attachment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("file", models.FileField(upload_to="attachments/")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "report",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attachments", to="reports.report"),
                ),
            ],
            options={"ordering": ["created_at"]},
        ),
        migrations.CreateModel(
            name="Comment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("content", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "author",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="report_comments", to=settings.AUTH_USER_MODEL),
                ),
                (
                    "report",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="comments", to="reports.report"),
                ),
            ],
            options={"ordering": ["created_at"]},
        ),
        migrations.CreateModel(
            name="StatusHistory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "from_status",
                    models.CharField(
                        choices=[
                            ("ABERTO", "Aberto"),
                            ("ANALISANDO", "Analisando"),
                            ("DEFERIDO", "Deferido"),
                            ("INDEFERIDO", "Indeferido"),
                            ("EM_ANDAMENTO", "Em andamento"),
                            ("CONCLUIDO", "Concluído"),
                            ("IGNORADO", "Ignorado"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "to_status",
                    models.CharField(
                        choices=[
                            ("ABERTO", "Aberto"),
                            ("ANALISANDO", "Analisando"),
                            ("DEFERIDO", "Deferido"),
                            ("INDEFERIDO", "Indeferido"),
                            ("EM_ANDAMENTO", "Em andamento"),
                            ("CONCLUIDO", "Concluído"),
                            ("IGNORADO", "Ignorado"),
                        ],
                        max_length=20,
                    ),
                ),
                ("reason", models.TextField(blank=True)),
                ("changed_at", models.DateTimeField(auto_now_add=True)),
                (
                    "changed_by",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
                ),
                (
                    "report",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="status_history", to="reports.report"),
                ),
            ],
            options={"ordering": ["-changed_at"]},
        ),
        migrations.CreateModel(
            name="ReportTag",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "report",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="reports.report"),
                ),
                (
                    "tag",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to="reports.tag"),
                ),
            ],
        ),
        migrations.AddField(
            model_name="report",
            name="tags",
            field=models.ManyToManyField(related_name="reports", through="reports.ReportTag", to="reports.tag"),
        ),
        migrations.AddConstraint(
            model_name="reporttag",
            constraint=models.UniqueConstraint(fields=("report", "tag"), name="unique_report_tag"),
        ),
        ConditionalRunSQL(
            sql="""
            CREATE FUNCTION sla_hours_remaining(due_at DATETIME)
            RETURNS INT DETERMINISTIC
            BEGIN
                IF due_at IS NULL THEN
                    RETURN NULL;
                END IF;
                RETURN TIMESTAMPDIFF(HOUR, NOW(), due_at);
            END;
            """,
            reverse_sql="DROP FUNCTION IF EXISTS sla_hours_remaining;",
            vendor="mysql",
        ),
        migrations.RunSQL(
            sql="""
            CREATE VIEW report_status_dashboard AS
            SELECT r.status AS status,
                   c.name AS category_name,
                   COUNT(*) AS total
            FROM core_reports_report AS r
            INNER JOIN core_reports_category AS c ON c.id = r.category_id
            GROUP BY r.status, c.name;
            """,
            reverse_sql="DROP VIEW IF EXISTS report_status_dashboard;",
        ),
    ]
