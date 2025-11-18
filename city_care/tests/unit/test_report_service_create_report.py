from __future__ import annotations

import io
from pathlib import Path

import pytest
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile

from accounts.models import Administrator, Citizen
from core.reports.models import Category, Department, ReportPriority, ReportStatus, StatusHistory, Tag
from core.services.report_service import ReportService
from tests.utils import ensure_location, force_resolved_city


@pytest.fixture
def base_entities(db):
    _, city, organization = ensure_location("Report Service City")
    admin = Administrator.objects.create_superuser(
        email="admin@example.com",
        password="Senha123",
        first_name="Admin",
        organization=organization,
    )
    citizen = Citizen.objects.create(
        email="citizen@example.com",
        first_name="Fulano",
        last_name="de Tal",
        phone="11999999999",
        password=make_password("Senha123"),
        is_active=True,
        city=city,
    )
    department = Department.objects.create(name="Infraestrutura", email="infra@citycare.gov", phone="11988887777")
    category = Category.objects.create(department=department, name="Iluminacao publica", slug="iluminacao")
    force_resolved_city(city)
    return admin, citizen, department, category


@pytest.fixture
def tags(db):
    return [
        Tag.objects.create(name="urgente", slug="urgente"),
        Tag.objects.create(name="noite", slug="noite"),
    ]


def test_create_report_with_history_tags_and_attachments(base_entities, tags, tmp_path):
    admin, citizen, department, category = base_entities

    path_one = tmp_path / "foto1.jpg"
    path_one.write_text("dummy")
    path_two = tmp_path / "foto2.png"
    path_two.write_text("dummy")
    file_like = io.BytesIO(b"bytes stream")
    file_like.name = "stream.bin"

    report = ReportService.create_report(
        citizen=citizen,
        category=category,
        department=department,
        title="Lampada queimada em avenida",
        description="Rua escura a noite",
        priority="ALTA",
        address="Rua A",
        neighborhood="Centro",
        latitude="-10.123456",
        longitude="-20.654321",
        tags=tags,
        attachments=[
            str(path_one),
            Path(path_two),
            ContentFile(b"inline", name="inline.txt"),
            file_like,
        ],
    )

    assert report.priority == ReportPriority.HIGH
    assert report.assigned_to == admin
    assert set(report.tags.values_list("name", flat=True)) == {"urgente", "noite"}
    assert report.attachments.count() == 4

    history = StatusHistory.objects.filter(report=report)
    assert history.count() == 1
    entry = history.first()
    assert entry.previous_status == ReportStatus.ABERTO
    assert entry.new_status == ReportStatus.ABERTO
    assert entry.changed_by == admin
    assert entry.notes == "Atribuicao inicial"


def test_create_report_uses_default_priority(base_entities, tags):
    _, citizen, department, category = base_entities

    report = ReportService.create_report(
        citizen=citizen,
        category=category,
        department=department,
        title="Buraco na rua",
        description="Descricao simples",
        priority="",
        address="Rua B",
        neighborhood="Centro",
        latitude="0.000001",
        longitude="0.000002",
        tags=tags,
        attachments=[],
    )
    assert report.priority == ReportPriority.MEDIUM


def test_create_report_duplicate_coordinates_raise(base_entities, tags):
    _, citizen, department, category = base_entities
    kwargs = dict(
        citizen=citizen,
        category=category,
        department=department,
        title="Primeiro teste",
        description="teste",
        priority="MEDIA",
        address="Rua C",
        neighborhood="Centro",
        latitude="1.000001",
        longitude="2.000001",
        tags=tags,
        attachments=[],
    )
    ReportService.create_report(**kwargs)

    with pytest.raises(ValidationError):
        ReportService.create_report(**kwargs)
