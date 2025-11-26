"""
Script de Treinamento usando YOLOv8 para Classificação
Classifica imagens entre 'permitido' e 'nao_permitido'
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from ultralytics import YOLO
import yaml
import shutil

# Adicionar pasta raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# ===========================
# CONFIGURAÇÕES
# ===========================
EPOCHS = 100
IMG_SIZE = 640
BATCH_SIZE = 16
MODEL_SIZE = 'n'
PATIENCE = 20
DATA_DIR = Path(__file__).parent.parent / "data"
MODELS_DIR = Path(__file__).parent / "models"
CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"

# Criar diretórios necessários
MODELS_DIR.mkdir(exist_ok=True)
(MODELS_DIR / "final_model").mkdir(exist_ok=True)

print("=" * 80)
print("🚀 INICIANDO TREINAMENTO DO MODELO YOLOv8 CLASSIFICATION")
print("=" * 80)
print(f"📊 Configurações:")
print(f"   - Modelo: YOLOv8{MODEL_SIZE}-cls")
print(f"   - Tamanho da imagem: {IMG_SIZE}x{IMG_SIZE}")
print(f"   - Batch size: {BATCH_SIZE}")
print(f"   - Epochs: {EPOCHS}")
print(f"   - Patience (Early Stopping): {PATIENCE}")
print(f"   - Diretório de dados: {DATA_DIR}")
print("=" * 80)

# ===========================
# VERIFICAR ESTRUTURA DE DADOS (dinâmica)
# ===========================
print("\n📁 Verificando estrutura de dados...")

# Detecta automaticamente se há subpasta 'train/'
if (DATA_DIR / "train").exists():
    base_dir = DATA_DIR / "train"
else:
    base_dir = DATA_DIR

permitido_dir = base_dir / "permitido"
nao_permitido_dir = base_dir / "nao_permitido"

if not permitido_dir.exists() or not nao_permitido_dir.exists():
    print("❌ ERRO: Estrutura de dados incorreta!")
    print(f"   Esperado: {base_dir}/permitido e {base_dir}/nao_permitido")
    sys.exit(1)

# Contagem de imagens
num_permitido = len(list(permitido_dir.glob("*.jpg"))) + len(list(permitido_dir.glob("*.png")))
num_nao_permitido = len(list(nao_permitido_dir.glob("*.jpg"))) + len(list(nao_permitido_dir.glob("*.png")))
total_images = num_permitido + num_nao_permitido

print(f"✅ Estrutura de dados verificada!")
print(f"   - Imagens 'permitido': {num_permitido}")
print(f"   - Imagens 'nao_permitido': {num_nao_permitido}")
print(f"   - Total de imagens: {total_images}")
print("=" * 80)

# ===========================
# CRIAR ARQUIVO DE CONFIGURAÇÃO YAML
# ===========================
print("\n📝 Criando arquivo de configuração...")

# Para YOLOv8 Classification, apenas precisamos do path
# As classes são detectadas automaticamente pelas subpastas
config_data = {
    'path': str(DATA_DIR.absolute()),
    'train': 'train',  # Caminho relativo
    'val': 'val',      # Caminho relativo
    'test': 'train'    # Usar train como test se não houver pasta test
}

with open(CONFIG_PATH, 'w') as f:
    yaml.dump(config_data, f, default_flow_style=False)

print(f"✅ Configuração salva em: {CONFIG_PATH}")
print(f"   Classes serão detectadas automaticamente das subpastas")

# ===========================
# INICIALIZAR MODELO
# ===========================
print("\n🤖 Inicializando modelo YOLOv8...")

model_name = f'yolov8{MODEL_SIZE}-cls.pt'
model = YOLO(model_name)

print(f"✅ Modelo {model_name} carregado!")

# ===========================
# TREINAMENTO
# ===========================
start_time = datetime.now()
print(f"\n⏰ Início do treinamento: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)
print("🏋️ Treinando... (isso pode levar alguns minutos)")
print("=" * 80)

try:
    results = model.train(
        data=str(DATA_DIR),
        epochs=EPOCHS,
        imgsz=IMG_SIZE,
        batch=BATCH_SIZE,
        patience=PATIENCE,
        save=True,
        project=str(MODELS_DIR),
        name='training_run',
        exist_ok=True,
        pretrained=True,
        optimizer='auto',
        verbose=True,
        seed=42,
        deterministic=False,
        single_cls=False,
        rect=False,
        cos_lr=False,
        close_mosaic=0,
        resume=False,
        amp=True,
        fraction=1.0,
        profile=False,
        freeze=None,
        multi_scale=False,
        overlap_mask=True,
        mask_ratio=4,
        dropout=0.0,
        val=True,
        split='val',
        save_period=-1,
        cache=False,
        device=None,
        workers=8,
        plots=True,
    )
    
    end_time = datetime.now()
    training_duration = end_time - start_time
    
    print("\n" + "=" * 80)
    print("✅ TREINAMENTO CONCLUÍDO COM SUCESSO!")
    print("=" * 80)
    
    # ===========================
    # SALVAR MODELO FINAL
    # ===========================
    print("\n💾 Salvando modelo final...")

    best_model_path = MODELS_DIR / "training_run" / "weights" / "best.pt"
    final_model_path = MODELS_DIR / "final_model" / "best.pt"
    
    if best_model_path.exists():
        shutil.copy(best_model_path, final_model_path)
        print(f"✅ Modelo final salvo em: {final_model_path}")
    else:
        print(f"⚠️  Aviso: Modelo 'best.pt' não encontrado em {best_model_path}")
    
    # ===========================
    # GERAR RELATÓRIO
    # ===========================
    print("\n📝 Gerando relatório de treinamento...")

    metrics = results.results_dict if hasattr(results, 'results_dict') else {}
    
    report = f"""
{'=' * 80}
                    RELATÓRIO DE TREINAMENTO - YOLOv8 CLASSIFICATION
{'=' * 80}

📅 DATA E HORA
   Início:   {start_time.strftime('%Y-%m-%d %H:%M:%S')}
   Término:  {end_time.strftime('%Y-%m-%d %H:%M:%S')}
   Duração:  {training_duration}

📊 CONFIGURAÇÕES
   Modelo:                YOLOv8{MODEL_SIZE}-cls
   Tamanho da Imagem:     {IMG_SIZE}x{IMG_SIZE}
   Batch Size:            {BATCH_SIZE}
   Epochs Configurados:   {EPOCHS}
   Patience:              {PATIENCE}
   Otimizador:            Auto (AdamW)
   Device:                Auto (CUDA se disponível)

📁 DATASET
   Imagens 'permitido':      {num_permitido}
   Imagens 'nao_permitido':  {num_nao_permitido}
   Total de Imagens:         {total_images}
   Diretório usado:          {base_dir}

🎯 RESULTADOS FINAIS
   Acurácia (Top1):       {metrics.get('metrics/accuracy_top1', 'N/A')}
   Acurácia (Top5):       {metrics.get('metrics/accuracy_top5', 'N/A')}
   Loss (Treino):         {metrics.get('train/loss', 'N/A')}
   Loss (Validação):      {metrics.get('val/loss', 'N/A')}

📂 ARQUIVOS GERADOS
   Modelo Final:          {final_model_path}
   Diretório Completo:    {MODELS_DIR / 'training_run'}
   Gráficos:              {MODELS_DIR / 'training_run' / 'results.png'}
   Configuração:          {CONFIG_PATH}

📝 OBSERVAÇÕES
   - YOLOv8 aplica data augmentation automaticamente
   - Early stopping configurado com patience={PATIENCE}
   - Modelo utiliza transfer learning de pesos pré-treinados
   - Métricas detalhadas disponíveis em: {MODELS_DIR / 'training_run' / 'results.csv'}

💡 PRÓXIMOS PASSOS
   1. Avaliar modelo: python scripts/evaluate.py
   2. Fazer predições: python scripts/predict.py
   3. Verificar gráficos em: {MODELS_DIR / 'training_run'}

{'=' * 80}
"""
    
    report_path = MODELS_DIR / "final_model" / "training_report.txt"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(report)
    print(f"📄 Relatório salvo em: {report_path}")
    print("=" * 80)
    print("✨ PROCESSO COMPLETO!")
    print("=" * 80)

except Exception as e:
    print(f"\n❌ ERRO durante o treinamento: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
