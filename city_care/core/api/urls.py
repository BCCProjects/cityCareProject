from django.urls import include, path
from rest_framework.routers import DefaultRouter

from accounts import urls as account_urls
from core.api import views

router = DefaultRouter()
router.register("departments", views.DepartmentViewSet, basename="department")
router.register("categories", views.CategoryViewSet, basename="category")
router.register("tags", views.TagViewSet, basename="tag")
router.register("reports", views.ReportViewSet, basename="report")
router.register("dashboard", views.DashboardViewSet, basename="dashboard")

urlpatterns = [
    path("auth/", include(account_urls)),
    path("", include(router.urls)),
]
