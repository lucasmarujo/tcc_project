"""
Script de Predição usando YOLOv8 Classification
Faz predições em imagens individuais ou em lote
"""

import os
import sys
from pathlib import Path
from ultralytics import YOLO
from PIL import Image
import tkinter as tk
from tkinter import filedialog
import cv2
import numpy as np

# Adicionar pasta raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# ===========================
# CONFIGURAÇÕES
# ===========================
MODELS_DIR = Path(__file__).parent / "models"
MODEL_PATH = MODELS_DIR / "final_model" / "best.pt"

# Classes do modelo
CLASSES = {
    0: 'nao_permitido',
    1: 'permitido'
}

print("=" * 80)
print("🔮 PREDIÇÃO COM YOLOv8 CLASSIFICATION")
print("=" * 80)

# ===========================
# CARREGAR MODELO
# ===========================
print("\n🤖 Carregando modelo...")

if not MODEL_PATH.exists():
    print(f"❌ ERRO: Modelo não encontrado em {MODEL_PATH}")
    print("   Execute primeiro: python scripts/train.py")
    sys.exit(1)

try:
    model = YOLO(str(MODEL_PATH))
    print(f"✅ Modelo carregado com sucesso de: {MODEL_PATH}")
except Exception as e:
    print(f"❌ ERRO ao carregar modelo: {str(e)}")
    sys.exit(1)

# ===========================
# FUNÇÕES DE PREDIÇÃO
# ===========================

def predict_image(image_path, verbose=True):
    """
    Faz predição em uma única imagem
    
    Args:
        image_path: Caminho para a imagem
        verbose: Se True, exibe informações detalhadas
        
    Returns:
        tuple: (classe_nome, confiança, classe_id)
    """
    try:
        # Fazer predição
        results = model.predict(
            source=str(image_path),
            verbose=False,
            conf=0.25,
            save=False,
            show=False
        )
        
        # Extrair resultado
        result = results[0]
        
        # Obter a classe com maior probabilidade
        probs = result.probs
        top1_idx = int(probs.top1)
        top1_conf = float(probs.top1conf)
        
        # Nome da classe
        class_name = CLASSES.get(top1_idx, f'class_{top1_idx}')
        
        if verbose:
            print(f"\n{'=' * 60}")
            print(f"📁 Imagem: {Path(image_path).name}")
            print(f"🎯 Classe: {class_name.upper()}")
            print(f"📊 Confiança: {top1_conf * 100:.2f}%")
            
            # Mostrar todas as probabilidades
            if hasattr(probs, 'data'):
                print(f"\n📈 Probabilidades:")
                for idx, prob in enumerate(probs.data.cpu().numpy()):
                    class_label = CLASSES.get(idx, f'class_{idx}')
                    print(f"   {class_label}: {prob * 100:.2f}%")
            
            print(f"{'=' * 60}")
        
        return class_name, top1_conf, top1_idx
        
    except Exception as e:
        print(f"❌ ERRO ao processar imagem: {str(e)}")
        return None, 0.0, -1


def predict_with_visualization(image_path):
    """
    Faz predição e mostra a imagem com o resultado
    
    Args:
        image_path: Caminho para a imagem
    """
    class_name, confidence, class_id = predict_image(image_path, verbose=True)
    
    if class_name is None:
        return
    
    # Carregar e mostrar imagem
    try:
        img = cv2.imread(str(image_path))
        if img is None:
            print(f"⚠️  Aviso: Não foi possível carregar a imagem para visualização")
            return
        
        # Redimensionar se for muito grande
        height, width = img.shape[:2]
        max_dimension = 800
        if max(height, width) > max_dimension:
            scale = max_dimension / max(height, width)
            new_width = int(width * scale)
            new_height = int(height * scale)
            img = cv2.resize(img, (new_width, new_height))
        
        # Adicionar texto com resultado
        label = f"{class_name.upper()}: {confidence * 100:.1f}%"
        color = (0, 255, 0) if class_name == 'permitido' else (0, 0, 255)
        
        # Fundo para o texto
        (text_width, text_height), baseline = cv2.getTextSize(
            label, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 2
        )
        cv2.rectangle(img, (10, 10), (20 + text_width, 30 + text_height), (0, 0, 0), -1)
        
        # Texto
        cv2.putText(img, label, (15, 35), cv2.FONT_HERSHEY_SIMPLEX, 
                   1.0, color, 2, cv2.LINE_AA)
        
        # Mostrar imagem
        cv2.imshow('Predição YOLOv8', img)
        print("\n💡 Pressione qualquer tecla para fechar a janela...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
    except Exception as e:
        print(f"⚠️  Erro na visualização: {str(e)}")


def predict_batch(directory_path):
    """
    Faz predições em todas as imagens de um diretório
    
    Args:
        directory_path: Caminho para o diretório com imagens
    """
    directory = Path(directory_path)
    
    # Extensões suportadas
    extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']
    
    # Encontrar todas as imagens
    image_files = []
    for ext in extensions:
        image_files.extend(list(directory.glob(f'*{ext}')))
        image_files.extend(list(directory.glob(f'*{ext.upper()}')))
    
    if not image_files:
        print(f"❌ Nenhuma imagem encontrada em: {directory_path}")
        return
    
    print(f"\n📁 Encontradas {len(image_files)} imagens")
    print("=" * 80)
    
    results_summary = {
        'permitido': 0,
        'nao_permitido': 0,
        'total': len(image_files)
    }
    
    # Processar cada imagem
    for i, image_path in enumerate(image_files, 1):
        print(f"\n[{i}/{len(image_files)}] Processando: {image_path.name}")
        class_name, confidence, _ = predict_image(image_path, verbose=False)
        
        if class_name:
            results_summary[class_name] += 1
            print(f"   ✅ {class_name.upper()} ({confidence * 100:.1f}%)")
        else:
            print(f"   ❌ Erro ao processar")
    
    # Resumo
    print("\n" + "=" * 80)
    print("📊 RESUMO DAS PREDIÇÕES")
    print("=" * 80)
    print(f"Total de imagens:      {results_summary['total']}")
    print(f"Permitido:             {results_summary['permitido']} ({results_summary['permitido']/results_summary['total']*100:.1f}%)")
    print(f"Não permitido:         {results_summary['nao_permitido']} ({results_summary['nao_permitido']/results_summary['total']*100:.1f}%)")
    print("=" * 80)


# ===========================
# INTERFACE INTERATIVA
# ===========================

def select_file():
    """Abre diálogo para selecionar arquivo"""
    root = tk.Tk()
    root.withdraw()
    
    file_path = filedialog.askopenfilename(
        title="Selecione uma imagem",
        filetypes=[
            ("Imagens", "*.jpg *.jpeg *.png *.bmp *.gif *.webp"),
            ("Todos os arquivos", "*.*")
        ]
    )
    
    return file_path


def select_directory():
    """Abre diálogo para selecionar diretório"""
    root = tk.Tk()
    root.withdraw()
    
    dir_path = filedialog.askdirectory(
        title="Selecione um diretório com imagens"
    )
    
    return dir_path


# ===========================
# MENU PRINCIPAL
# ===========================

if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("ESCOLHA UMA OPÇÃO:")
    print("=" * 80)
    print("1. Predizer uma única imagem (com visualização)")
    print("2. Predizer uma única imagem (apenas resultado)")
    print("3. Predizer todas as imagens de um diretório")
    print("4. Sair")
    print("=" * 80)
    
    choice = input("\nDigite o número da opção: ").strip()
    
    if choice == '1':
        print("\n🔍 Selecione uma imagem...")
        img_path = select_file()
        
        if not img_path:
            print("❌ Nenhuma imagem selecionada. Encerrando...")
        else:
            predict_with_visualization(img_path)
    
    elif choice == '2':
        print("\n🔍 Selecione uma imagem...")
        img_path = select_file()
        
        if not img_path:
            print("❌ Nenhuma imagem selecionada. Encerrando...")
        else:
            predict_image(img_path, verbose=True)
    
    elif choice == '3':
        print("\n📁 Selecione um diretório...")
        dir_path = select_directory()
        
        if not dir_path:
            print("❌ Nenhum diretório selecionado. Encerrando...")
        else:
            predict_batch(dir_path)
    
    elif choice == '4':
        print("\n👋 Até logo!")
    
    else:
        print("\n❌ Opção inválida!")
    
    print("\n" + "=" * 80)
