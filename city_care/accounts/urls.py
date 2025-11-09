from django.urls import path

from .views import CitizenRegistrationView, CitizenTokenObtainView, EmployeeRegistrationView, EmployeeTokenObtainView

urlpatterns = [
    path("citizens/register/", CitizenRegistrationView.as_view(), name="citizen-register"),
    path("citizens/token/", CitizenTokenObtainView.as_view(), name="citizen-token"),
    path("employees/register/", EmployeeRegistrationView.as_view(), name="employee-register"),
    path("employees/token/", EmployeeTokenObtainView.as_view(), name="employee-token"),
]
