from django.contrib import admin

from .models import Attachment, Category, Comment, Department, Report, ReportTag, StatusHistory, Tag


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "phone", "created_at")
    search_fields = ("name",)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "department", "slug", "created_at")
    search_fields = ("name", "slug")
    list_filter = ("department",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


class AttachmentInline(admin.TabularInline):
    model = Attachment
    extra = 0


class ReportTagInline(admin.TabularInline):
    model = ReportTag
    extra = 0


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    readonly_fields = ("citizen", "message", "created_at")


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        "citizen",
        "category",
        "department",
        "assigned_to",
        "status",
        "priority",
        "created_at",
        "last_status_at",
    )
    list_filter = ("status", "priority", "category", "category__department", "assigned_to", "tags")
    search_fields = ("title", "citizen__full_name", "category__name")
    inlines = [AttachmentInline, ReportTagInline, CommentInline]
    autocomplete_fields = ("citizen", "category", "department", "tags", "assigned_to")
    readonly_fields = ("created_at", "updated_at", "last_status_at")


@admin.register(StatusHistory)
class StatusHistoryAdmin(admin.ModelAdmin):
    list_display = ("report", "previous_status", "new_status", "changed_by", "created_at")
    search_fields = ("report__title", "changed_by__email")
    list_filter = ("new_status",)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("report", "citizen", "created_at")
    search_fields = ("report__title", "citizen__full_name")


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ("report", "file", "created_at")
    search_fields = ("report__title",)


@admin.register(ReportTag)
class ReportTagAdmin(admin.ModelAdmin):
    list_display = ("report", "tag")
    autocomplete_fields = ("report", "tag")
