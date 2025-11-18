import pytest
from core.services.report_service import ReportService, ReportPriority

def test_normalize_priority_none():
    assert ReportService.normalize_priority(None) is None

def test_normalize_priority_strip_upper():
    assert ReportService.normalize_priority("  alta  ") == ReportPriority.HIGH

def test_normalize_priority_synonyms_low():
    assert ReportService.normalize_priority("baixa") == ReportPriority.LOW
    assert ReportService.normalize_priority("BAIXAS") == ReportPriority.LOW

def test_normalize_priority_synonyms_medium():
    assert ReportService.normalize_priority("media") == ReportPriority.MEDIUM
    assert ReportService.normalize_priority("médias") == ReportPriority.MEDIUM

def test_normalize_priority_synonyms_high():
    assert ReportService.normalize_priority("alta") == ReportPriority.HIGH
    assert ReportService.normalize_priority("ALTAS") == ReportPriority.HIGH

def test_normalize_priority_unknown_returns_uppercase():
    assert ReportService.normalize_priority("super") == "SUPER"
