"""
Models para gerenciamento de alunos.
"""
from django.db import models
from django.core.validators import EmailValidator
import uuid


class Student(models.Model):
    """Modelo para representar um aluno monitorado."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    registration_number = models.CharField('Matrícula', max_length=50, unique=True)
    name = models.CharField('Nome', max_length=200)
    email = models.EmailField('Email', validators=[EmailValidator()])
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    is_active = models.BooleanField('Ativo', default=True)
    
    # Chave secreta para autenticação do script
    api_key = models.CharField('Chave API', max_length=100, unique=True, editable=False)
    
    class Meta:
        db_table = 'students'
        verbose_name = 'Aluno'
        verbose_name_plural = 'Alunos'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.registration_number} - {self.name}"
    
    def save(self, *args, **kwargs):
        if not self.api_key:
            self.api_key = uuid.uuid4().hex
        super().save(*args, **kwargs)


class StudentHeartbeat(models.Model):
    """Modelo para registrar heartbeats dos alunos (indica que o script está rodando)."""
    
    student = models.OneToOneField(
        Student, 
        on_delete=models.CASCADE, 
        related_name='heartbeat',
        verbose_name='Aluno'
    )
    last_heartbeat = models.DateTimeField('Último Heartbeat', auto_now=True)
    machine_name = models.CharField('Nome da Máquina', max_length=200, blank=True)
    ip_address = models.GenericIPAddressField('Endereço IP', blank=True, null=True)
    
    class Meta:
        db_table = 'student_heartbeats'
        verbose_name = 'Heartbeat do Aluno'
        verbose_name_plural = 'Heartbeats dos Alunos'
        ordering = ['-last_heartbeat']
    
    def __str__(self):
        return f"{self.student.name} - {self.last_heartbeat.strftime('%d/%m/%Y %H:%M:%S')}"
    
    def is_online(self, threshold_seconds=120):
        """Verifica se o aluno está online (heartbeat nos últimos X segundos)."""
        from django.utils import timezone
        from datetime import timedelta
        threshold = timezone.now() - timedelta(seconds=threshold_seconds)
        return self.last_heartbeat >= threshold


class ExamSession(models.Model):
    """Modelo para representar uma sessão de exame."""
    
    STATUS_CHOICES = [
        ('scheduled', 'Agendado'),
        ('active', 'Em Andamento'),
        ('completed', 'Concluído'),
        ('cancelled', 'Cancelado'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField('Título', max_length=200)
    description = models.TextField('Descrição', blank=True)
    students = models.ManyToManyField(Student, related_name='exam_sessions', verbose_name='Alunos')
    
    start_time = models.DateTimeField('Início')
    end_time = models.DateTimeField('Fim')
    status = models.CharField('Status', max_length=20, choices=STATUS_CHOICES, default='scheduled')
    
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        db_table = 'exam_sessions'
        verbose_name = 'Sessão de Exame'
        verbose_name_plural = 'Sessões de Exames'
        ordering = ['-start_time']
    
    def __str__(self):
        return f"{self.title} ({self.start_time.strftime('%d/%m/%Y %H:%M')})"

