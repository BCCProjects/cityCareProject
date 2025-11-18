from core.reports.models import ReportPriority
from core.services.report_service import ReportService


def test_normalize_priority_low_variants():
    for value in ["baixa", "baixo", "baixas", "BAIXO"]:
        assert ReportService.normalize_priority(value) == ReportPriority.LOW


def test_normalize_priority_medium_variants():
    for value in ["media", "média", "medias", "médias"]:
        assert ReportService.normalize_priority(value) == ReportPriority.MEDIUM


def test_normalize_priority_high_variants():
    for value in ["alta", "alto", "altas"]:
        assert ReportService.normalize_priority(value) == ReportPriority.HIGH
