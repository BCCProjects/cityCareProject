import pytest
from accounts.models import Citizen, Administrator
from core.reports.models import Category, Department, Tag, Report
from core.services.report_service import ReportService
from django.core.exceptions import ValidationError

@pytest.fixture
def basic_structures(db):
    dep = Department.objects.create(name="Infra")
    cat = Category.objects.create(name="Iluminação", department=dep)

    admin = Administrator.objects.create_superuser(
        email="admin@test.com",
        password="123456",
        first_name="Admin"
    )

    citizen = Citizen.objects.create(
        email="citizen@test.com",
        full_name="User Test",
        phone="123",
        password="pbkdf2_test"
    )

    return citizen, cat, dep, admin


def test_create_report_basic(basic_structures):
    citizen, cat, dep, admin = basic_structures

    report = ReportService.create_report(
        citizen=citizen,
        category=cat,
        department=dep,
        title="Lâmpada queimada",
        description="Rua inteira apagada.",
        priority="ALTA",
        address="Rua A, 123",
        neighborhood="Centro",
        latitude=-22.0,
        longitude=-48.0,
        tags=[],
        attachments=[],
    )

    assert report.pk is not None
    assert report.title == "Lâmpada queimada"
    assert report.priority == "HIGH"
    assert report.status == "ABERTO"


def test_create_report_duplication(basic_structures):
    citizen, cat, dep, admin = basic_structures

    ReportService.create_report(
        citizen=citizen,
        category=cat,
        department=dep,
        title="Buraco na rua",
        description="Em frente ao número 100",
        priority="MEDIA",
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
            priority="MEDIA",
            address="Rua B",
            neighborhood="Centro",
            latitude=-10.0,
            longitude=-20.0,
            tags=[],
            attachments=[],
        )


def test_create_report_tags_and_attachments(basic_structures, tmp_path):
    citizen, cat, dep, admin = basic_structures

    # Tag NÃO tem category
    tag1 = Tag.objects.create(name="urgente")
    tag2 = Tag.objects.create(name="iluminação")

    class DummyAttachment:
        def __init__(self, file):
            self.file = file
            self.description = "desc"

    fake_file = tmp_path / "file.txt"
    fake_file.write_text("conteudo")

    attachment = DummyAttachment(file=str(fake_file))

    report = ReportService.create_report(
        citizen=citizen,
        category=cat,
        department=dep,
        title="Poste caído",
        description="Perigo na rua",
        priority="ALTA",
        address="Rua X",
        neighborhood="Bairro Y",
        latitude=1.1,
        longitude=2.2,
        tags=[tag1, tag2],
        attachments=[attachment],
    )

    assert report.tags.count() == 2
    assert report.attachments.count() == 1
