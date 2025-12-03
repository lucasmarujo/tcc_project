"""
Script para limpar o banco de dados mantendo apenas o usuário admin.
ATENÇÃO: Este script deleta TODOS os dados de alunos, eventos e alertas!

Otimizado para grandes volumes de dados (500k+ registros).
"""
import os
import sys
import django
from time import time

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from django.db import connection, transaction
from students.models import Student, ExamSession
from monitoring.models import MonitoringEvent, Alert


# Tamanho do lote para deleção em batch (quando necessário)
BATCH_SIZE = 10_000


def confirmar_limpeza():
    """Pede confirmação do usuário antes de limpar."""
    print("=" * 70)
    print("  LIMPEZA DO BANCO DE DADOS (OTIMIZADA)")
    print("=" * 70)
    print()
    print("ATENÇÃO! Este script irá DELETAR:")
    print("  - Todos os alertas")
    print("  - Todos os eventos de monitoramento")
    print("  - Todas as sessões de exame")
    print("  - Todos os alunos cadastrados")
    print()
    print("SERÁ MANTIDO apenas:")
    print("  - Usuário(s) administrador(es)")
    print()
    print("=" * 70)
    print()
    
    resposta = input("Tem certeza que deseja continuar? Digite 'SIM' para confirmar: ")
    return resposta.strip().upper() == 'SIM'


def delete_table_fast(table_name, model_class=None):
    """
    Deleta todos os registros de uma tabela de forma otimizada.
    Usa DELETE direto no SQL para máxima performance.
    """
    # Contar registros antes
    if model_class:
        total = model_class.objects.count()
    else:
        with connection.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            total = cursor.fetchone()[0]
    
    if total == 0:
        return 0
    
    start_time = time()
    
    # Usar DELETE direto no SQL (muito mais rápido que ORM)
    with connection.cursor() as cursor:
        cursor.execute(f"DELETE FROM {table_name}")
    
    elapsed = time() - start_time
    speed = total / elapsed if elapsed > 0 else total
    
    print(f"  ✓ {table_name}: {total:,} registros deletados em {elapsed:.2f}s ({speed:,.0f}/s)")
    
    return total


def delete_in_batches(model_class, table_name, batch_size=BATCH_SIZE):
    """
    Deleta registros em lotes (fallback se DELETE direto falhar).
    """
    total = model_class.objects.count()
    if total == 0:
        return 0
    
    print(f"  Deletando {total:,} registros de {table_name} em lotes...")
    
    start_time = time()
    deleted_count = 0
    batch_num = 0
    
    while True:
        # Buscar IDs do próximo lote
        ids = list(model_class.objects.values_list('pk', flat=True)[:batch_size])
        
        if not ids:
            break
        
        # Deletar lote
        with transaction.atomic():
            model_class.objects.filter(pk__in=ids).delete()
        
        deleted_count += len(ids)
        batch_num += 1
        
        # Mostrar progresso a cada 5 lotes
        if batch_num % 5 == 0:
            progress = (deleted_count / total) * 100
            elapsed = time() - start_time
            speed = deleted_count / elapsed if elapsed > 0 else 0
            print(f"    Progresso: {progress:.1f}% ({deleted_count:,}/{total:,}) - {speed:,.0f}/s")
    
    elapsed = time() - start_time
    speed = deleted_count / elapsed if elapsed > 0 else deleted_count
    print(f"  ✓ {table_name}: {deleted_count:,} registros deletados em {elapsed:.2f}s ({speed:,.0f}/s)")
    
    return deleted_count


def limpar_banco():
    """Limpa todos os dados do banco de forma otimizada."""
    
    print("\n" + "=" * 70)
    print("INICIANDO LIMPEZA OTIMIZADA")
    print("=" * 70 + "\n")
    
    total_start = time()
    stats = {}
    
    # ================================================================
    # IMPORTANTE: Ordem de deleção respeitando foreign keys
    # 1. Alertas (depende de MonitoringEvent e Student)
    # 2. Eventos de Monitoramento (depende de Student e ExamSession)
    # 3. Relação ManyToMany ExamSession <-> Student
    # 4. Sessões de Exame
    # 5. StudentHeartbeat (depende de Student)
    # 6. Alunos
    # ================================================================
    
    print("Fase 1: Deletando Alertas...")
    stats['alertas'] = delete_table_fast('alerts', Alert)
    
    print("\nFase 2: Deletando Eventos de Monitoramento...")
    stats['eventos'] = delete_table_fast('monitoring_events', MonitoringEvent)
    
    print("\nFase 3: Deletando relação Sessões-Alunos...")
    # Tabela intermediária do ManyToMany
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM exam_sessions_students")
        count = cursor.fetchone()[0]
    if count > 0:
        start = time()
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM exam_sessions_students")
        elapsed = time() - start
        print(f"  ✓ exam_sessions_students: {count:,} registros deletados em {elapsed:.2f}s")
    else:
        print(f"  ✓ exam_sessions_students: 0 registros")
    stats['sessoes_alunos'] = count
    
    print("\nFase 4: Deletando Sessões de Exame...")
    stats['sessoes'] = delete_table_fast('exam_sessions', ExamSession)
    
    print("\nFase 5: Deletando Heartbeats...")
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM student_heartbeats")
        count = cursor.fetchone()[0]
    if count > 0:
        start = time()
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM student_heartbeats")
        elapsed = time() - start
        print(f"  ✓ student_heartbeats: {count:,} registros deletados em {elapsed:.2f}s")
    else:
        print(f"  ✓ student_heartbeats: 0 registros")
    stats['heartbeats'] = count
    
    print("\nFase 6: Deletando Alunos...")
    stats['alunos'] = delete_table_fast('students', Student)
    
    # Verificar usuários admin mantidos
    total_admins = User.objects.filter(is_superuser=True).count()
    
    total_elapsed = time() - total_start
    
    # ================================================================
    # VACUUM para liberar espaço no SQLite (opcional mas recomendado)
    # ================================================================
    print("\nFase 7: Otimizando banco de dados (VACUUM)...")
    try:
        start = time()
        with connection.cursor() as cursor:
            cursor.execute("VACUUM")
        vacuum_time = time() - start
        print(f"  ✓ VACUUM concluído em {vacuum_time:.2f}s")
    except Exception as e:
        print(f"  ⚠ VACUUM não executado: {e}")
    
    # ================================================================
    # Resumo Final
    # ================================================================
    print("\n" + "=" * 70)
    print("  LIMPEZA CONCLUÍDA COM SUCESSO!")
    print("=" * 70)
    print()
    print("📊 Resumo:")
    print(f"  • Alertas deletados: {stats['alertas']:,}")
    print(f"  • Eventos deletados: {stats['eventos']:,}")
    print(f"  • Relações sessão-aluno: {stats['sessoes_alunos']:,}")
    print(f"  • Sessões de exame: {stats['sessoes']:,}")
    print(f"  • Heartbeats: {stats['heartbeats']:,}")
    print(f"  • Alunos deletados: {stats['alunos']:,}")
    print(f"  • Admins mantidos: {total_admins}")
    print()
    
    total_deleted = sum(stats.values())
    print(f"⏱️  Tempo total: {total_elapsed:.2f}s")
    print(f"📈 Total deletado: {total_deleted:,} registros")
    if total_elapsed > 0:
        print(f"🚀 Velocidade média: {total_deleted/total_elapsed:,.0f} registros/s")
    print()
    print("✅ O banco de dados foi resetado e está pronto para novos dados.")
    print()


def main():
    """Função principal."""
    try:
        if confirmar_limpeza():
            limpar_banco()
        else:
            print("\n[CANCELADO] Limpeza cancelada pelo usuário.\n")
            sys.exit(0)
    except KeyboardInterrupt:
        print("\n\n⚠ Processo interrompido pelo usuário.")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERRO] Ocorreu um erro durante a limpeza: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
