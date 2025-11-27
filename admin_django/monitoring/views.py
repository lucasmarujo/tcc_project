"""
Views for Monitoring API.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from datetime import timedelta

from .models import MonitoringEvent, Alert
from .serializers import (
    MonitoringEventSerializer, 
    MonitoringEventCreateSerializer,
    AlertSerializer
)
from students.models import Student


class MonitoringEventViewSet(viewsets.ModelViewSet):
    """ViewSet para eventos de monitoramento."""
    
    queryset = MonitoringEvent.objects.all().select_related('student', 'exam_session')
    serializer_class = MonitoringEventSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['student', 'event_type', 'exam_session']
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Retorna eventos recentes (últimas 24 horas)."""
        time_threshold = timezone.now() - timedelta(hours=24)
        recent_events = self.queryset.filter(timestamp__gte=time_threshold)
        
        serializer = self.get_serializer(recent_events, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_student(self, request):
        """Retorna eventos agrupados por aluno."""
        student_id = request.query_params.get('student_id')
        if not student_id:
            return Response(
                {'error': 'student_id parameter is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        events = self.queryset.filter(student_id=student_id)
        serializer = self.get_serializer(events, many=True)
        return Response(serializer.data)


class AlertViewSet(viewsets.ModelViewSet):
    """ViewSet para alertas."""
    
    queryset = Alert.objects.all().select_related('student', 'event')
    serializer_class = AlertSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['student', 'severity', 'status']
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Retorna alertas ativos (novos ou em revisão)."""
        active_alerts = self.queryset.filter(status__in=['new', 'reviewing'])
        serializer = self.get_serializer(active_alerts, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Marca um alerta como resolvido."""
        alert = self.get_object()
        alert.status = 'resolved'
        alert.resolved_at = timezone.now()
        
        if 'admin_notes' in request.data:
            alert.admin_notes = request.data['admin_notes']
        
        alert.save()
        serializer = self.get_serializer(alert)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Retorna estatísticas de alertas."""
        total = self.queryset.count()
        by_severity = {}
        by_status = {}
        
        for severity, _ in Alert.SEVERITY_LEVELS:
            by_severity[severity] = self.queryset.filter(severity=severity).count()
        
        for status_val, _ in Alert.STATUS_CHOICES:
            by_status[status_val] = self.queryset.filter(status=status_val).count()
        
        return Response({
            'total': total,
            'by_severity': by_severity,
            'by_status': by_status
        })


@api_view(['POST'])
@permission_classes([AllowAny])
def report_event(request):
    """
    Endpoint público para o script do aluno reportar eventos.
    Requer api_key válida no corpo da requisição.
    """
    serializer = MonitoringEventCreateSerializer(
        data=request.data,
        context={'request': request}
    )
    
    if serializer.is_valid():
        event = serializer.save()
        return Response(
            {
                'status': 'success',
                'event_id': str(event.id),
                'message': 'Evento registrado com sucesso'
            },
            status=status.HTTP_201_CREATED
        )
    
    return Response(
        {
            'status': 'error',
            'errors': serializer.errors
        },
        status=status.HTTP_400_BAD_REQUEST
    )


@api_view(['POST'])
@permission_classes([AllowAny])
def create_alert(request):
    """
    Endpoint para o script do aluno criar alertas (URL bloqueada, acesso indevido, etc).
    """
    registration_number = request.data.get('registration_number')
    
    if not registration_number:
        return Response(
            {'error': 'registration_number is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        student = Student.objects.get(registration_number=registration_number)
    except Student.DoesNotExist:
        return Response(
            {'error': 'Student not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Criar evento primeiro
    event_data = {
        'student': student.id,
        'event_type': request.data.get('event_type', 'system'),
        'url': request.data.get('url', ''),
        'browser': request.data.get('browser', ''),
        'app_name': request.data.get('app_name', ''),
        'window_title': request.data.get('window_title', ''),
        'machine_name': request.data.get('machine_name', ''),
        'additional_data': request.data.get('additional_data', {})
    }
    
    # Obter IP
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        event_data['ip_address'] = x_forwarded_for.split(',')[0]
    else:
        event_data['ip_address'] = request.META.get('REMOTE_ADDR')
    
    event = MonitoringEvent.objects.create(**event_data)
    
    # Criar alerta
    alert_data = {
        'event': event,
        'student': student,
        'severity': request.data.get('severity', 'medium'),
        'title': request.data.get('title', 'Alerta de Segurança'),
        'description': request.data.get('description', ''),
        'reason': request.data.get('reason', '')
    }
    
    alert = Alert.objects.create(**alert_data)
    
    return Response({
        'status': 'success',
        'alert_id': str(alert.id),
        'event_id': str(event.id),
        'message': 'Alerta criado com sucesso'
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def heartbeat(request):
    """
    Endpoint para o script enviar heartbeat (confirmar que está ativo).
    Cria o aluno automaticamente se não existir.
    """
    from students.models import StudentHeartbeat
    
    registration_number = request.data.get('registration_number')
    student_name = request.data.get('student_name')
    student_email = request.data.get('student_email')
    machine_name = request.data.get('machine_name', '')
    
    if not registration_number:
        return Response(
            {'error': 'registration_number is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Obter IP do cliente
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip_address = x_forwarded_for.split(',')[0]
    else:
        ip_address = request.META.get('REMOTE_ADDR')
    
    try:
        # Tentar buscar o aluno
        student = Student.objects.get(registration_number=registration_number)
        
        # Verificar se está ativo
        if not student.is_active:
            return Response(
                {'error': 'Aluno inativo. Entre em contato com a administração.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Atualizar ou criar heartbeat
        heartbeat_obj, created = StudentHeartbeat.objects.update_or_create(
            student=student,
            defaults={
                'machine_name': machine_name,
                'ip_address': ip_address
            }
        )
        
        return Response({
            'status': 'success',
            'student': student.name,
            'student_registration': student.registration_number,
            'monitoring_active': True,
            'new_student': False,
            'heartbeat_registered': True
        })
        
    except Student.DoesNotExist:
        # Se não existir, criar automaticamente
        if not student_name or not student_email:
            return Response({
                'error': 'Aluno não cadastrado',
                'requires_registration': True,
                'message': 'Por favor, informe seu nome e email'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Criar novo aluno
        student = Student.objects.create(
            registration_number=registration_number,
            name=student_name,
            email=student_email,
            is_active=True
        )
        
        # Criar heartbeat inicial
        StudentHeartbeat.objects.create(
            student=student,
            machine_name=machine_name,
            ip_address=ip_address
        )
        
        return Response({
            'status': 'success',
            'student': student.name,
            'student_registration': student.registration_number,
            'monitoring_active': True,
            'new_student': True,
            'heartbeat_registered': True,
            'message': 'Aluno cadastrado com sucesso!'
        }, status=status.HTTP_201_CREATED)

