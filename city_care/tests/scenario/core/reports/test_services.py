from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone

from accounts.models import Administrator, Citizen
from core.repositories import report_repository
from core.reports.models import Attachment, Category, Department, Report, ReportPriority, ReportStatus, Tag
from core.services.report_service import InvalidStatusTransition, ReportService
from tests.utils import ensure_location, force_resolved_city


class ReportServiceTests(TestCase):
    def setUp(self):
        _, self.city, self.organization = ensure_location("Scenario Service City")
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
            first_name="Fulano",
            last_name="Silva",
            phone="11988887777",
            password="pbkdf2_sha256$260000$dummy$ZVd5Q3g=",
            is_active=True,
            city=self.city,
        )
        self.citizen.set_password("SenhaSegura123")
        self.citizen.save()
        self.admin = Administrator.objects.create_superuser(
            email="admin@citycare.gov",
            password="SenhaSegura123",
            first_name="Admin",
            organization=self.organization,
        )
        Attachment._meta.get_field("file").storage = FileSystemStorage(location=settings.MEDIA_ROOT)
        force_resolved_city(self.city)

    def test_full_status_flow(self):
        file_data = SimpleUploadedFile("foto.jpg", b"fake-image", content_type="image/jpeg")
        report = ReportService.create_report(
            citizen=self.citizen,
            category=self.category,
            department=self.department,
            title="Buraco perigoso proximo a escola",
            description="Ha um buraco profundo proximo a escola municipal.",
            priority="ALTA",
            address="Rua A, 123",
            neighborhood="Centro",
            latitude=Decimal("-23.000000"),
            longitude=Decimal("-46.000000"),
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
        self.assertEqual(report.status_history.count(), 5)

    def test_indefere_requires_reason(self):
        report = ReportService.create_report(
            citizen=self.citizen,
            category=self.category,
            department=self.department,
            title="Solicitacao de poda",
            description="Poda necessaria.",
            priority="MEDIA",
            address="Rua B, 456",
            neighborhood="Centro",
            latitude=Decimal("-23.100000"),
            longitude=Decimal("-46.100000"),
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
            city=self.city,
            organization=self.organization,
            title="Buraco sem resposta",
            description="Sem retorno",
            priority="BAIXO",
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
            description="Fios caidos na rua",
            priority="MEDIA",
            address="Rua D, 321",
            neighborhood="Vila",
            latitude=Decimal("-23.300000"),
            longitude=Decimal("-46.300000"),
            tags=[self.tag_road, self.tag_urgent],
            attachments=[file_one, file_two],
        )

        self.assertEqual(report.tags.count(), 2)
        self.assertEqual(report.attachments.count(), 2)

    def test_normalize_priority_accepts_variants(self):
        self.assertEqual(ReportService.normalize_priority("alta"), ReportPriority.HIGH)
        self.assertEqual(ReportService.normalize_priority("media"), ReportPriority.MEDIUM)
        self.assertEqual(ReportService.normalize_priority("baixas"), ReportPriority.LOW)
        self.assertIsNone(ReportService.normalize_priority(None))

    def test_transition_to_invalid_status_raises_error(self):
        report = ReportService.create_report(
            citizen=self.citizen,
            category=self.category,
            department=self.department,
            title="Tapar buraco",
            description="Rua interditada",
            priority="ALTA",
            address="Rua Z",
            neighborhood="Bairro Novo",
            latitude=Decimal("-24.100000"),
            longitude=Decimal("-47.100000"),
            tags=[],
            attachments=[],
        )

        with self.assertRaises(InvalidStatusTransition):
            ReportService.transition_status(
                report.id,
                ReportStatus.CONCLUIDO,
                administrator=self.admin,
            )
