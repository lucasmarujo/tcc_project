"""
Admin configuration for Monitoring app.
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import MonitoringEvent, Alert


@admin.register(MonitoringEvent)
class MonitoringEventAdmin(admin.ModelAdmin):
    list_display = ['student', 'event_type', 'formatted_url_or_app', 'timestamp', 'exam_session']
    list_filter = ['event_type', 'timestamp', 'browser', 'exam_session']
    search_fields = ['student__name', 'student__registration_number', 'url', 'app_name', 'window_title']
    readonly_fields = ['id', 'timestamp']
    date_hierarchy = 'timestamp'
    
    def formatted_url_or_app(self, obj):
        if obj.url:
            return format_html('<a href="{}" target="_blank">{}</a>', obj.url, obj.url[:50])
        elif obj.app_name:
            return obj.app_name
        return '-'
    formatted_url_or_app.short_description = 'URL/App'
    
    fieldsets = (
        ('Aluno', {
            'fields': ('student', 'exam_session')
        }),
        ('Evento', {
            'fields': ('event_type', 'timestamp')
        }),
        ('Detalhes', {
            'fields': ('url', 'browser', 'app_name', 'window_title')
        }),
        ('Sistema', {
            'fields': ('machine_name', 'ip_address', 'additional_data'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Alert)
class AlertAdmin(admin.ModelAdmin):
    list_display = ['title', 'student', 'severity_badge', 'status_badge', 'created_at', 'view_event']
    list_filter = ['severity', 'status', 'created_at']
    search_fields = ['title', 'description', 'student__name', 'student__registration_number']
    readonly_fields = ['id', 'event', 'student', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    def severity_badge(self, obj):
        colors = {
            'low': '#28a745',
            'medium': '#ffc107',
            'high': '#fd7e14',
            'critical': '#dc3545'
        }
        color = colors.get(obj.severity, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color, obj.get_severity_display()
        )
    severity_badge.short_description = 'Severidade'
    
    def status_badge(self, obj):
        colors = {
            'new': '#007bff',
            'reviewing': '#ffc107',
            'resolved': '#28a745',
            'false_positive': '#6c757d'
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def view_event(self, obj):
        url = f'/admin/monitoring/monitoringevent/{obj.event.id}/change/'
        return format_html('<a href="{}" target="_blank">Ver Evento</a>', url)
    view_event.short_description = 'Ação'
    
    fieldsets = (
        ('Informações do Alerta', {
            'fields': ('title', 'description', 'reason')
        }),
        ('Classificação', {
            'fields': ('severity', 'status')
        }),
        ('Relacionamentos', {
            'fields': ('student', 'event')
        }),
        ('Notas', {
            'fields': ('admin_notes',)
        }),
        ('Metadados', {
            'fields': ('id', 'created_at', 'updated_at', 'resolved_at'),
            'classes': ('collapse',)
        }),
    )

