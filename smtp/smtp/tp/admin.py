from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Course, Lesson


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "instructor", "is_deleted", "created_at")
    list_filter = ("is_deleted", "instructor")
    search_fields = ("title", "description", "slug")
    actions = ["soft_delete_selected", "restore_selected", "hard_delete_selected"]

    @admin.action(description=_("Soft delete selected courses"))
    def soft_delete_selected(self, request, queryset):
        updated = queryset.filter(is_deleted=False).update(is_deleted=True, deleted_at=admin.utils.timezone.now())
        self.message_user(request, _("Soft-deleted %d courses") % updated)

    @admin.action(description=_("Restore selected courses"))
    def restore_selected(self, request, queryset):
        updated = queryset.filter(is_deleted=True).update(is_deleted=False, deleted_at=None)
        self.message_user(request, _("Restored %d courses") % updated)

    @admin.action(description=_("Hard delete selected courses"))
    def hard_delete_selected(self, request, queryset):
        count = queryset.count()
        queryset.delete()  # this will call hard delete on queryset
        self.message_user(request, _("Hard-deleted %d courses") % count)


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ("title", "course", "order", "is_deleted")
    list_filter = ("is_deleted", "course")
    search_fields = ("title", "content")
    actions = ["soft_delete_selected", "restore_selected", "hard_delete_selected"]

    @admin.action(description=_("Soft delete selected lessons"))
    def soft_delete_selected(self, request, queryset):
        updated = queryset.filter(is_deleted=False).update(is_deleted=True, deleted_at=admin.utils.timezone.now())
        self.message_user(request, _("Soft-deleted %d lessons") % updated)

    @admin.action(description=_("Restore selected lessons"))
    def restore_selected(self, request, queryset):
        updated = queryset.filter(is_deleted=True).update(is_deleted=False, deleted_at=None)
        self.message_user(request, _("Restored %d lessons") % updated)

    @admin.action(description=_("Hard delete selected lessons"))
    def hard_delete_selected(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, _("Hard-deleted %d lessons") % count)
from django.contrib import admin

# Register your models here.
