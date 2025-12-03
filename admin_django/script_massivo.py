"""
Script para criar 500.000 registros de eventos e alertas em massa.
Utiliza bulk_create para máxima eficiência.
"""
import os
import sys
import django
import random
import uuid
from datetime import datetime, timedelta
from time import time

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from students.models import Student, ExamSession
from monitoring.models import MonitoringEvent, Alert
from django.utils import timezone


# Configurações
TOTAL_EVENTS = 500_000
TOTAL_ALERTS = 500_000
BATCH_SIZE = 10_000  # Inserir em lotes de 10.000 registros


# Dados para geração aleatória
EVENT_TYPES = [
    'url_access',
    'app_launch',
    'window_change',
    'copy_paste',
    'screenshot',
    'keyboard_event',
    'brightspace_event',
    'system',
]

URLS = [
    'https://ava.anchieta.br/prova/matematica',
    'https://ava.anchieta.br/curso/portugues',
    'https://ava.anchieta.br/exame/final',
    'https://www.google.com/search?q=resposta',
    'https://www.youtube.com/watch?v=tutorial',
    'https://stackoverflow.com/questions/python',
    'https://github.com/projeto/codigo',
    'https://translate.google.com',
    'https://www.wikipedia.org',
    'https://chat.openai.com',
]

BROWSERS = ['Google Chrome', 'Mozilla Firefox', 'Microsoft Edge', 'Brave']

APPS = [
    'Calculator.exe',
    'Notepad.exe',
    'Code.exe',
    'Discord.exe',
    'WhatsApp.exe',
    'Spotify.exe',
    'Excel.exe',
    'Word.exe',
]

WINDOW_TITLES = [
    'Prova de Matemática - AVA',
    'Google - Pesquisa',
    'YouTube - Como fazer',
    'Visual Studio Code',
    'Calculadora',
    'Discord - Chat',
    'WhatsApp Web',
]

KEY_EVENTS = [
    'Ctrl+C',
    'Ctrl+V',
    'Alt+Tab',
    'Ctrl+A',
    'Ctrl+Z',
    'PrintScreen',
    'Ctrl+Shift+Esc',
]

MACHINE_NAMES = [
    'DESKTOP-PC01',
    'DESKTOP-PC02',
    'LAPTOP-USER01',
    'NOTEBOOK-001',
    'PC-LAB-01',
]

IP_ADDRESSES = [
    '192.168.1.10',
    '192.168.1.11',
    '192.168.1.12',
    '192.168.1.13',
    '192.168.1.14',
    '10.0.0.100',
    '10.0.0.101',
]

# Dados para alertas
ALERT_SEVERITIES = ['low', 'medium', 'high', 'critical']
ALERT_STATUSES = ['new', 'reviewing', 'resolved', 'false_positive']

ALERT_TITLES = [
    'Acesso a site não permitido',
    'Tentativa de captura de tela',
    'Aplicativo suspeito detectado',
    'Mudança frequente de janela',
    'Uso de copiar/colar',
    'Teclas de atalho suspeitas',
    'Acesso a mecanismo de busca',
    'Troca de contexto detectada',
]

ALERT_DESCRIPTIONS = [
    'O aluno acessou um site fora da lista permitida durante a prova.',
    'Foi detectada uma tentativa de capturar a tela.',
    'Aplicativo não autorizado foi aberto durante o exame.',
    'Múltiplas mudanças de janela em curto período de tempo.',
    'Uso excessivo de copiar e colar detectado.',
    'Combinação de teclas suspeita foi pressionada.',
    'Acesso a mecanismo de busca durante a prova.',
    'Comportamento anormal de troca de contexto.',
]

ALERT_REASONS = [
    'URL fora da whitelist de sites permitidos',
    'Tentativa de violação das regras do exame',
    'Aplicativo bloqueado iniciado',
    'Comportamento suspeito detectado',
    'Possível tentativa de cola',
    'Violação das políticas de segurança',
    'Atividade não autorizada',
]


def get_or_create_students(num_students=100):
    """Obtém alunos existentes ou cria novos se necessário."""
    
    print(f"\n{'='*70}")
    print("VERIFICANDO ALUNOS NO BANCO DE DADOS")
    print(f"{'='*70}")
    
    existing_students = list(Student.objects.filter(is_active=True))
    
    if len(existing_students) >= num_students:
        print(f"✓ Encontrados {len(existing_students)} alunos ativos no banco.")
        return existing_students[:num_students]
    
    print(f"⚠ Apenas {len(existing_students)} alunos encontrados.")
    print(f"  Criando {num_students - len(existing_students)} novos alunos...")
    
    # Criar novos alunos
    new_students = []
    for i in range(len(existing_students), num_students):
        student = Student(
            registration_number=f'2023{str(i+1).zfill(4)}',
            name=f'Aluno {i+1}',
            email=f'aluno{i+1}@teste.br',
            api_key=uuid.uuid4().hex,
            is_active=True
        )
        new_students.append(student)
    
    # Criar em lote
    Student.objects.bulk_create(new_students, batch_size=1000)
    print(f"✓ {len(new_students)} novos alunos criados com sucesso!")
    
    return list(Student.objects.filter(is_active=True)[:num_students])


def get_or_create_exam_session(students):
    """Obtém ou cria uma sessão de exame."""
    
    print(f"\n{'='*70}")
    print("VERIFICANDO SESSÃO DE EXAME")
    print(f"{'='*70}")
    
    exam_session = ExamSession.objects.filter(status='active').first()
    
    if not exam_session:
        print("⚠ Nenhuma sessão ativa encontrada. Criando nova sessão...")
        exam_session = ExamSession.objects.create(
            title='Prova Massiva - Teste de Carga',
            description='Sessão de exame para teste de carga do sistema',
            start_time=timezone.now() - timedelta(hours=2),
            end_time=timezone.now() + timedelta(hours=2),
            status='active'
        )
        exam_session.students.set(students)
        print(f"✓ Sessão de exame criada: {exam_session.title}")
    else:
        print(f"✓ Sessão ativa encontrada: {exam_session.title}")
    
    return exam_session


def generate_monitoring_events(students, exam_session, total_events):
    """Gera eventos de monitoramento em massa."""
    
    print(f"\n{'='*70}")
    print(f"GERANDO {total_events:,} EVENTOS DE MONITORAMENTO")
    print(f"{'='*70}")
    print(f"Batch size: {BATCH_SIZE:,} registros por lote")
    print()
    
    start_time = time()
    total_batches = (total_events + BATCH_SIZE - 1) // BATCH_SIZE
    
    # Data base para os eventos (últimas 24 horas)
    base_time = timezone.now() - timedelta(hours=24)
    
    created_events = []
    
    for batch_num in range(total_batches):
        batch_start = batch_num * BATCH_SIZE
        batch_end = min(batch_start + BATCH_SIZE, total_events)
        batch_size = batch_end - batch_start
        
        events = []
        for i in range(batch_size):
            event_type = random.choice(EVENT_TYPES)
            student = random.choice(students)
            
            # Timestamp aleatório nas últimas 24 horas
            random_seconds = random.randint(0, 24 * 3600)
            timestamp = base_time + timedelta(seconds=random_seconds)
            
            event = MonitoringEvent(
                id=uuid.uuid4(),
                student=student,
                exam_session=exam_session if random.random() > 0.3 else None,
                event_type=event_type,
                url=random.choice(URLS) if event_type == 'url_access' else '',
                browser=random.choice(BROWSERS) if event_type == 'url_access' else '',
                app_name=random.choice(APPS) if event_type in ['app_launch', 'window_change'] else '',
                window_title=random.choice(WINDOW_TITLES) if event_type == 'window_change' else '',
                key_event=random.choice(KEY_EVENTS) if event_type == 'keyboard_event' else '',
                machine_name=random.choice(MACHINE_NAMES),
                ip_address=random.choice(IP_ADDRESSES),
                additional_data={
                    'batch': batch_num,
                    'index': i,
                    'generated': True
                }
            )
            events.append(event)
        
        # Inserir lote no banco
        batch_start_time = time()
        created = MonitoringEvent.objects.bulk_create(events, batch_size=BATCH_SIZE)
        batch_time = time() - batch_start_time
        
        created_events.extend(created)
        
        # Mostrar progresso
        progress = (batch_end / total_events) * 100
        events_per_sec = batch_size / batch_time if batch_time > 0 else 0
        elapsed = time() - start_time
        
        print(f"[{batch_num+1}/{total_batches}] "
              f"Progresso: {progress:6.2f}% | "
              f"Inseridos: {batch_end:>7,}/{total_events:,} | "
              f"Velocidade: {events_per_sec:>8,.0f} eventos/s | "
              f"Tempo: {elapsed:>6.1f}s")
    
    total_time = time() - start_time
    avg_speed = total_events / total_time if total_time > 0 else 0
    
    print()
    print(f"✓ {total_events:,} eventos criados com sucesso!")
    print(f"  Tempo total: {total_time:.2f}s")
    print(f"  Velocidade média: {avg_speed:,.0f} eventos/s")
    
    return created_events


def generate_alerts(events, students, total_alerts):
    """Gera alertas em massa baseados nos eventos."""
    
    print(f"\n{'='*70}")
    print(f"GERANDO {total_alerts:,} ALERTAS")
    print(f"{'='*70}")
    print(f"Batch size: {BATCH_SIZE:,} registros por lote")
    print()
    
    if len(events) < total_alerts:
        print(f"⚠ Aviso: Apenas {len(events)} eventos disponíveis para {total_alerts:,} alertas.")
        print(f"  Alertas serão criados reutilizando eventos.")
    
    start_time = time()
    total_batches = (total_alerts + BATCH_SIZE - 1) // BATCH_SIZE
    
    for batch_num in range(total_batches):
        batch_start = batch_num * BATCH_SIZE
        batch_end = min(batch_start + BATCH_SIZE, total_alerts)
        batch_size = batch_end - batch_start
        
        alerts = []
        for i in range(batch_size):
            # Selecionar evento (com possível reuso)
            event = events[(batch_start + i) % len(events)]
            
            # 70% dos alertas são relacionados ao aluno do evento
            student = event.student if random.random() > 0.3 else random.choice(students)
            
            # Peso maior para severidades médias
            severity_weights = [0.2, 0.4, 0.3, 0.1]  # low, medium, high, critical
            severity = random.choices(ALERT_SEVERITIES, weights=severity_weights)[0]
            
            # Peso maior para alertas novos
            status_weights = [0.6, 0.2, 0.15, 0.05]  # new, reviewing, resolved, false_positive
            status = random.choices(ALERT_STATUSES, weights=status_weights)[0]
            
            alert = Alert(
                id=uuid.uuid4(),
                event=event,
                student=student,
                severity=severity,
                status=status,
                title=random.choice(ALERT_TITLES),
                description=random.choice(ALERT_DESCRIPTIONS),
                reason=random.choice(ALERT_REASONS),
                admin_notes='' if random.random() > 0.2 else 'Verificado automaticamente',
                resolved_at=timezone.now() if status == 'resolved' else None
            )
            alerts.append(alert)
        
        # Inserir lote no banco
        batch_start_time = time()
        Alert.objects.bulk_create(alerts, batch_size=BATCH_SIZE)
        batch_time = time() - batch_start_time
        
        # Mostrar progresso
        progress = (batch_end / total_alerts) * 100
        alerts_per_sec = batch_size / batch_time if batch_time > 0 else 0
        elapsed = time() - start_time
        
        print(f"[{batch_num+1}/{total_batches}] "
              f"Progresso: {progress:6.2f}% | "
              f"Inseridos: {batch_end:>7,}/{total_alerts:,} | "
              f"Velocidade: {alerts_per_sec:>8,.0f} alertas/s | "
              f"Tempo: {elapsed:>6.1f}s")
    
    total_time = time() - start_time
    avg_speed = total_alerts / total_time if total_time > 0 else 0
    
    print()
    print(f"✓ {total_alerts:,} alertas criados com sucesso!")
    print(f"  Tempo total: {total_time:.2f}s")
    print(f"  Velocidade média: {avg_speed:,.0f} alertas/s")


def show_statistics():
    """Mostra estatísticas do banco de dados."""
    
    print(f"\n{'='*70}")
    print("ESTATÍSTICAS DO BANCO DE DADOS")
    print(f"{'='*70}")
    
    total_students = Student.objects.count()
    total_exam_sessions = ExamSession.objects.count()
    total_events = MonitoringEvent.objects.count()
    total_alerts = Alert.objects.count()
    
    print(f"\n📊 Resumo:")
    print(f"  • Alunos: {total_students:,}")
    print(f"  • Sessões de Exame: {total_exam_sessions:,}")
    print(f"  • Eventos de Monitoramento: {total_events:,}")
    print(f"  • Alertas: {total_alerts:,}")
    
    if total_events > 0:
        print(f"\n📈 Eventos por tipo:")
        for event_type, label in MonitoringEvent.EVENT_TYPES:
            count = MonitoringEvent.objects.filter(event_type=event_type).count()
            percentage = (count / total_events) * 100
            print(f"  • {label}: {count:,} ({percentage:.1f}%)")
    
    if total_alerts > 0:
        print(f"\n🚨 Alertas por severidade:")
        for severity, label in Alert.SEVERITY_LEVELS:
            count = Alert.objects.filter(severity=severity).count()
            percentage = (count / total_alerts) * 100
            print(f"  • {label}: {count:,} ({percentage:.1f}%)")
        
        print(f"\n📋 Alertas por status:")
        for status, label in Alert.STATUS_CHOICES:
            count = Alert.objects.filter(status=status).count()
            percentage = (count / total_alerts) * 100
            print(f"  • {label}: {count:,} ({percentage:.1f}%)")


def main():
    """Função principal."""
    
    print("\n")
    print("╔" + "═"*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "  SCRIPT DE GERAÇÃO MASSIVA DE DADOS".center(68) + "║")
    print("║" + f"  {TOTAL_EVENTS:,} Eventos + {TOTAL_ALERTS:,} Alertas".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "═"*68 + "╝")
    
    try:
        # 1. Verificar/criar alunos
        students = get_or_create_students(num_students=100)
        
        # 2. Verificar/criar sessão de exame
        exam_session = get_or_create_exam_session(students)
        
        # 3. Gerar eventos de monitoramento
        events = generate_monitoring_events(students, exam_session, TOTAL_EVENTS)
        
        # 4. Gerar alertas
        generate_alerts(events, students, TOTAL_ALERTS)
        
        # 5. Mostrar estatísticas
        show_statistics()
        
        print(f"\n{'='*70}")
        print("✅ PROCESSO CONCLUÍDO COM SUCESSO!")
        print(f"{'='*70}\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠ Processo interrompido pelo usuário.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Erro durante a execução: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

