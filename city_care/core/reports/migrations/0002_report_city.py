from __future__ import annotations

from django.db import migrations, models


def copy_city_from_organization(apps, schema_editor):
    Report = apps.get_model("core_reports", "Report")
    for report in Report.objects.select_related("organization__city").all():
        if report.organization_id and report.organization.city_id and not report.city_id:
            report.city_id = report.organization.city_id
            report.save(update_fields=["city"])


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0001_initial"),
        ("core_reports", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="report",
            name="city",
            field=models.ForeignKey(
                null=True,
                on_delete=models.deletion.PROTECT,
                related_name="reports",
                to="accounts.city",
            ),
        ),
        migrations.RunPython(copy_city_from_organization, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="report",
            name="city",
            field=models.ForeignKey(
                on_delete=models.deletion.PROTECT,
                related_name="reports",
                to="accounts.city",
            ),
        ),
    ]
