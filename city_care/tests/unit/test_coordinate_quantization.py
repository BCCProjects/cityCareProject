from decimal import Decimal

from core.reports.models import Report


def test_report_latitude_field_precision():
    field = Report._meta.get_field("latitude")
    assert field.max_digits == 9
    assert field.decimal_places == 6


def test_report_longitude_field_precision():
    field = Report._meta.get_field("longitude")
    assert field.max_digits == 9
    assert field.decimal_places == 6

