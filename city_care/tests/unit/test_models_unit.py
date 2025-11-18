from __future__ import annotations

from decimal import Decimal

from accounts.models import Administrator, Citizen
from core.reports.models import (
    Category,
    Department,
    Report,
    ReportPriority,
    ReportStatus,
    ReportTag,
    Tag,
)


def test_administrator_str_and_defaults():
    admin = Administrator(email="admin@example.com", first_name="Admin")
    assert str(admin) == "admin@example.com"
    assert admin.is_active is True
    assert admin.is_staff is True


def test_citizen_str_and_password_hashing():
    citizen = Citizen(
        email="citizen@example.com",
        full_name="Fernando Lopes",
        phone="11999999999",
        password="pbkdf2_sha256$dummy$hash",
    )
    citizen.set_password("SenhaMuitoSegura123")
    assert citizen.password.startswith("pbkdf2_")
    assert str(citizen) == "Fernando Lopes"


def test_department_and_category_str():
    department = Department(name="Infraestrutura", email="infra@city.gov", phone="11988887777")
    category = Category(name="Buracos", slug="buracos", department=department)
    assert str(department) == "Infraestrutura"
    assert str(category) == "Buracos"


def _make_report(**overrides) -> Report:
    base_kwargs = {
        "citizen_id": 1,
        "category_id": 1,
        "department_id": 1,
        "title": "Problema na via pública",
        "description": "Descrição suficiente para o teste.",
        "address": "Rua Principal, 123",
        "neighborhood": "Centro",
        "latitude": Decimal("1.000000"),
        "longitude": Decimal("1.000000"),
    }
    base_kwargs.update(overrides)
    return Report(**base_kwargs)


def test_report_defaults_without_db():
    report = _make_report()
    assert report.priority == ReportPriority.MEDIUM
    assert report.status == ReportStatus.ABERTO
    assert report.denied_reason == ""
    assert str(report) == "Problema na via pública"


def test_report_priority_can_be_changed_without_db():
    report = _make_report(priority=ReportPriority.HIGH)
    assert report.priority == ReportPriority.HIGH


def test_tag_and_report_tag_str_without_db():
    tag = Tag(name="Poda", slug="poda")
    relation = ReportTag(report_id=10, tag_id=20)
    assert str(tag) == "Poda"
    assert str(relation) == "10-20"
