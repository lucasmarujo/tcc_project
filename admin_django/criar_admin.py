"""
Script para criar usuários administradores no Django.
Solicita username e senha e cria um superusuário.
"""
import os
import sys
import django
import getpass

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User


def criar_administrador():
    """Cria um usuário administrador."""
    
    print("=" * 60)
    print("  CRIAR USUÁRIO ADMINISTRADOR")
    print("=" * 60)
    print()
    
    # Solicitar username
    while True:
        username = input("Digite o username: ").strip()
        
        if not username:
            print("❌ O username não pode estar vazio!")
            continue
        
        # Verificar se o usuário já existe
        if User.objects.filter(username=username).exists():
            print(f"❌ O usuário '{username}' já existe!")
            resposta = input("Deseja tentar outro username? (s/n): ").strip().lower()
            if resposta != 's':
                print("Operação cancelada.")
                return
            continue
        
        break
    
    # Solicitar senha
    while True:
        senha = getpass.getpass("Digite a senha: ")
        
        if not senha:
            print("❌ A senha não pode estar vazia!")
            continue
        
        senha_confirmacao = getpass.getpass("Confirme a senha: ")
        
        if senha != senha_confirmacao:
            print("❌ As senhas não coincidem! Tente novamente.")
            continue
        
        if len(senha) < 6:
            print("❌ A senha deve ter pelo menos 6 caracteres!")
            continue
        
        break
    
    # Criar o superusuário
    try:
        user = User.objects.create_superuser(
            username=username,
            password=senha,
            email=''  # Email opcional
        )
        
        print()
        print("=" * 60)
        print("✅ ADMINISTRADOR CRIADO COM SUCESSO!")
        print("=" * 60)
        print()
        print(f"  Username: {user.username}")
        print(f"  É superusuário: Sim")
        print(f"  É staff: Sim")
        print()
        print("Você já pode acessar o admin com essas credenciais:")
        print("  http://localhost:8000/admin")
        print()
        
    except Exception as e:
        print()
        print("❌ Erro ao criar administrador:")
        print(f"  {str(e)}")
        print()
        sys.exit(1)


def main():
    """Função principal."""
    
    try:
        criar_administrador()
    except KeyboardInterrupt:
        print()
        print()
        print("Operação cancelada pelo usuário.")
        sys.exit(0)
    except Exception as e:
        print()
        print(f"❌ Erro inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

