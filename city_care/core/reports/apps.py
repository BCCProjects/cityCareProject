from django.apps import AppConfig


class ReportsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "core.reports"
    verbose_name = "Relatórios"

    def ready(self) -> None:  # pragma: no cover
        try:
            import core.reports.signals  # noqa: F401
        except Exception:
            pass
