"""
Models para monitoramento de atividades dos alunos.
"""
from django.db import models
from students.models import Student, ExamSession
import uuid


class MonitoringEvent(models.Model):
    """Modelo para representar um evento de monitoramento."""
    
    EVENT_TYPES = [
        ('url_access', 'Acesso a URL'),
        ('app_launch', 'Abertura de Aplicativo'),
        ('window_change', 'Mudança de Janela'),
        ('copy_paste', 'Copiar/Colar'),
        ('screenshot', 'Screenshot Tentado'),
        ('keyboard_event', 'Evento de Teclado'),
        ('system', 'Evento do Sistema'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='events', verbose_name='Aluno')
    exam_session = models.ForeignKey(
        ExamSession, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='events',
        verbose_name='Sessão de Exame'
    )
    
    event_type = models.CharField('Tipo de Evento', max_length=20, choices=EVENT_TYPES)
    timestamp = models.DateTimeField('Data/Hora', auto_now_add=True)
    
    # Dados do evento
    url = models.URLField('URL', max_length=500, blank=True, null=True)
    browser = models.CharField('Navegador', max_length=50, blank=True)
    app_name = models.CharField('Nome do Aplicativo', max_length=200, blank=True)
    window_title = models.CharField('Título da Janela', max_length=500, blank=True)
    key_event = models.CharField('Evento de Tecla', max_length=100, blank=True)
    
    # Metadados
    machine_name = models.CharField('Nome da Máquina', max_length=200, blank=True)
    ip_address = models.GenericIPAddressField('Endereço IP', blank=True, null=True)
    additional_data = models.JSONField('Dados Adicionais', default=dict, blank=True)
    
    class Meta:
        db_table = 'monitoring_events'
        verbose_name = 'Evento de Monitoramento'
        verbose_name_plural = 'Eventos de Monitoramento'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['student', '-timestamp']),
            models.Index(fields=['event_type', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.student.name} - {self.get_event_type_display()} - {self.timestamp.strftime('%d/%m/%Y %H:%M:%S')}"


class Alert(models.Model):
    """Modelo para representar alertas de atividades suspeitas."""
    
    SEVERITY_LEVELS = [
        ('low', 'Baixa'),
        ('medium', 'Média'),
        ('high', 'Alta'),
        ('critical', 'Crítica'),
    ]
    
    STATUS_CHOICES = [
        ('new', 'Novo'),
        ('reviewing', 'Em Revisão'),
        ('resolved', 'Resolvido'),
        ('false_positive', 'Falso Positivo'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(MonitoringEvent, on_delete=models.CASCADE, related_name='alerts', verbose_name='Evento')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='alerts', verbose_name='Aluno')
    
    severity = models.CharField('Severidade', max_length=20, choices=SEVERITY_LEVELS, default='medium')
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='new')
    
    title = models.CharField('Título', max_length=200)
    description = models.TextField('Descrição')
    reason = models.TextField('Motivo do Alerta')
    
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    resolved_at = models.DateTimeField('Resolvido em', null=True, blank=True)
    
    # Notas do administrador
    admin_notes = models.TextField('Notas do Administrador', blank=True)
    
    class Meta:
        db_table = 'alerts'
        verbose_name = 'Alerta'
        verbose_name_plural = 'Alertas'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['severity', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.student.name} ({self.get_severity_display()})"

