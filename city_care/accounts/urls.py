from django.urls import path

from .views import (
    AdministratorRegistrationView,
    AdministratorTokenObtainView,
    CitizenRegistrationView,
    CitizenTokenObtainView,
)

urlpatterns = [
    path("citizens/register", CitizenRegistrationView.as_view(), name="citizen-register"),
    path("citizens/token", CitizenTokenObtainView.as_view(), name="citizen-token"),
    path("admins/register", AdministratorRegistrationView.as_view(), name="admin-register"),
    path("admins/token", AdministratorTokenObtainView.as_view(), name="admin-token"),
]
