"""
Script para compilar o monitor em executável usando PyInstaller.

Uso:
    python build_exe.py

O executável será criado na pasta 'dist/'.
"""
import os
import sys
import subprocess

def build_executable():
    """Compila o script em executável."""
    
    print("=" * 60)
    print("  Compilando Monitor de Alunos para Executável")
    print("=" * 60)
    print()
    
    # Verificar se PyInstaller está instalado
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller não encontrado. Instalando...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Comando PyInstaller
    pyinstaller_cmd = [
        'pyinstaller',
        '--onefile',  # Criar um único executável
        '--noconsole',  # Sem janela de console (opcional, remover se quiser ver logs)
        '--name=MonitorAluno',  # Nome do executável
        '--icon=icon.ico',  # Ícone (opcional, criar um icon.ico)
        '--add-data=config.py;.',  # Incluir config
        '--hidden-import=win32gui',
        '--hidden-import=win32process',
        '--hidden-import=win32api',
        '--hidden-import=win32con',
        'monitor.py'
    ]
    
    print("Executando PyInstaller...")
    print(f"Comando: {' '.join(pyinstaller_cmd)}")
    print()
    
    try:
        # Se icon.ico não existe, remover a opção
        if not os.path.exists('icon.ico'):
            pyinstaller_cmd = [cmd for cmd in pyinstaller_cmd if not cmd.startswith('--icon')]
        
        subprocess.check_call(pyinstaller_cmd)
        
        print()
        print("=" * 60)
        print("  Compilação concluída com sucesso!")
        print("=" * 60)
        print()
        print("O executável está em: dist/MonitorAluno.exe")
        print()
        
    except subprocess.CalledProcessError as e:
        print(f"Erro ao compilar: {e}")
        return False
    
    return True


if __name__ == '__main__':
    success = build_executable()
    sys.exit(0 if success else 1)

