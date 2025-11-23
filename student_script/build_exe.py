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
    
    print("=" * 60)
    print("  Compilando Monitor de Alunos para Executável")
    print("=" * 60)
    print()
    
    # Verificar se PyInstaller está instalado
    try:
        import PyInstaller
        print(f"✓ PyInstaller encontrado (versão {PyInstaller.__version__})")
    except ImportError:
        print("PyInstaller não encontrado. Instalando...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Verificar se o modelo existe
    model_path = Path(__file__).parent / 'face_detection_model' / 'yolov8m_200e.pt'
    if not model_path.exists():
        print(f"❌ ERRO: Modelo não encontrado em {model_path}")
        print("   O modelo YOLOv8 é essencial para o funcionamento!")
        return False
    
    print(f"✓ Modelo encontrado: {model_path}")
    print()
    
    # Preparar separador para Windows
    separator = ';' if sys.platform == 'win32' else ':'
    
    # Comando PyInstaller
    pyinstaller_cmd = [
        'pyinstaller',
        '--onedir',  # Usar --onedir por causa do modelo grande (198MB)
        '--console',  # COM console para ver logs e erros
        '--name=MonitorAluno',
        
        # Adicionar o modelo YOLOv8 (CRÍTICO!)
        f'--add-data=face_detection_model{separator}face_detection_model',
        
        # Adicionar arquivos de configuração e dados
        f'--add-data=url_bloqueadas.txt{separator}.',
        f'--add-data=student_config.json{separator}.' if Path('student_config.json').exists() else '',
        
        # Adicionar módulos Python necessários
        f'--add-data=api_client.py{separator}.',
        f'--add-data=browser_monitor.py{separator}.',
        f'--add-data=keyboard_monitor.py{separator}.',
        f'--add-data=display_monitor.py{separator}.',
        f'--add-data=screen_monitor.py{separator}.',
        f'--add-data=webcam_monitor.py{separator}.',
        f'--add-data=config.py{separator}.',
        
        # Hidden imports (bibliotecas que PyInstaller pode não detectar)
        '--hidden-import=win32gui',
        '--hidden-import=win32process',
        '--hidden-import=win32api',
        '--hidden-import=win32con',
        '--hidden-import=pywintypes',
        '--hidden-import=win32com',
        '--hidden-import=pynput',
        '--hidden-import=pynput.keyboard',
        '--hidden-import=pynput.mouse',
        '--hidden-import=screeninfo',
        '--hidden-import=cv2',
        '--hidden-import=ultralytics',
        '--hidden-import=torch',
        '--hidden-import=torchvision',
        '--hidden-import=omegaconf',  # CRÍTICO: Necessário para carregar modelos YOLOv8
        '--hidden-import=hydra',
        '--hidden-import=PIL',
        '--hidden-import=PIL.Image',
        '--hidden-import=PIL.ImageGrab',  # CRÍTICO para screen_monitor
        '--hidden-import=PIL.ImageDraw',
        '--hidden-import=PIL.ImageFont',
        '--hidden-import=PIL.ImageFilter',
        '--hidden-import=numpy',
        '--hidden-import=psutil',
        '--hidden-import=requests',
        '--hidden-import=websocket',
        '--hidden-import=websocket._app',
        '--hidden-import=websocket._core',
        
        # Coletar todos os submódulos necessários
        '--collect-all=ultralytics',
        '--collect-all=torch',
        '--collect-all=torchvision',
        '--collect-all=omegaconf',  # Coletar omegaconf completo
        '--collect-submodules=PIL',  # Coletar todos os submódulos do Pillow
        
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
        print("=" * 60)
        print("  ✓ Compilação concluída com sucesso!")
        print("=" * 60)
        print()
        print("📁 O executável está em: dist/MonitorAluno/")
        print("📄 Arquivo principal: dist/MonitorAluno/MonitorAluno.exe")
        print()
        print("⚠️  IMPORTANTE:")
        print("   - Distribua a PASTA COMPLETA 'MonitorAluno' (não apenas o .exe)")
        print("   - O modelo YOLOv8 está incluído na pasta 'face_detection_model'")
        print()
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao compilar: {e}")
        return False
    
    return True


if __name__ == '__main__':
    success = build_executable()
    sys.exit(0 if success else 1)

