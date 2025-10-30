"""
Script de Limpeza - Remove arquivos obsoletos do TensorFlow
Execute este script para limpar completamente os artefatos antigos
"""

import os
import shutil
from pathlib import Path

print("=" * 80)
print("LIMPEZA DE ARQUIVOS OBSOLETOS DO TENSORFLOW")
print("=" * 80)

# Diretório raiz
ROOT_DIR = Path(__file__).parent

# Arquivos e diretórios para remover
TO_REMOVE = [
    # Modelos antigos TensorFlow
    "scripts/models/checkpoints/model_01.h5",
    "scripts/models/checkpoints/model_03.h5",
    "scripts/models/checkpoints/model_04.h5",
    "scripts/models/final_model/model.h5",
    "scripts/models/final_model/analysis_report.txt",
    "scripts/models/final_model/training_report.txt",
    
    # Diretórios de cache Python
    "utils/__pycache__",
    "scripts/__pycache__",
    "__pycache__",
]

removed_count = 0
kept_count = 0

for item in TO_REMOVE:
    full_path = ROOT_DIR / item
    
    try:
        if full_path.exists():
            if full_path.is_file():
                full_path.unlink()
                print(f"[OK] Removido arquivo: {item}")
                removed_count += 1
            elif full_path.is_dir():
                shutil.rmtree(full_path)
                print(f"[OK] Removido diretorio: {item}")
                removed_count += 1
        else:
            print(f"[SKIP] Nao encontrado: {item}")
            kept_count += 1
    except Exception as e:
        print(f"[ERRO] Erro ao remover {item}: {e}")

print("\n" + "=" * 80)
print("RESUMO")
print("=" * 80)
print(f"Removidos: {removed_count}")
print(f"Nao encontrados: {kept_count}")
print("\nAgora voce pode treinar um novo modelo com YOLOv8!")
print("Execute: cd scripts && python train.py")
print("=" * 80)

