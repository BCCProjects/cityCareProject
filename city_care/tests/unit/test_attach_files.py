from __future__ import annotations

import io
from pathlib import Path

import pytest
from django.core.files.base import ContentFile

from accounts.models import Administrator, Citizen
from tests.utils import ensure_location
from core.reports.models import Category, Department, Report
from core.services.report_service import ReportService


@pytest.fixture
def empty_report(db):
    _, city, organization = ensure_location("Attach City")
    Administrator.objects.create_superuser(
        email="admin@example.com",
        password="Senha123",
        first_name="Admin",
        organization=organization,
    )
    citizen = Citizen.objects.create(
        email="citizen@example.com",
        first_name="Fulano",
        last_name="da Silva",
        phone="11999999999",
        password="pbkdf2_sha256$260000$dummy$hash",
        is_active=True,
        city=city,
    )
    department = Department.objects.create(name="Infra", email="infra@city.gov", phone="11988888888")
    category = Category.objects.create(department=department, name="Buracos", slug="buracos")
    return Report.objects.create(
        citizen=citizen,
        category=category,
        department=department,
        city=city,
        organization=organization,
        title="Buraco na rua",
        description="Teste",
        address="Rua X",
        neighborhood="Centro",
        latitude="1.000000",
        longitude="2.000000",
    )


@pytest.mark.django_db
def test_attach_files_accepts_multiple_sources(empty_report, tmp_path):
    report = empty_report
    path_string = tmp_path / "string.txt"
    path_string.write_text("string")

    path_obj = tmp_path / "path.txt"
    path_obj.write_text("path")

    django_file = ContentFile(b"content", name="inline.txt")

    file_like = io.BytesIO(b"bytes")
    file_like.name = "bytes.bin"

    class Wrapper:
        def __init__(self, inner):
            self.file = inner
            self.description = "wrapped"

    wrapped = Wrapper(ContentFile(b"wrapped", name="wrapped.txt"))

    ReportService._attach_files(
        report,
        [
            str(path_string),
            Path(path_obj),
            django_file,
            file_like,
            wrapped,
        ],
    )

    names = [Path(name).name for name in report.attachments.values_list("file", flat=True)]
    assert len(names) == 5
    assert any(name.startswith("string") for name in names)
    assert any(name.startswith("path") for name in names)
    assert any(name.startswith("inline") and name.endswith(".txt") for name in names)
    assert any(name.startswith("bytes") and name.endswith(".bin") for name in names)
    assert any("wrapped" in name for name in names)
