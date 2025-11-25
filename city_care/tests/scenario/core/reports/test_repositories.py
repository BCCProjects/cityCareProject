from __future__ import annotations

from datetime import datetime, timedelta

from django.test import TestCase
from django.utils import timezone

from accounts.models import Citizen
from core.repositories import report_repository
from core.reports.models import Category, Department, Report, ReportPriority, ReportStatus
from tests.utils import ensure_location


class ReportRepositoryTests(TestCase):
    def setUp(self):
        _, self.city, self.organization = ensure_location("Repository Scenario City")
        self.department = Department.objects.create(
            name="Infraestrutura",
            email="infra@citycare.gov",
            phone="11777777777",
        )
        self.category_pavement = Category.objects.create(
            department=self.department,
            name="Pavimentacao",
            slug="pavimentacao",
            description="Buracos e afundamentos",
        )
        self.category_trees = Category.objects.create(
            department=self.department,
            name="Arborizacao",
            slug="arborizacao",
            description="Poda e quedas de arvores",
        )
        self.citizen = Citizen.objects.create(
            email="repository-tests@example.com",
            first_name="Joao",
            last_name="Souza",
            phone="11922222222",
            password="pbkdf2_sha256$260000$dummy$ZVd5Q3g=",
            is_active=True,
            city=self.city,
        )
        self.citizen.set_password("RepositoryTest123")
        self.citizen.save()

    def _create_report(
        self,
        *,
        category: Category,
        latitude: float,
        longitude: float,
        status: str = ReportStatus.ABERTO,
        priority: str = ReportPriority.MEDIUM,
        neighborhood: str = "Centro",
        created_at: datetime | None = None,
        last_status_at: datetime | None = None,
    ) -> Report:
        created_at = created_at or timezone.now()
        last_status_at = last_status_at or created_at
        return Report.objects.create(
            citizen=self.citizen,
            category=category,
            department=self.department,
            city=self.city,
            organization=self.organization,
            title=f"Sinalizar {category.name} em {latitude}",
            description="Ocorrencia registrada para testes de repositorio",
            priority=priority,
            address="Rua Teste, 42",
            neighborhood=neighborhood,
            latitude=latitude,
            longitude=longitude,
            status=status,
            created_at=created_at,
            last_status_at=last_status_at,
        )

    def test_ignore_query_requires_positive_hours(self):
        with self.assertRaises(ValueError):
            report_repository.get_reports_eligible_for_ignore(0)

    def test_ignore_query_returns_reports_sorted_by_last_status(self):
        older = timezone.now() - timedelta(hours=300)
        newer = timezone.now() - timedelta(hours=200)
        report_old = self._create_report(
            category=self.category_pavement,
            latitude=-23.1,
            longitude=-46.1,
            status=ReportStatus.DEFERIDO,
            last_status_at=older,
        )
        report_new = self._create_report(
            category=self.category_pavement,
            latitude=-23.2,
            longitude=-46.2,
            status=ReportStatus.ANALISANDO,
            last_status_at=newer,
        )

        eligible = report_repository.get_reports_eligible_for_ignore(168)
        self.assertEqual([item["id"] for item in eligible], [report_old.id, report_new.id])

    def test_average_resolution_time_by_category(self):
        created = timezone.now() - timedelta(days=4)
        self._create_report(
            category=self.category_pavement,
            latitude=-23.3,
            longitude=-46.3,
            status=ReportStatus.CONCLUIDO,
            created_at=created,
            last_status_at=created + timedelta(hours=48),
        )
        self._create_report(
            category=self.category_pavement,
            latitude=-23.4,
            longitude=-46.4,
            status=ReportStatus.CONCLUIDO,
            created_at=created,
            last_status_at=created + timedelta(hours=24),
        )
        self._create_report(
            category=self.category_trees,
            latitude=-23.5,
            longitude=-46.5,
            status=ReportStatus.ABERTO,
            created_at=created,
            last_status_at=created,
        )

        result = report_repository.get_average_resolution_time_by_category()
        categories = {item["category_name"]: round(item["average_hours"], 2) for item in result}
        self.assertEqual(len(categories), 1)
        self.assertAlmostEqual(categories[self.category_pavement.name], 36.0, places=1)

    def test_open_reports_grouped_by_neighborhood(self):
        self._create_report(
            category=self.category_pavement,
            latitude=-23.6,
            longitude=-46.6,
            status=ReportStatus.ABERTO,
            priority=ReportPriority.HIGH,
            neighborhood="Centro",
        )
        self._create_report(
            category=self.category_pavement,
            latitude=-23.7,
            longitude=-46.7,
            status=ReportStatus.ABERTO,
            priority=ReportPriority.LOW,
            neighborhood="Centro",
        )
        self._create_report(
            category=self.category_trees,
            latitude=-23.8,
            longitude=-46.8,
            status=ReportStatus.ABERTO,
            priority=ReportPriority.MEDIUM,
            neighborhood="Vila Nova",
        )

        data = report_repository.get_open_reports_grouped_by_neighborhood()
        totals = {(item["neighborhood"], item["priority"]): item["total"] for item in data}
        self.assertEqual(totals[("Centro", ReportPriority.HIGH)], 1)
        self.assertEqual(totals[("Centro", ReportPriority.LOW)], 1)
        self.assertEqual(totals[("Vila Nova", ReportPriority.MEDIUM)], 1)

    def test_weekly_series_by_status_groups_data(self):
        week_one = timezone.make_aware(datetime(2025, 1, 6, 10, 0, 0))
        week_two = timezone.make_aware(datetime(2025, 1, 15, 9, 0, 0))
        self._create_report(
            category=self.category_pavement,
            latitude=-23.9,
            longitude=-46.9,
            created_at=week_one,
            last_status_at=week_one,
            status=ReportStatus.ABERTO,
        )
        self._create_report(
            category=self.category_trees,
            latitude=-24.0,
            longitude=-47.0,
            created_at=week_two,
            last_status_at=week_two,
            status=ReportStatus.CONCLUIDO,
        )

        series = report_repository.get_weekly_series_by_status()
        weeks = {item["week"] for item in series}
        statuses = {item["status"] for item in series}
        self.assertEqual(len(weeks), 2)
        self.assertIn(ReportStatus.ABERTO, statuses)
        self.assertIn(ReportStatus.CONCLUIDO, statuses)
