from __future__ import annotations

import pytest
from django.contrib.auth.hashers import make_password
from django.utils import timezone

from accounts.models import Employee, Citizen
from core.reports.models import Category, Department, Report, ReportStatus
from core.services.report_service import InvalidStatusTransition, ReportService
from tests.utils import ensure_location

Administrator = Employee


@pytest.fixture
def setup_data(db):
    _, city, organization = ensure_location("Transition City")
    citizen = Citizen.objects.create(
        email="citizen@test.com",
        first_name="User",
        last_name="Test",
        phone="123",
        password=make_password("123456"),
        city=city,
    )

    admin = Administrator.objects.create(
        email="admin@test.com",
        first_name="Admin",
        password=make_password("123456"),
        organization=organization,
    )

    dep = Department.objects.create(name="Infra", email="i@test.com", phone="123")
    cat = Category.objects.create(name="Buraco", slug="buraco", department=dep)

    report = Report.objects.create(
        citizen=citizen,
        category=cat,
        department=dep,
        city=city,
        organization=organization,
        title="Buraco grande",
        description="Existe um buraco enorme na rua.",
        address="Rua A",
        neighborhood="Centro",
        latitude=1,
        longitude=1,
        status=ReportStatus.ABERTO,
        last_status_at=timezone.now(),
    )

    return citizen, admin, dep, cat, report


def test_transition_invalid_status(db, setup_data):
    _, admin, _, _, report = setup_data

    with pytest.raises(InvalidStatusTransition):
        ReportService.transition_status(report.id, "STATUS_QUE_NAO_EXISTE", employee=admin)


def test_transition_not_allowed(db, setup_data):
    _, admin, _, _, report = setup_data

    with pytest.raises(InvalidStatusTransition):
        ReportService.transition_status(report.id, ReportStatus.CONCLUIDO, employee=admin)


def test_transition_indeferido_without_reason(db, setup_data):
    _, admin, _, _, report = setup_data

    with pytest.raises(InvalidStatusTransition):
        ReportService.transition_status(report.id, ReportStatus.INDEFERIDO, employee=admin)


def test_transition_valid(db, setup_data):
    _, admin, _, _, report = setup_data

    result = ReportService.transition_status(
        report.id,
        ReportStatus.ANALISANDO,
        employee=admin,
        notes="Iniciando analise",
    )

    assert result.report.status == ReportStatus.ANALISANDO
    assert result.history.new_status == ReportStatus.ANALISANDO
    assert result.history.previous_status == ReportStatus.ABERTO
    assert result.history.changed_by == admin
    assert result.report.last_status_at is not None

