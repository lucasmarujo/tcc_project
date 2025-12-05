"""
Script para compilar o monitor em executável usando PyInstaller.

Uso:
    python build_exe.py

O executável será criado na pasta 'dist/'.
"""
import os
import sys
import subprocess
from pathlib import Path

def build_executable():
    """Compila o script em executável."""
    
    print("=" * 70)
    print("  Compilando Monitor de Alunos para Executável")
    print("=" * 70)
    print()
    print("ATENÇÃO: Este processo pode demorar vários minutos.")
    print("O executável final pode ter 500MB+ devido aos modelos YOLO.")
    print()
    
    # Verificar se PyInstaller está instalado
    try:
        import PyInstaller
        print(f"✓ PyInstaller encontrado (versão {PyInstaller.__version__})")
    except ImportError:
        print("PyInstaller não encontrado. Instalando...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Comando PyInstaller otimizado
    pyinstaller_cmd = [
        'pyinstaller',
        '--onefile',  # Criar um único executável
        '--console',  # COM janela de console para ver logs
        '--name=MonitorAluno',  # Nome do executável
        # Adicionar arquivos de dados e módulos locais
        '--add-data=config.py;.',
        '--add-data=url_bloqueadas.txt;.',
        '--add-data=urls_permitidas.txt;.',
        '--add-data=face_detection_model;face_detection_model',
        # MÓDULOS LOCAIS DO PROJETO - CRÍTICO!
        '--add-data=browser_monitor.py;.',
        '--add-data=api_client.py;.',
        '--add-data=keyboard_monitor.py;.',
        '--add-data=display_monitor.py;.',
        '--add-data=webcam_monitor.py;.',
        '--add-data=screen_monitor.py;.',
        '--add-data=brightspace_detector.py;.',
        '--add-data=screen_analyzer.py;.',
        # Hidden imports dos módulos locais
        '--hidden-import=browser_monitor',
        '--hidden-import=api_client',
        '--hidden-import=keyboard_monitor',
        '--hidden-import=display_monitor',
        '--hidden-import=webcam_monitor',
        '--hidden-import=screen_monitor',
        '--hidden-import=brightspace_detector',
        '--hidden-import=screen_analyzer',
        '--hidden-import=config',
        # Hidden imports de bibliotecas externas
        '--hidden-import=win32gui',
        '--hidden-import=win32process',
        '--hidden-import=win32api',
        '--hidden-import=win32con',
        '--hidden-import=cv2',
        '--hidden-import=PIL',
        '--hidden-import=PIL.Image',
        '--hidden-import=numpy',
        '--hidden-import=ultralytics',
        '--hidden-import=torch',
        '--hidden-import=websocket',
        '--hidden-import=websocket._core',
        '--hidden-import=websocket._app',
        '--hidden-import=requests',
        '--hidden-import=psutil',
        '--hidden-import=pynput',
        '--hidden-import=pynput.keyboard',
        '--hidden-import=pynput.keyboard._win32',
        '--hidden-import=mss',
        '--hidden-import=screeninfo',
        '--hidden-import=screeninfo.enumerators',
        '--hidden-import=screeninfo.enumerators.windows',
        '--hidden-import=omegaconf',
        '--hidden-import=antlr4',
        '--hidden-import=yaml',
        # Coletar submodules
        '--collect-all=ultralytics',
        '--collect-all=torch',
        '--collect-all=cv2',
        '--collect-all=omegaconf',
        # Arquivo principal
        'monitor.py'
    ]
    
    # Remover strings vazias da lista
    pyinstaller_cmd = [cmd for cmd in pyinstaller_cmd if cmd]
    
    # Se icon.ico existe, adicionar
    if Path('icon.ico').exists():
        pyinstaller_cmd.insert(1, '--icon=icon.ico')
        print("✓ Ícone encontrado: icon.ico")
    
    print("Executando PyInstaller...")
    print(f"Comando: {' '.join(pyinstaller_cmd)}")
    print()
    print("⏳ Isso pode levar alguns minutos devido ao tamanho do modelo (198MB)...")
    print()
    
    try:
        subprocess.check_call(pyinstaller_cmd)
        
        print()
        print("=" * 70)
        print("  Compilação concluída com sucesso!")
        print("=" * 70)
        print()
        print("O executável está em: dist/MonitorAluno.exe")
        print()
        print("PRÓXIMOS PASSOS:")
        print("  1. Teste o executável: dist\\MonitorAluno.exe")
        print("  2. Verifique se todos os recursos funcionam corretamente")
        print("  3. Distribua o executável para os alunos")
        print()
        print("NOTA: O executável inclui:")
        print("  - Modelo YOLO de detecção facial")
        print("  - Lista de URLs bloqueadas")
        print("  - Todas as dependências necessárias")
        print()
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao compilar: {e}")
        return False
    
    return True


if __name__ == '__main__':
    success = build_executable()
    sys.exit(0 if success else 1)

