"""
Admin configuration for Students app.
"""
from django.contrib import admin
from .models import Student, ExamSession


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['registration_number', 'name', 'email', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['registration_number', 'name', 'email']
    readonly_fields = ['id', 'api_key', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('registration_number', 'name', 'email', 'is_active')
        }),
        ('Segurança', {
            'fields': ('api_key',),
            'classes': ('collapse',)
        }),
        ('Metadados', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ExamSession)
class ExamSessionAdmin(admin.ModelAdmin):
    list_display = ['title', 'start_time', 'end_time', 'status', 'created_at']
    list_filter = ['status', 'start_time', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    filter_horizontal = ['students']
    
    fieldsets = (
        ('Informações do Exame', {
            'fields': ('title', 'description', 'status')
        }),
        ('Período', {
            'fields': ('start_time', 'end_time')
        }),
        ('Alunos', {
            'fields': ('students',)
        }),
        ('Metadados', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

