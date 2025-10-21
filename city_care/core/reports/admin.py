from django.contrib import admin

from .models import Attachment, Category, Comment, Department, Report, ReportTag, StatusHistory, Tag


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    search_fields = ["name"]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "department")
    search_fields = ("name",)
    list_filter = ("department",)


class ReportTagInline(admin.TabularInline):
    model = ReportTag
    extra = 0


class AttachmentInline(admin.TabularInline):
    model = Attachment
    extra = 0


class StatusHistoryInline(admin.TabularInline):
    model = StatusHistory
    extra = 0
    readonly_fields = ("from_status", "to_status", "reason", "changed_by", "changed_at")


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "priority", "status", "last_status_at")
    search_fields = ("title", "description", "address", "neighborhood")
    list_filter = ("category", "status", "priority")
    inlines = [ReportTagInline, AttachmentInline, StatusHistoryInline]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("report", "author", "created_at")
    search_fields = ("content",)


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ("report", "file", "created_at")


@admin.register(StatusHistory)
class StatusHistoryAdmin(admin.ModelAdmin):
    list_display = ("report", "from_status", "to_status", "changed_by", "changed_at")
    list_filter = ("to_status",)
