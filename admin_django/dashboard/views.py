"""
Views for Dashboard.
"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from monitoring.models import MonitoringEvent, Alert
from students.models import Student, ExamSession


@login_required
def dashboard_home(request):
    """View principal da dashboard."""
    from django.http import JsonResponse
    
    # Verificar se é requisição AJAX
    ajax_type = request.GET.get('ajax')
    
    # Estatísticas gerais
    total_students = Student.objects.filter(is_active=True).count()
    total_events_today = MonitoringEvent.objects.filter(
        timestamp__date=timezone.now().date()
    ).count()
    
    active_alerts = Alert.objects.filter(status__in=['new', 'reviewing']).count()
    critical_alerts = Alert.objects.filter(
        status__in=['new', 'reviewing'],
        severity='critical'
    ).count()
    
    # Se é requisição AJAX para estatísticas
    if ajax_type == 'stats':
        return JsonResponse({
            'total_students': total_students,
            'total_events_today': total_events_today,
            'active_alerts': active_alerts,
            'critical_alerts': critical_alerts,
        })
    
    # Alertas recentes
    recent_alerts = Alert.objects.select_related(
        'student', 'event'
    ).filter(
        status__in=['new', 'reviewing']
    ).order_by('-created_at')[:10]
    
    # Eventos recentes
    recent_events = MonitoringEvent.objects.select_related(
        'student', 'exam_session'
    ).order_by('-timestamp')[:20]
    
    # Se é requisição AJAX para alertas ou eventos
    if ajax_type in ['alertas', 'eventos']:
        context = {
            'recent_alerts': recent_alerts if ajax_type == 'alertas' else [],
            'recent_events': recent_events if ajax_type == 'eventos' else [],
        }
        return render(request, 'dashboard/home.html', context)
    
    # Alunos com mais alertas
    students_with_alerts = Student.objects.annotate(
        alert_count=Count('alerts', filter=Q(alerts__status__in=['new', 'reviewing']))
    ).filter(alert_count__gt=0).order_by('-alert_count')[:10]
    
    # Sessões de exame ativas
    active_exams = ExamSession.objects.filter(
        status='active'
    ).prefetch_related('students')
    
    context = {
        'total_students': total_students,
        'total_events_today': total_events_today,
        'active_alerts': active_alerts,
        'critical_alerts': critical_alerts,
        'recent_alerts': recent_alerts,
        'recent_events': recent_events,
        'students_with_alerts': students_with_alerts,
        'active_exams': active_exams,
    }
    
    return render(request, 'dashboard/home.html', context)


@login_required
def student_detail(request, student_id):
    """View de detalhes de um aluno específico."""
    
    student = get_object_or_404(Student, pk=student_id)
    
    # Eventos do aluno
    events = MonitoringEvent.objects.filter(
        student=student
    ).order_by('-timestamp')[:50]
    
    # Alertas do aluno
    alerts = Alert.objects.filter(
        student=student
    ).order_by('-created_at')[:30]
    
    # Estatísticas
    events_last_24h = MonitoringEvent.objects.filter(
        student=student,
        timestamp__gte=timezone.now() - timedelta(hours=24)
    ).count()
    
    total_alerts = Alert.objects.filter(student=student).count()
    active_alerts_count = Alert.objects.filter(
        student=student,
        status__in=['new', 'reviewing']
    ).count()
    
    context = {
        'student': student,
        'events': events,
        'alerts': alerts,
        'events_last_24h': events_last_24h,
        'total_alerts': total_alerts,
        'active_alerts_count': active_alerts_count,
    }
    
    return render(request, 'dashboard/student_detail.html', context)


@login_required
def alerts_list(request):
    """View de lista de todos os alertas."""
    
    # Filtros
    status_filter = request.GET.get('status', 'active')
    severity_filter = request.GET.get('severity', '')
    
    alerts = Alert.objects.select_related('student', 'event')
    
    if status_filter == 'active':
        alerts = alerts.filter(status__in=['new', 'reviewing'])
    elif status_filter == 'resolved':
        alerts = alerts.filter(status='resolved')
    elif status_filter == 'all':
        pass
    
    if severity_filter:
        alerts = alerts.filter(severity=severity_filter)
    
    alerts = alerts.order_by('-created_at')[:100]
    
    context = {
        'alerts': alerts,
        'status_filter': status_filter,
        'severity_filter': severity_filter,
    }
    
    return render(request, 'dashboard/alerts_list.html', context)


@login_required
def events_list(request):
    """View de lista de todos os eventos."""
    
    # Filtros
    event_type = request.GET.get('type', '')
    student_id = request.GET.get('student', '')
    
    events = MonitoringEvent.objects.select_related('student', 'exam_session')
    
    if event_type:
        events = events.filter(event_type=event_type)
    
    if student_id:
        events = events.filter(student_id=student_id)
    
    events = events.order_by('-timestamp')[:100]
    
    # Lista de alunos para o filtro
    students = Student.objects.filter(is_active=True).order_by('name')
    
    context = {
        'events': events,
        'event_type': event_type,
        'student_id': student_id,
        'students': students,
        'event_types': MonitoringEvent.EVENT_TYPES,
    }
    
    return render(request, 'dashboard/events_list.html', context)


@login_required
def live_monitor(request):
    """View para monitoramento em tempo real."""
    from students.models import StudentHeartbeat
    
    # Obter apenas alunos com heartbeat recente (últimos 30 segundos)
    # Com heartbeat a cada 10s, se passar 30s sem heartbeat = script parou
    time_threshold = timezone.now() - timedelta(seconds=30)
    
    # Buscar heartbeats recentes
    online_heartbeats = StudentHeartbeat.objects.filter(
        last_heartbeat__gte=time_threshold,
        student__is_active=True
    ).select_related('student').order_by('student__name')
    
    # Montar lista de alunos online
    students_status = []
    for heartbeat in online_heartbeats:
        students_status.append({
            'student': heartbeat.student,
            'is_online': True,
            'last_activity': heartbeat.last_heartbeat,
            'registration_number': heartbeat.student.registration_number,
            'name': heartbeat.student.name,
            'email': heartbeat.student.email,
            'machine_name': heartbeat.machine_name,
            'ip_address': heartbeat.ip_address
        })
    
    # Contar totais
    online_count = len(students_status)
    total_students = Student.objects.filter(is_active=True).count()
    offline_count = total_students - online_count
    
    # Eventos recentes apenas dos alunos online (últimos 20)
    online_student_ids = [s['student'].id for s in students_status]
    recent_events = MonitoringEvent.objects.filter(
        student_id__in=online_student_ids
    ).select_related('student').order_by('-timestamp')[:20]
    
    context = {
        'page_title': 'Monitoramento em Tempo Real',
        'students_status': students_status,
        'online_count': online_count,
        'offline_count': offline_count,
        'total_students': total_students,
        'recent_events': recent_events,
    }
    
    return render(request, 'dashboard/live_monitor.html', context)

