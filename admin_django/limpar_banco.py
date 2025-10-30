"""
Script para limpar o banco de dados mantendo apenas o usuário admin.
ATENÇÃO: Este script deleta TODOS os dados de alunos, eventos e alertas!
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from students.models import Student, ExamSession
from monitoring.models import MonitoringEvent, Alert


def confirmar_limpeza():
    """Pede confirmação do usuário antes de limpar."""
    print("=" * 70)
    print("  LIMPEZA DO BANCO DE DADOS")
    print("=" * 70)
    print()
    print("ATENÇÃO! Este script irá DELETAR:")
    print("  - Todos os eventos de monitoramento")
    print("  - Todos os alertas")
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


def limpar_banco():
    """Limpa todos os dados do banco, mantendo apenas usuários admin."""
    
    print("\nIniciando limpeza...\n")
    
    # 1. Deletar todos os alertas
    total_alertas = Alert.objects.count()
    Alert.objects.all().delete()
    print(f"[OK] {total_alertas} alertas deletados")
    
    # 2. Deletar todos os eventos de monitoramento
    total_eventos = MonitoringEvent.objects.count()
    MonitoringEvent.objects.all().delete()
    print(f"[OK] {total_eventos} eventos deletados")
    
    # 3. Deletar todas as sessões de exame
    total_sessoes = ExamSession.objects.count()
    ExamSession.objects.all().delete()
    print(f"[OK] {total_sessoes} sessões de exame deletadas")
    
    # 4. Deletar todos os alunos
    total_alunos = Student.objects.count()
    Student.objects.all().delete()
    print(f"[OK] {total_alunos} alunos deletados")
    
    # 5. Verificar usuários admin mantidos
    total_admins = User.objects.filter(is_superuser=True).count()
    print(f"[OK] {total_admins} usuário(s) admin mantidos")
    
    print("\n" + "=" * 70)
    print("  LIMPEZA CONCLUÍDA COM SUCESSO!")
    print("=" * 70)
    print()
    print("Resumo:")
    print(f"  - Alertas deletados: {total_alertas}")
    print(f"  - Eventos deletados: {total_eventos}")
    print(f"  - Sessões de exame deletadas: {total_sessoes}")
    print(f"  - Alunos deletados: {total_alunos}")
    print(f"  - Admins mantidos: {total_admins}")
    print()
    print("O banco de dados foi resetado e está pronto para novos dados.")
    print()


def main():
    """Função principal."""
    try:
        if confirmar_limpeza():
            limpar_banco()
        else:
            print("\n[CANCELADO] Limpeza cancelada pelo usuário.\n")
            sys.exit(0)
    except Exception as e:
        print(f"\n[ERRO] Ocorreu um erro durante a limpeza: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

