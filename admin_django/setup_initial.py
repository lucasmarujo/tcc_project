"""
Script para configuração inicial do sistema.
Cria dados de exemplo para testes.
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from students.models import Student, ExamSession
from monitoring.models import MonitoringEvent, Alert


def create_sample_data():
    """Cria dados de exemplo para testes."""
    
    print("=" * 60)
    print("  CONFIGURAÇÃO INICIAL - Criando dados de exemplo")
    print("=" * 60)
    print()
    
    # Criar alunos de exemplo
    print("Criando alunos de exemplo...")
    
    students_data = [
        {
            'registration_number': '202301',
            'name': 'João da Silva',
            'email': 'joao.silva@aluno.anchieta.br'
        },
        {
            'registration_number': '202302',
            'name': 'Maria Santos',
            'email': 'maria.santos@aluno.anchieta.br'
        },
        {
            'registration_number': '202303',
            'name': 'Pedro Oliveira',
            'email': 'pedro.oliveira@aluno.anchieta.br'
        },
    ]
    
    students = []
    for student_data in students_data:
        student, created = Student.objects.get_or_create(
            registration_number=student_data['registration_number'],
            defaults=student_data
        )
        students.append(student)
        status = "criado" if created else "ja existe"
        print(f"  [OK] {student.name} ({student.registration_number}) - {status}")
        if created:
            print(f"    API Key: {student.api_key}")
    
    print()
    
    # Criar sessão de exame de exemplo
    print("Criando sessão de exame de exemplo...")
    
    exam_session, created = ExamSession.objects.get_or_create(
        title='Prova Final - Matemática',
        defaults={
            'description': 'Prova final do primeiro semestre',
            'start_time': datetime.now() + timedelta(days=1),
            'end_time': datetime.now() + timedelta(days=1, hours=2),
            'status': 'scheduled'
        }
    )
    
    if created:
        exam_session.students.set(students)
        print(f"  [OK] Sessao de exame criada: {exam_session.title}")
    else:
        print(f"  [OK] Sessao de exame ja existe: {exam_session.title}")
    
    print()
    
    # Criar alguns eventos de exemplo
    print("Criando eventos de exemplo...")
    
    events_data = [
        {
            'student': students[0],
            'event_type': 'url_access',
            'url': 'https://ava.anchieta.br/curso/matematica',
            'browser': 'Google Chrome'
        },
        {
            'student': students[0],
            'event_type': 'url_access',
            'url': 'https://www.google.com/search?q=matematica',
            'browser': 'Google Chrome'
        },
        {
            'student': students[1],
            'event_type': 'app_launch',
            'app_name': 'Calculator.exe'
        },
    ]
    
    for event_data in events_data:
        event = MonitoringEvent.objects.create(**event_data, machine_name='PC-TESTE')
        print(f"  [OK] Evento criado: {event.student.name} - {event.get_event_type_display()}")
    
    print()
    
    # Criar alertas de exemplo
    print("Criando alertas de exemplo...")
    
    # Buscar evento de acesso ao Google
    google_event = MonitoringEvent.objects.filter(
        url__contains='google.com'
    ).first()
    
    if google_event:
        alert, created = Alert.objects.get_or_create(
            event=google_event,
            defaults={
                'student': google_event.student,
                'severity': 'high',
                'title': 'Acesso a site não permitido',
                'description': f'Aluno acessou: {google_event.url}',
                'reason': 'URL fora da whitelist de sites permitidos'
            }
        )
        status = "criado" if created else "ja existe"
        print(f"  [OK] Alerta {status}: {alert.title}")
    
    print()
    print("=" * 60)
    print("  Configuração concluída!")
    print("=" * 60)
    print()
    print("Próximos passos:")
    print("1. Acesse o admin: http://localhost:8000/admin")
    print("2. Acesse a dashboard: http://localhost:8000")
    print()
    print("Credenciais dos alunos (API Keys):")
    for student in Student.objects.all():
        print(f"  - {student.name}: {student.api_key}")
    print()


def main():
    """Função principal."""
    
    try:
        create_sample_data()
    except Exception as e:
        print(f"Erro ao criar dados de exemplo: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

