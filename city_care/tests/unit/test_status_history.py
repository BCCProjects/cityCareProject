from __future__ import annotations

from datetime import timedelta

import pytest
from django.contrib.auth.hashers import make_password
from django.utils import timezone

from accounts.models import Administrator, Citizen
from core.reports.models import Category, Department, Report, ReportStatus, StatusHistory
from tests.utils import ensure_location


@pytest.fixture
def base_report(db):
    _, city, organization = ensure_location("History City")
    admin = Administrator.objects.create_superuser(
        email="admin@example.com",
        password="Senha123",
        first_name="Admin",
        organization=organization,
    )
    citizen = Citizen.objects.create(
        email="citizen@example.com",
        first_name="Fulano",
        last_name="Teste",
        phone="11999999999",
        password=make_password("Senha123"),
        is_active=True,
        city=city,
    )
    department = Department.objects.create(name="Infra", email="infra@city.gov", phone="11988888888")
    category = Category.objects.create(department=department, name="Buracos", slug="buracos")
    report = Report.objects.create(
        citizen=citizen,
        category=category,
        department=department,
        city=city,
        organization=organization,
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
        previous_status=ReportStatus.ABERTO,
        new_status=ReportStatus.ANALISANDO,
        changed_by=admin,
        notes="Verificando",
        created_at=timezone.now() - timedelta(days=1),
    )
    StatusHistory.objects.create(
        report=report,
        previous_status=ReportStatus.ANALISANDO,
        new_status=ReportStatus.DEFERIDO,
        changed_by=admin,
        notes="Aprovado",
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
