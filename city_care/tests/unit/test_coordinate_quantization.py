from decimal import Decimal

from core.services.report_service import ReportService


def test_quantize_coordinate_decimal():
    value = ReportService._quantize_coordinate(Decimal("1.23456789"))
    assert isinstance(value, Decimal)
    assert str(value) == "1.234568"


def test_quantize_coordinate_float():
    value = ReportService._quantize_coordinate(3.1415926535)
    assert str(value) == "3.141593"


def test_quantize_coordinate_string():
    value = ReportService._quantize_coordinate("9.87654321")
    assert str(value) == "9.876543"


def test_quantize_coordinate_precision_matches():
    a = ReportService._quantize_coordinate("1.0000004")
    b = ReportService._quantize_coordinate("1.0000005")
    assert str(a) == "1.000000"
    assert str(b) == "1.000001"
