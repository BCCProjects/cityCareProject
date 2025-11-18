from __future__ import annotations

from decimal import Decimal

import pytest
from django.contrib.auth.hashers import make_password
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from accounts.models import Administrator, Citizen
from core.reports.models import Category, Department, Report, ReportPriority


_ALIAS_EMAILS: dict[str, str] = {}


def home_view(_request):
    return HttpResponse("home")


@csrf_exempt
def fake_login_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        email = _ALIAS_EMAILS.get(username)
        if email:
            try:
                user = Administrator.objects.get(email=email)
            except Administrator.DoesNotExist:
                user = None
            if user and user.check_password(password):
                return HttpResponseRedirect("/")
        return HttpResponse("invalid credentials", status=400)
    return HttpResponse("login page")


urlpatterns = [
    path("", home_view, name="home"),
    path("login/", fake_login_view, name="login"),
]


@pytest.fixture(name="django_user_model")
def django_user_model_override():
    class Adapter:
        class objects:
            @staticmethod
            def create_user(username, password):
                email = f"{username}@example.com"
                user = Administrator.objects.create_user(email=email, password=password, first_name=username.title())
                _ALIAS_EMAILS[username] = email
                return user

    return Adapter


@pytest.fixture(autouse=True)
def clear_alias_map():
    _ALIAS_EMAILS.clear()
    yield
    _ALIAS_EMAILS.clear()


@pytest.mark.urls("tests.scenario.test_login_flow")
@pytest.mark.django_db
def test_login_flow(client, django_user_model):
    user = django_user_model.objects.create_user(
        username="fer",
        password="123"
    )

    response = client.post("/login/", {
        "username": "fer",
        "password": "123"
    })

    assert response.status_code == 302
    assert response.url == "/"


@pytest.mark.django_db
def test_report_creation_scenario():
    department = Department.objects.create(name="Obras", email="obras@city.gov", phone="11988887777")
    category = Category.objects.create(department=department, name="Buraco", slug="buraco")
    citizen = Citizen.objects.create(
        email="citizen@example.com",
        full_name="Cidadão Teste",
        phone="11999999999",
        password=make_password("Senha123"),
    )

    report = Report.objects.create(
        citizen=citizen,
        category=category,
        department=department,
        title="Buraco em frente à escola",
        description="Há um buraco grande na rua.",
        address="Rua A, 123",
        neighborhood="Centro",
        latitude=Decimal("1.000000"),
        longitude=Decimal("1.000000"),
    )

    assert Report.objects.count() == 1
    assert report.priority == ReportPriority.MEDIUM
