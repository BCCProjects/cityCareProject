from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
from unittest import mock

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.core.files.storage import FileSystemStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone

from accounts.models import City, Citizen, Employee, Organization, State
from core.repositories import report_repository
from core.reports.models import Attachment, Category, Department, Report, ReportPriority, ReportStatus, Tag
from core.services.location_service import CityNotCoveredError
from core.services.report_service import InvalidStatusTransition, ReportService


class ReportServiceTests(TestCase):
    def setUp(self):
        settings.USE_SUPABASE_ATTACHMENTS = False
        self.state = State.objects.create(name="Sao Paulo", abbreviation="SP")
        self.city = City.objects.create(name="Sao Paulo", state=self.state)
        self.organization = Organization.objects.create(name="Prefeitura Sao Paulo", city=self.city)
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

        # Ensure at least one group exists for employees
        self.default_group = Group.objects.create(name="Default")
        self.employee = Employee.objects.create_superuser(
            email="employee@citycare.gov",
            password="SenhaSegura123",
            first_name="Employee",
            organization=self.organization,
        )
        self.employee.groups.add(self.default_group)
        field = Attachment._meta.get_field("file")
        self._original_attachment_storage = field.storage
        field.storage = FileSystemStorage(location=settings.MEDIA_ROOT)

        self.city_resolver_patcher = mock.patch(
            "core.services.report_service.resolve_city_from_coordinates",
            return_value=self.city,
        )
        self.mock_city_resolver = self.city_resolver_patcher.start()
        self.addCleanup(self.city_resolver_patcher.stop)
        self.addCleanup(self._restore_attachment_storage)

    def _restore_attachment_storage(self):
        Attachment._meta.get_field("file").storage = self._original_attachment_storage

    def test_full_status_flow(self):
        file_data = SimpleUploadedFile("foto.jpg", b"fake-image", content_type="image/jpeg")
        report = ReportService.create_report(
            citizen=self.citizen,
            category=self.category,
            department=self.department,
            title="Buraco perigoso proximo a escola",
            description="Ha um buraco profundo proximo a escola municipal.",
            priority=ReportPriority.HIGH,
            address="Rua A, 123",
            neighborhood="Centro",
            latitude=Decimal("-23.0"),
            longitude=Decimal("-46.0"),
            tags=[self.tag_road, self.tag_urgent],
            attachments=[file_data],
        )

        ReportService.transition_status(report.id, ReportStatus.ANALISANDO, employee=self.employee)
        ReportService.transition_status(report.id, ReportStatus.DEFERIDO, employee=self.employee)
        ReportService.transition_status(report.id, ReportStatus.EM_ANDAMENTO, employee=self.employee)
        result = ReportService.transition_status(report.id, ReportStatus.CONCLUIDO, employee=self.employee)

        report.refresh_from_db()
        self.assertEqual(report.status, ReportStatus.CONCLUIDO)
        self.assertEqual(report.organization, self.organization)
        self.assertEqual(report.attachments.count(), 1)
        self.assertEqual(report.tags.count(), 2)
        self.assertEqual(result.history.new_status, ReportStatus.CONCLUIDO)
        self.assertEqual(report.status_history.count(), 5)
        self.mock_city_resolver.assert_called_with(Decimal("-23.0"), Decimal("-46.0"))
        self.assertEqual(report.city, self.city)

    def test_indefere_requires_reason(self):
        report = ReportService.create_report(
            citizen=self.citizen,
            category=self.category,
            department=self.department,
            title="Solicitacao de poda",
            description="Poda necessaria.",
            priority=ReportPriority.MEDIUM,
            address="Rua B, 456",
            neighborhood="Centro",
            latitude=Decimal("-23.1"),
            longitude=Decimal("-46.1"),
            tags=[self.tag_road],
            attachments=[],
        )

        ReportService.transition_status(report.id, ReportStatus.ANALISANDO, employee=self.employee)
        with self.assertRaises(InvalidStatusTransition):
            ReportService.transition_status(report.id, ReportStatus.INDEFERIDO, employee=self.employee)

    def test_repository_ignore_query(self):
        report = Report.objects.create(
            citizen=self.citizen,
            category=self.category,
            department=self.department,
            city=self.city,
            organization=self.organization,
            title="Buraco sem resposta",
            description="Sem retorno",
            priority=ReportPriority.LOW,
            address="Rua C, 789",
            neighborhood="Bairro",
            latitude=Decimal("-23.2"),
            longitude=Decimal("-46.2"),
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
            priority=ReportPriority.MEDIUM,
            address="Rua D, 321",
            neighborhood="Vila",
            latitude=Decimal("-23.3"),
            longitude=Decimal("-46.3"),
            tags=[self.tag_road, self.tag_urgent],
            attachments=[file_one, file_two],
        )

        self.assertEqual(report.organization, self.organization)
        self.assertEqual(report.tags.count(), 2)
        self.assertEqual(report.attachments.count(), 2)

    def test_create_report_outside_configured_cities(self):
        self.mock_city_resolver.side_effect = CityNotCoveredError("fora da area")
        with self.assertRaises(ValidationError):
            ReportService.create_report(
                citizen=self.citizen,
                category=self.category,
                department=self.department,
                title="Ocorrencia distante",
                description="Local nao coberto",
                priority=ReportPriority.MEDIUM,
                address="Rua Z, 999",
                neighborhood="Centro",
                latitude=Decimal("-10.0"),
                longitude=Decimal("-35.0"),
                tags=[],
                attachments=[],
            )
