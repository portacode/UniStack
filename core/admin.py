from django.contrib import admin

from core.models import ModelInvocation


@admin.register(ModelInvocation)
class ModelInvocationAdmin(admin.ModelAdmin):
    list_display = ["id", "model", "status", "input_tokens", "output_tokens", "started_at"]
    list_filter = ["status", "model"]
    search_fields = ["chat_id", "request_id", "response_id"]
    readonly_fields = [field.name for field in ModelInvocation._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
