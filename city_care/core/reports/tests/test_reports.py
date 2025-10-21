from __future__ import annotations

import shutil
import tempfile
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from core.reports.models import Category, Department, Report, StatusHistory, Tag
from core.reports.repositories.report_repository import ReportRepository
from core.reports.services.status_service import (
    IgnoreEligibilityError,
    MissingIndefermentReason,
    ReportStatusService,
)

User = get_user_model()


def create_department_and_category(name="Infraestrutura"):
    department = Department.objects.create(name=name)
    category = Category.objects.create(name="Iluminação", department=department)
    return department, category


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class ReportDomainTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="citizen", password="pass123")
        self.department, self.category = create_department_and_category()
        self.tag = Tag.objects.create(name="Iluminação")
        self.service = ReportStatusService(user=self.user)
        self.media_root = settings.MEDIA_ROOT
        self.addCleanup(lambda: shutil.rmtree(self.media_root, ignore_errors=True))

    def _create_report(self, **overrides):
        data = {
            "citizen": self.user,
            "category": self.category,
            "title": "Buraco na rua",
            "description": "Existe um buraco perigoso.",
            "priority": Report.Priority.HIGH,
            "address": "Rua das Flores, 123",
            "neighborhood": "Centro",
            "latitude": -23.000000,
            "longitude": -46.000000,
        }
        data.update(overrides)
        report = Report.objects.create(**data)
        report.tags.add(self.tag)
        return report

    def test_status_flow_creates_history(self):
        report = self._create_report()
        self.service.transition(report.id, Report.Status.ANALYZING)
        self.service.transition(report.id, Report.Status.APPROVED)
        self.service.transition(report.id, Report.Status.IN_PROGRESS)
        self.service.transition(report.id, Report.Status.COMPLETED)

        report.refresh_from_db()
        statuses = list(Report.objects.values_list("status", flat=True))
        self.assertEqual(statuses[0], Report.Status.COMPLETED)
        history = StatusHistory.objects.filter(report=report).order_by("changed_at")
        self.assertEqual(history.count(), 4)
        self.assertEqual(history.last().to_status, Report.Status.COMPLETED)

    def test_reject_requires_reason(self):
        report = self._create_report()
        self.service.transition(report.id, Report.Status.ANALYZING)
        with self.assertRaises(MissingIndefermentReason):
            self.service.transition(report.id, Report.Status.REJECTED)

    def test_ignore_repository_with_threshold(self):
        old_time = timezone.now() - timedelta(hours=200)
        report = self._create_report(status=Report.Status.ANALYZING, last_status_at=old_time)
        repo = ReportRepository()
        results = repo.get_reports_eligible_for_ignore(168)
        self.assertTrue(any(row["id"] == report.id for row in results))

    def test_create_report_with_tags_and_attachments(self):
        client = APIClient()
        client.force_authenticate(self.user)
        image = tempfile.NamedTemporaryFile(suffix=".jpg")
        image.write(b"fake image data")
        image.seek(0)
        tag = Tag.objects.create(name="Buraco")
        payload = {
            "title": "Buraco",
            "description": "Buraco enorme",
            "priority": Report.Priority.MEDIUM,
            "address": "Rua das Laranjeiras",
            "neighborhood": "Centro",
            "latitude": -23.555,
            "longitude": -46.444,
            "category": self.category.id,
            "tags": [self.tag.id, tag.id],
            "attachments": [image],
        }
        response = client.post(reverse("report-list"), data=payload, format="multipart")
        self.assertEqual(response.status_code, 201, response.content)
        report = Report.objects.get(id=response.data["id"])
        self.assertEqual(report.tags.count(), 2)
        self.assertEqual(report.attachments.count(), 1)

    def test_ignore_requires_eligibility(self):
        report = self._create_report()
        self.service.transition(report.id, Report.Status.ANALYZING)
        with self.assertRaises(IgnoreEligibilityError):
            self.service.transition(report.id, Report.Status.IGNORED)
