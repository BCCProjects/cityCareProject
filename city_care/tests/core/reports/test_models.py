from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from accounts.models import Citizen
from core.reports.models import Category, Department, Report, ReportPriority, ReportStatus, Tag


class ReportModelValidationTests(TestCase):
    def setUp(self):
        self.department = Department.objects.create(
            name="Serviços Urbanos",
            email="servicos@citycare.gov",
            phone="11999999999",
        )
        self.other_department = Department.objects.create(
            name="Iluminação",
            email="luz@citycare.gov",
            phone="11888888888",
        )
        self.category = Category.objects.create(
            department=self.department,
            name="Árvore caída",
            slug="arvore",
            description="Tratativa de árvores",
        )
        self.tag = Tag.objects.create(name="Galho", slug="galho")
        self.citizen = Citizen.objects.create(
            email="model-tests@example.com",
            full_name="Maria Silva",
            phone="11911111111",
            password="pbkdf2_sha256$260000$dummy$ZVd5Q3g=",
            is_active=True,
        )
        self.citizen.set_password("SenhaModel123")
        self.citizen.save()

    def _build_report(self, **overrides):
        base_kwargs = {
            "citizen": self.citizen,
            "category": self.category,
            "department": self.department,
            "title": "Fiscalizar poda inadequada",
            "description": "Galhos bloqueando a calçada",
            "priority": ReportPriority.MEDIUM,
            "address": "Rua das Flores, 10",
            "neighborhood": "Jardim",
            "latitude": Decimal("-23.550500"),
            "longitude": Decimal("-46.633300"),
            "last_status_at": timezone.now() - timedelta(hours=1),
        }
        base_kwargs.update(overrides)
        return Report(**base_kwargs)

    def test_category_must_match_department(self):
        report = self._build_report(department=self.other_department)
        with self.assertRaises(ValidationError) as exc:
            report.full_clean()
        self.assertIn("Categoria informada", str(exc.exception))

    def test_denied_reason_is_required_when_status_is_denied(self):
        report = self._build_report(status=ReportStatus.INDEFERIDO)
        with self.assertRaises(ValidationError) as exc:
            report.full_clean()
        self.assertIn("Informe o motivo de indeferimento", str(exc.exception))

    def test_report_allows_denied_reason_when_provided(self):
        report = self._build_report(
            status=ReportStatus.INDEFERIDO,
            denied_reason="Documentação incompleta",
        )
        report.full_clean()  # should not raise
        report.save()
        self.assertEqual(report.denied_reason, "Documentação incompleta")
