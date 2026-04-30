from django.contrib import admin
from .models import WorkOrder, Brigade, BrigadeMember, Signature, AuditLog


@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display  = ['title', 'date', 'location', 'status', 'issuer', 'created_at']
    list_filter   = ['status']
    search_fields = ['title', 'location']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Brigade)
class BrigadeAdmin(admin.ModelAdmin):
    list_display = ['name', 'work_order']


@admin.register(BrigadeMember)
class BrigadeMemberAdmin(admin.ModelAdmin):
    list_display = ['user', 'brigade', 'is_leader']


@admin.register(Signature)
class SignatureAdmin(admin.ModelAdmin):
    list_display = ['user', 'work_order', 'role', 'signed_at']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display  = ['user', 'action', 'work_order', 'created_at']
    readonly_fields = ['user', 'work_order', 'action', 'description', 'created_at']