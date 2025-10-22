from __future__ import annotations

from datetime import timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone

from accounts.models import Administrator, Citizen
from core.repositories import report_repository
from core.reports.models import Category, Department, Report, ReportStatus, Tag
from core.services.report_service import InvalidStatusTransition, ReportService


class ReportServiceTests(TestCase):
    def setUp(self):
        self.department = Department.objects.create(name="Obras", email="obras@citycare.gov", phone="1199999999")
        self.category = Category.objects.create(
            department=self.department,
            name="Buracos",
            slug="buracos",
            description="Tratativa de buracos em vias",
        )
        self.tag_road = Tag.objects.create(name="Buraco", slug="buraco")
        self.tag_urgent = Tag.objects.create(name="Urgente", slug="urgente")
        self.citizen = Citizen.objects.create(
            email="citizen@example.com",
            full_name="Fulano",
            phone="11988887777",
            password="pbkdf2_sha256$260000$dummy$ZVd5Q3g=",
            is_active=True,
        )
        self.citizen.set_password("SenhaSegura123")
        self.citizen.save()
        self.admin = Administrator.objects.create_superuser(
            email="admin@citycare.gov",
            password="SenhaSegura123",
            first_name="Admin",
        )

    def test_full_status_flow(self):
        file_data = SimpleUploadedFile("foto.jpg", b"fake-image", content_type="image/jpeg")
        report = ReportService.create_report(
            citizen=self.citizen,
            category=self.category,
            department=self.department,
            title="Buraco perigoso próximo à escola",
            description="Há um buraco profundo próximo à escola municipal.",
            priority="ALTA",
            address="Rua A, 123",
            neighborhood="Centro",
            latitude=-23.0,
            longitude=-46.0,
            tags=[self.tag_road, self.tag_urgent],
            attachments=[file_data],
        )

        ReportService.transition_status(report.id, ReportStatus.ANALISANDO, administrator=self.admin)
        ReportService.transition_status(report.id, ReportStatus.DEFERIDO, administrator=self.admin)
        ReportService.transition_status(report.id, ReportStatus.EM_ANDAMENTO, administrator=self.admin)
        result = ReportService.transition_status(report.id, ReportStatus.CONCLUIDO, administrator=self.admin)

        report.refresh_from_db()
        self.assertEqual(report.status, ReportStatus.CONCLUIDO)
        self.assertEqual(report.attachments.count(), 1)
        self.assertEqual(report.tags.count(), 2)
        self.assertEqual(result.history.new_status, ReportStatus.CONCLUIDO)
        self.assertEqual(report.status_history.count(), 4)

    def test_indefere_requires_reason(self):
        report = ReportService.create_report(
            citizen=self.citizen,
            category=self.category,
            department=self.department,
            title="Solicitação de poda",
            description="Poda necessária.",
            priority="MEDIA",
            address="Rua B, 456",
            neighborhood="Centro",
            latitude=-23.1,
            longitude=-46.1,
            tags=[self.tag_road],
            attachments=[],
        )

        ReportService.transition_status(report.id, ReportStatus.ANALISANDO, administrator=self.admin)
        with self.assertRaises(InvalidStatusTransition):
            ReportService.transition_status(report.id, ReportStatus.INDEFERIDO, administrator=self.admin)

    def test_repository_ignore_query(self):
        report = Report.objects.create(
            citizen=self.citizen,
            category=self.category,
            department=self.department,
            title="Buraco sem resposta",
            description="Sem retorno",
            priority="BAIXA",
            address="Rua C, 789",
            neighborhood="Bairro",
            latitude=-23.2,
            longitude=-46.2,
            status=ReportStatus.ANALISANDO,
            last_status_at=timezone.now() - timedelta(hours=200),
        )

        eligible = report_repository.get_reports_eligible_for_ignore(168)
        self.assertTrue(any(item["id"] == report.id for item in eligible))

    def test_create_with_multiple_tags_and_attachments(self):
        file_one = SimpleUploadedFile("foto1.jpg", b"fake-image", content_type="image/jpeg")
        file_two = SimpleUploadedFile("foto2.png", b"fake-image", content_type="image/png")
        report = ReportService.create_report(
            citizen=self.citizen,
            category=self.category,
            department=self.department,
            title="Fios soltos",
            description="Fios caídos na rua",
            priority="MEDIA",
            address="Rua D, 321",
            neighborhood="Vila",
            latitude=-23.3,
            longitude=-46.3,
            tags=[self.tag_road, self.tag_urgent],
            attachments=[file_one, file_two],
        )

        self.assertEqual(report.tags.count(), 2)
        self.assertEqual(report.attachments.count(), 2)
