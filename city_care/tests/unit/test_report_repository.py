import pytest
import core.repositories.report_repository as repo
from core.reports.models import Report, Category, Department
from accounts.models import Citizen


def make_citizen():
    c = Citizen(
        email="test@test.com",
        full_name="Test User",
        phone="00000000000",
    )
    c.set_password("123456")
    c.save()
    return c



@pytest.mark.django_db
def test_get_reports_eligible_for_ignore_with_invalid_hours():
    with pytest.raises(ValueError):
        repo.get_reports_eligible_for_ignore(0)


@pytest.mark.django_db
def test_get_reports_eligible_for_ignore_returns_list():
    citizen = make_citizen()

    dep = Department.objects.create(
        name="Infra",
        email="infra@test.com",
        phone="111"
    )

    cat = Category.objects.create(
        name="Iluminação",
        slug="iluminacao",
        department=dep
    )

    Report.objects.create(
        citizen=citizen,
        department=dep,
        category=cat,
        title="Poste apagado",
        description="Teste",
        address="Rua X",
        neighborhood="Centro",
        latitude=1,
        longitude=1,
        status="ABERTO",
    )

    result = repo.get_reports_eligible_for_ignore(1)
    assert isinstance(result, list)


@pytest.mark.django_db
def test_get_open_reports_grouped_by_neighborhood():
    citizen = make_citizen()

    dep = Department.objects.create(name="Limpeza", email="x@x.com", phone="999")
    cat = Category.objects.create(name="Lixo", slug="lixo", department=dep)

    Report.objects.create(
        citizen=citizen,
        category=cat,
        department=dep,
        title="Lixo 1",
        description="OK",
        address="Rua A",
        neighborhood="Centro",
        latitude=1,
        longitude=1,
        status="ABERTO",
    )

    Report.objects.create(
        citizen=citizen,
        category=cat,
        department=dep,
        title="Lixo 2",
        description="OK",
        address="Rua A",
        neighborhood="Centro",
        latitude=2,  # <--- DIFFERENT
        longitude=1,
        status="ABERTO",
    )

    result = repo.get_open_reports_grouped_by_neighborhood()

    assert isinstance(result, list)
    assert result[0]["total"] == 2


@pytest.mark.django_db
def test_get_average_resolution_time_by_category_returns_list():
    result = repo.get_average_resolution_time_by_category()
    assert isinstance(result, list)


@pytest.mark.django_db
def test_get_weekly_series_by_status_returns_list():
    result = repo.get_weekly_series_by_status()
    assert isinstance(result, list)
