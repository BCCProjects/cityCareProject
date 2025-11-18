from django.urls import path

from .views import (
    AdministratorRegistrationView,
    AdministratorTokenObtainView,
    CitizenProfileView,
    CitizenRegistrationView,
    CitizenTokenObtainView,
    EmployeeRegistrationView,
    EmployeeTokenObtainView,
)

urlpatterns = [
    path("citizens/register/", CitizenRegistrationView.as_view(), name="citizen-register"),
    path("citizens/token/", CitizenTokenObtainView.as_view(), name="citizen-token"),
    path("citizens/me/", CitizenProfileView.as_view(), name="citizen-profile"),
    path("employees/register/", EmployeeRegistrationView.as_view(), name="employee-register"),
    path("employees/token/", EmployeeTokenObtainView.as_view(), name="employee-token"),
    path("admins/register/", AdministratorRegistrationView.as_view(), name="admin-register"),
    path("admins/token/", AdministratorTokenObtainView.as_view(), name="admin-token"),
]
