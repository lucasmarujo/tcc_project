"""
Script para verificar se o ambiente está pronto para build.
"""
import sys
import os
from pathlib import Path

def check_dependencies():
    """Verifica se todas as dependências estão instaladas."""
    print("Verificando dependências...")
    
    required = [
        'pyinstaller',
        'cv2',
        'PIL',
        'numpy',
        'ultralytics',
        'torch',
        'websocket',
        'requests',
        'psutil',
        'pynput',
    ]
    
    optional = [
        'mss',
        'win32gui',
    ]
    
    missing = []
    optional_missing = []
    
    for module in required:
        try:
            __import__(module if module != 'cv2' else 'cv2')
            print(f"  ✓ {module}")
        except ImportError:
            print(f"  ✗ {module} - FALTANDO")
            missing.append(module)
    
    for module in optional:
        try:
            __import__(module)
            print(f"  ✓ {module} (opcional)")
        except ImportError:
            print(f"  ⚠ {module} (opcional) - não encontrado")
            optional_missing.append(module)
    
    return missing, optional_missing


def check_files():
    """Verifica se todos os arquivos necessários existem."""
    print("\nVerificando arquivos...")
    
    files = [
        'monitor.py',
        'config.py',
        'url_bloqueadas.txt',
        'browser_monitor.py',
        'webcam_monitor.py',
        'screen_monitor.py',
        'api_client.py',
        'keyboard_monitor.py',
        'face_detection_model/yolov8m_200e.pt',
    ]
    
    missing = []
    
    for file in files:
        file_path = Path(file)
        if file_path.exists():
            size = file_path.stat().st_size
            print(f"  ✓ {file} ({size // 1024} KB)")
        else:
            print(f"  ✗ {file} - FALTANDO")
            missing.append(file)
    
    return missing


def check_space():
    """Verifica espaço em disco."""
    print("\nVerificando espaço em disco...")
    
    import shutil
    total, used, free = shutil.disk_usage(".")
    
    free_gb = free // (1024 ** 3)
    print(f"  Espaço livre: {free_gb} GB")
    
    if free_gb < 5:
        print("  ⚠ AVISO: Pouco espaço em disco (recomendado: 5GB+)")
        return False
    else:
        print("  ✓ Espaço suficiente")
        return True


def main():
    print("\n" + "=" * 70)
    print("VERIFICAÇÃO DE AMBIENTE PARA BUILD")
    print("=" * 70 + "\n")
    
    # Verificar dependências
    missing_deps, optional_missing = check_dependencies()
    
    # Verificar arquivos
    missing_files = check_files()
    
    # Verificar espaço
    has_space = check_space()
    
    # Resumo
    print("\n" + "=" * 70)
    print("RESUMO")
    print("=" * 70)
    
    all_good = True
    
    if missing_deps:
        print(f"\n✗ DEPENDÊNCIAS FALTANDO: {', '.join(missing_deps)}")
        print(f"   Instalar com: pip install {' '.join(missing_deps)}")
        all_good = False
    else:
        print("\n✓ Todas as dependências obrigatórias instaladas")
    
    if optional_missing:
        print(f"\n⚠ Dependências opcionais faltando: {', '.join(optional_missing)}")
        print(f"   (opcional) pip install {' '.join(optional_missing)}")
    
    if missing_files:
        print(f"\n✗ ARQUIVOS FALTANDO: {', '.join(missing_files)}")
        all_good = False
    else:
        print("✓ Todos os arquivos necessários presentes")
    
    if not has_space:
        print("\n⚠ Pouco espaço em disco disponível")
    
    print()
    
    if all_good:
        print("=" * 70)
        print("✓ AMBIENTE PRONTO PARA BUILD!")
        print("=" * 70)
        print("\nPróximos passos:")
        print("  1. Execute: python build_exe.py")
        print("  2. Ou siga as instruções em: COMO_GERAR_EXE.md")
        print()
        return 0
    else:
        print("=" * 70)
        print("✗ AMBIENTE NÃO ESTÁ PRONTO")
        print("=" * 70)
        print("\nCorreja os problemas acima antes de continuar.")
        print()
        return 1


if __name__ == '__main__':
    sys.exit(main())

