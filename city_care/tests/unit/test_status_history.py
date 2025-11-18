from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone

from accounts.models import Administrator, Citizen
from core.reports.models import Category, Department, Report, ReportStatus, StatusHistory


@pytest.fixture
def base_report(db):
    admin = Administrator.objects.create_superuser(
        email="admin@example.com",
        password="Senha123",
        first_name="Admin",
    )
    citizen = Citizen.objects.create(
        email="citizen@example.com",
        full_name="Fulano",
        phone="11999999999",
        password="pbkdf2_sha256$260000$dummy$hash",
        is_active=True,
    )
    department = Department.objects.create(name="Infra", email="infra@city.gov", phone="11988888888")
    category = Category.objects.create(department=department, name="Buracos", slug="buracos")
    report = Report.objects.create(
        citizen=citizen,
        category=category,
        department=department,
        title="Buraco na rua",
        description="Bem grande",
        address="Rua X",
        neighborhood="Centro",
        latitude="1.000000",
        longitude="2.000000",
    )
    return report, admin


@pytest.mark.django_db
def test_status_history_properties_and_ordering(base_report):
    report, admin = base_report
    StatusHistory.objects.create(
        report=report,
        old_status=ReportStatus.ABERTO,
        new_status=ReportStatus.ANALISANDO,
        administrator=admin,
        reason="Verificando",
        created_at=timezone.now() - timedelta(days=1),
    )
    StatusHistory.objects.create(
        report=report,
        old_status=ReportStatus.ANALISANDO,
        new_status=ReportStatus.DEFERIDO,
        administrator=admin,
        reason="Aprovado",
        created_at=timezone.now(),
    )

    history = list(StatusHistory.objects.filter(report=report))
    assert len(history) == 2
    # Ordering desc
    assert history[0].new_status == ReportStatus.DEFERIDO
    assert history[1].new_status == ReportStatus.ANALISANDO
    # Properties
    latest = history[0]
    assert latest.previous_status == ReportStatus.ANALISANDO
    assert latest.changed_by == admin
