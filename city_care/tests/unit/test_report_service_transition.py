import pytest
from django.utils import timezone
from django.contrib.auth.hashers import make_password

from accounts.models import Administrator, Citizen
from core.reports.models import (
    Report,
    Category,
    Department,
    ReportStatus,
)
from core.services.report_service import ReportService, InvalidStatusTransition


@pytest.fixture
def setup_data(db):
    citizen = Citizen.objects.create(
        email="citizen@test.com",
        full_name="User Test",
        phone="123",
        password=make_password("123456"),
    )

    admin = Administrator.objects.create(
        email="admin@test.com",
        first_name="Admin",
        password=make_password("123456"),
    )

    dep = Department.objects.create(name="Infra", email="i@test.com", phone="123")
    cat = Category.objects.create(name="Buraco", slug="buraco", department=dep)

    report = Report.objects.create(
        citizen=citizen,
        category=cat,
        department=dep,
        title="Buraco grande",
        description="Existe um buraco enorme na rua.",
        address="Rua A",
        neighborhood="Centro",
        latitude=1,
        longitude=1,
        status=ReportStatus.ABERTO,
    )

    return citizen, admin, dep, cat, report


def test_transition_invalid_status(db, setup_data):
    _, admin, _, _, report = setup_data

    with pytest.raises(InvalidStatusTransition):
        ReportService.transition_status(
            report.id,
            "STATUS_QUE_NAO_EXISTE",
            administrator=admin
        )


def test_transition_not_allowed(db, setup_data):
    _, admin, _, _, report = setup_data

    with pytest.raises(InvalidStatusTransition):
        ReportService.transition_status(
            report.id,
            ReportStatus.CONCLUIDO,
            administrator=admin
        )


def test_transition_indeferido_without_reason(db, setup_data):
    _, admin, _, _, report = setup_data

    with pytest.raises(InvalidStatusTransition):
        ReportService.transition_status(
            report.id,
            ReportStatus.INDEFERIDO,
            administrator=admin
        )


def test_transition_valid(db, setup_data):
    _, admin, _, _, report = setup_data

    result = ReportService.transition_status(
        report.id,
        ReportStatus.ANALISANDO,
        administrator=admin,
        notes="Iniciando análise"
    )

    assert result.report.status == ReportStatus.ANALISANDO
    assert result.history.new_status == ReportStatus.ANALISANDO
    assert result.history.previous_status == ReportStatus.ABERTO
    assert result.history.changed_by == admin
    assert result.report.last_status_at is not None
