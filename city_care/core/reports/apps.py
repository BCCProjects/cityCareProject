from django.apps import AppConfig


class ReportsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core.reports"
    label = "core_reports"
    verbose_name = "Relatórios"

    def ready(self) -> None:
        try:
            import core.reports.signals
        except Exception:
            pass

