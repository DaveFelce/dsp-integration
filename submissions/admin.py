from django.contrib import admin
from .models import DspEntityQueue, DspEntityAudit

@admin.register(DspEntityQueue)
class DspEntityQueueAdmin(admin.ModelAdmin):
    list_display = ('id', 'entity_type', 'status', 'attempts', 'updated_at')
    list_filter = ('status',)

@admin.register(DspEntityAudit)
class DspEntityAuditAdmin(admin.ModelAdmin):
    list_display = ('id', 'queue', 'http_status', 'attempt_at')
    list_filter = ('http_status',)
