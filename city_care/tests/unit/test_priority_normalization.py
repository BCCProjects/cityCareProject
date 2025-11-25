from core.reports.models import ReportPriority


def test_report_priority_choices_values():
    values = {choice.value for choice in ReportPriority}
    assert values == {"BAIXO", "MODERADO", "ALTO"}


def test_report_priority_labels():
    labels = {choice.label for choice in ReportPriority}
    assert labels == {"Baixo", "Moderado", "Alto"}

