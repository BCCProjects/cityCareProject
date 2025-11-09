from __future__ import annotations

from unittest import mock

from django.test import TestCase

from accounts.models import City, Citizen, Employee, Organization, State
from core.reports.models import Category, Department, Report, ReportPriority, ReportStatus, StatusHistory


class ReportSignalTests(TestCase):
    def setUp(self):
        self.state = State.objects.create(name="Sao Paulo", abbreviation="SP")
        self.city = City.objects.create(name="Sao Paulo", state=self.state)
        self.organization = Organization.objects.create(name="Prefeitura", city=self.city)
        self.department = Department.objects.create(name="Obras", email="obras@test.com", phone="11999999999")
        self.category = Category.objects.create(
            department=self.department,
            name="Saneamento",
            slug="saneamento",
            description="Tratamento de saneamento",
        )
        self.citizen = Citizen.objects.create(
            email="citizen@example.com",
            first_name="Fulano",
            last_name="Silva",
            phone="11988887777",
            password="pbkdf2_sha256$260000$dummy$ZVd5Q3g=",
            city=self.city,
            is_active=True,
        )
        self.citizen.set_password("SenhaSegura123")
        self.citizen.save()
        self.employee = Employee.objects.create_superuser(
            email="funcionario@citycare.gov",
            password="SenhaSegura123",
            first_name="Funcionario",
            organization=self.organization,
        )
        self.report = Report.objects.create(
            citizen=self.citizen,
            category=self.category,
            department=self.department,
            organization=self.organization,
            assigned_to=self.employee,
            title="Buraco aberto",
            description="Buraco grande na avenida.",
            priority=ReportPriority.MEDIUM,
            address="Rua 1",
            neighborhood="Centro",
            latitude=-23.0,
            longitude=-46.0,
        )

    def test_status_history_updates_report_fields(self):
        history = StatusHistory.objects.create(
            report=self.report,
            previous_status=ReportStatus.ABERTO,
            new_status=ReportStatus.ANALISANDO,
            changed_by=self.employee,
            notes="Iniciando analise",
        )
        self.report.refresh_from_db()
        self.assertEqual(self.report.status, ReportStatus.ANALISANDO)
        self.assertEqual(self.report.last_status_at, history.created_at)

    def test_status_history_inferido_sets_denied_reason(self):
        StatusHistory.objects.create(
            report=self.report,
            previous_status=ReportStatus.ABERTO,
            new_status=ReportStatus.INDEFERIDO,
            changed_by=self.employee,
            notes="Documentacao incompleta",
        )
        self.report.refresh_from_db()
        self.assertEqual(self.report.status, ReportStatus.INDEFERIDO)
        self.assertEqual(self.report.denied_reason, "Documentacao incompleta")

    @mock.patch("core.reports.signals.emit_report_created")
    def test_report_creation_emits_event(self, emit_mock):
        report = Report.objects.create(
            citizen=self.citizen,
            category=self.category,
            department=self.department,
            organization=self.organization,
            assigned_to=self.employee,
            title="Nova ocorrencia",
            description="Descricao",
            priority=ReportPriority.MEDIUM,
            address="Rua 2",
            neighborhood="Centro",
            latitude=-23.1,
            longitude=-46.1,
        )
        emit_mock.assert_called_once_with(report)

    @mock.patch("core.reports.signals.emit_report_status_changed")
    def test_status_history_emits_event(self, emit_mock):
        history = StatusHistory.objects.create(
            report=self.report,
            previous_status=ReportStatus.ABERTO,
            new_status=ReportStatus.DEFERIDO,
            changed_by=self.employee,
            notes="Aprovado",
        )
        emit_mock.assert_called_once()
        emitted_report = emit_mock.call_args[0][0]
        self.assertEqual(emitted_report.status, ReportStatus.DEFERIDO)
        self.assertEqual(emit_mock.call_args[0][1], history)
