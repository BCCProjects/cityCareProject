from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import City, Citizen, Employee, Organization, State


@admin.register(Employee)
class EmployeeAdmin(UserAdmin):
    model = Employee
    list_display = ("email", "first_name", "last_name", "organization", "is_staff", "is_active", "created_at")
    list_filter = ("organization", "is_staff", "is_active")
    ordering = ("email",)
    search_fields = ("email", "first_name", "last_name", "organization__name")
    fieldsets = (
        (None, {"fields": ("email", "password", "organization")}),
        ("Informacoes pessoais", {"fields": ("first_name", "last_name")}),
        (
            "Permissoes",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Datas importantes", {"fields": ("last_login", "created_at", "updated_at")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "organization",
                    "password1",
                    "password2",
                    "is_staff",
                    "is_active",
                ),
            },
        ),
    )
    readonly_fields = ("created_at", "updated_at")
    filter_horizontal = ("groups", "user_permissions")


@admin.register(Citizen)
class CitizenAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "phone", "city", "created_at")
    search_fields = ("first_name", "last_name", "email", "city__name", "city__state__abbreviation")
    list_filter = ("city__state", "city")
    readonly_fields = ("created_at", "updated_at")

    def full_name(self, obj):
        return obj.get_full_name()

    full_name.short_description = "Full name"
    full_name.admin_order_field = "first_name"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return True


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ("name", "abbreviation")
    search_fields = ("name", "abbreviation")


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ("name", "state")
    search_fields = ("name", "state__name", "state__abbreviation")
    list_filter = ("state",)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "state", "created_at")
    search_fields = ("name", "city__name", "city__state__abbreviation")
    list_filter = ("city__state",)
    readonly_fields = ("created_at", "updated_at")

    def state(self, obj):
        return obj.city.state

    state.short_description = "State"
