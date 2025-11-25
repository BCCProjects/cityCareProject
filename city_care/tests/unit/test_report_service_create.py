import pytest
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError

from accounts.models import Citizen, Employee
from core.reports.models import Category, Department, ReportPriority, ReportStatus, Tag
from core.services.report_service import ReportService
from tests.utils import ensure_location, force_resolved_city

Administrator = Employee


@pytest.fixture
def basic_structures(db):
    _, city, organization = ensure_location("Infra City")
    dep = Department.objects.create(name="Infra", email="infra@test.com", phone="11999999999")
    cat = Category.objects.create(name="Iluminacao", slug="iluminacao-fixture", department=dep)

    admin = Administrator.objects.create_superuser(
        email="admin@test.com",
        password="123456",
        first_name="Admin",
        organization=organization,
    )

    citizen = Citizen.objects.create(
        email="citizen@test.com",
        first_name="User",
        last_name="Test",
        phone="123",
        password=make_password("Senha123"),
        city=city,
    )
    force_resolved_city(city)
    return citizen, cat, dep, admin


def test_create_report_basic(basic_structures):
    citizen, cat, dep, admin = basic_structures

    report = ReportService.create_report(
        citizen=citizen,
        category=cat,
        department=dep,
        title="Lǽmpada queimada",
        description="Rua inteira apagada.",
        priority=ReportPriority.HIGH,
        address="Rua A, 123",
        neighborhood="Centro",
        latitude=-22.0,
        longitude=-48.0,
        tags=[],
        attachments=[],
    )

    assert report.pk is not None
    assert report.title == "Lǽmpada queimada"
    # Quando nao ha anexos, o servico usa prioridade baixa (BAIXO).
    assert report.priority == ReportPriority.LOW
    assert report.status == ReportStatus.ABERTO


def test_create_report_duplication(basic_structures):
    citizen, cat, dep, admin = basic_structures

    ReportService.create_report(
        citizen=citizen,
        category=cat,
        department=dep,
        title="Buraco na rua",
        description="Em frente ao nǧmero 100",
        priority=ReportPriority.MEDIUM,
        address="Rua B",
        neighborhood="Centro",
        latitude=-10.0,
        longitude=-20.0,
        tags=[],
        attachments=[],
    )

    with pytest.raises(ValidationError):
        ReportService.create_report(
            citizen=citizen,
            category=cat,
            department=dep,
            title="Outro buraco",
            description="Mesmo local",
            priority=ReportPriority.MEDIUM,
            address="Rua B",
            neighborhood="Centro",
            latitude=-10.0,
            longitude=-20.0,
            tags=[],
            attachments=[],
        )


def test_create_report_tags_and_attachments(basic_structures, tmp_path):
    citizen, cat, dep, admin = basic_structures

    # Tag NAO tem category
    tag1 = Tag.objects.create(name="urgente", slug="urgente")
    tag2 = Tag.objects.create(name="iluminacao", slug="iluminacao")

    fake_file = tmp_path / "file.txt"
    fake_file.write_text("conteudo")

    from django.core.files.base import ContentFile

    attachment = ContentFile(fake_file.read_bytes(), name=fake_file.name)

    report = ReportService.create_report(
        citizen=citizen,
        category=cat,
        department=dep,
        title="Poste caido",
        description="Perigo na rua",
        priority=ReportPriority.HIGH,
        address="Rua X",
        neighborhood="Bairro Y",
        latitude="1.000001",
        longitude="2.000001",
        tags=[tag1, tag2],
        attachments=[attachment],
    )

    assert report.tags.count() == 2
    assert report.attachments.count() == 1
