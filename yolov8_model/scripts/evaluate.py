"""
Script de Avaliação usando YOLOv8 Classification
Avalia o modelo treinado e gera relatórios detalhados
"""

import os
import sys
from pathlib import Path
from ultralytics import YOLO
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from datetime import datetime
import json

# Adicionar pasta raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# ===========================
# CONFIGURAÇÕES
# ===========================
MODELS_DIR = Path(__file__).parent / "models"
MODEL_PATH = MODELS_DIR / "final_model" / "best.pt"
DATA_DIR = Path(__file__).parent.parent / "data"
RESULTS_DIR = MODELS_DIR / "final_model"

# Classes do modelo
CLASSES = {
    0: 'nao_permitido',
    1: 'permitido'
}

print("=" * 80)
print("📊 AVALIAÇÃO DO MODELO YOLOv8 CLASSIFICATION")
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
# AVALIAR DATASET
# ===========================
print("\n📁 Avaliando dataset de validação...")
print("=" * 80)

# Coletar predições e ground truth
predictions = []
ground_truth = []
confidences = []
file_names = []

# Processar cada classe
for class_id, class_name in CLASSES.items():
    class_dir = DATA_DIR / class_name
    
    if not class_dir.exists():
        print(f"⚠️  Aviso: Diretório {class_dir} não encontrado")
        continue
    
    # Encontrar todas as imagens
    extensions = ['.jpg', '.jpeg', '.png', '.bmp']
    image_files = []
    for ext in extensions:
        image_files.extend(list(class_dir.glob(f'*{ext}')))
        image_files.extend(list(class_dir.glob(f'*{ext.upper()}')))
    
    print(f"\n📂 Processando classe '{class_name}': {len(image_files)} imagens")
    
    for image_path in image_files:
        try:
            # Fazer predição
            results = model.predict(
                source=str(image_path),
                verbose=False,
                conf=0.0,  # Sem threshold para avaliação completa
                save=False,
                show=False
            )
            
            result = results[0]
            probs = result.probs
            
            # Obter predição
            pred_class = int(probs.top1)
            pred_conf = float(probs.top1conf)
            
            # Armazenar resultados
            predictions.append(pred_class)
            ground_truth.append(class_id)
            confidences.append(pred_conf)
            file_names.append(image_path.name)
            
        except Exception as e:
            print(f"   ⚠️  Erro ao processar {image_path.name}: {str(e)}")
            continue

print("\n" + "=" * 80)
print(f"✅ Avaliação concluída: {len(predictions)} imagens processadas")

# ===========================
# CALCULAR MÉTRICAS
# ===========================
print("\n📈 Calculando métricas...")

predictions = np.array(predictions)
ground_truth = np.array(ground_truth)
confidences = np.array(confidences)

# Acurácia geral
accuracy = np.mean(predictions == ground_truth)

# Métricas por classe
metrics_per_class = {}
confusion_matrix = np.zeros((len(CLASSES), len(CLASSES)), dtype=int)

for class_id, class_name in CLASSES.items():
    # Máscara para esta classe
    mask = ground_truth == class_id
    
    if not mask.any():
        continue
    
    # Predições para esta classe
    class_preds = predictions[mask]
    class_gt = ground_truth[mask]
    
    # True Positives, False Positives, False Negatives, True Negatives
    tp = np.sum((class_preds == class_id) & (class_gt == class_id))
    fp = np.sum((predictions == class_id) & (ground_truth != class_id))
    fn = np.sum((predictions != class_id) & (ground_truth == class_id))
    tn = np.sum((predictions != class_id) & (ground_truth != class_id))
    
    # Calcular métricas
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    metrics_per_class[class_name] = {
        'precision': precision,
        'recall': recall,
        'f1_score': f1_score,
        'support': int(np.sum(mask)),
        'tp': int(tp),
        'fp': int(fp),
        'fn': int(fn),
        'tn': int(tn)
    }
    
    # Preencher matriz de confusão
    for pred_id in range(len(CLASSES)):
        confusion_matrix[class_id, pred_id] = np.sum(
            (ground_truth == class_id) & (predictions == pred_id)
        )

# ===========================
# GERAR RELATÓRIO
# ===========================
print("\n📝 Gerando relatório detalhado...")

timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

report = f"""
{'=' * 80}
                    RELATÓRIO DE AVALIAÇÃO - YOLOv8 CLASSIFICATION
{'=' * 80}

📅 DATA: {timestamp}
🤖 MODELO: {MODEL_PATH}
📁 DATASET: {DATA_DIR}

{'=' * 80}
                              MÉTRICAS GLOBAIS
{'=' * 80}

🎯 Acurácia Geral: {accuracy * 100:.2f}%
📊 Total de Amostras: {len(predictions)}

{'=' * 80}
                           MÉTRICAS POR CLASSE
{'=' * 80}

"""

for class_name, metrics in metrics_per_class.items():
    report += f"""
Classe: {class_name.upper()}
{'─' * 80}
  Precision:  {metrics['precision'] * 100:6.2f}%
  Recall:     {metrics['recall'] * 100:6.2f}%
  F1-Score:   {metrics['f1_score'] * 100:6.2f}%
  Support:    {metrics['support']:6d} amostras
  
  True Positives:   {metrics['tp']:4d}
  False Positives:  {metrics['fp']:4d}
  False Negatives:  {metrics['fn']:4d}
  True Negatives:   {metrics['tn']:4d}
"""

report += f"""
{'=' * 80}
                            MATRIZ DE CONFUSÃO
{'=' * 80}

               Predito
            {'  '.join([CLASSES[i][:15].ljust(15) for i in range(len(CLASSES))])}
Real
"""

for i in range(len(CLASSES)):
    row = f"{CLASSES[i][:15].ljust(15)}"
    for j in range(len(CLASSES)):
        row += f"{confusion_matrix[i, j]:5d}           "
    report += row + "\n"

report += f"""
{'=' * 80}
                          ANÁLISE DE CONFIANÇA
{'=' * 80}

Confiança Média:    {np.mean(confidences) * 100:.2f}%
Confiança Mínima:   {np.min(confidences) * 100:.2f}%
Confiança Máxima:   {np.max(confidences) * 100:.2f}%
Desvio Padrão:      {np.std(confidences) * 100:.2f}%

{'=' * 80}
                          PREDIÇÕES INCORRETAS
{'=' * 80}

"""

# Encontrar predições incorretas
incorrect_mask = predictions != ground_truth
incorrect_indices = np.where(incorrect_mask)[0]

if len(incorrect_indices) > 0:
    report += f"Total de erros: {len(incorrect_indices)} ({len(incorrect_indices)/len(predictions)*100:.2f}%)\n\n"
    report += "Top 10 erros com menor confiança:\n"
    report += "─" * 80 + "\n"
    
    # Ordenar por confiança
    sorted_indices = incorrect_indices[np.argsort(confidences[incorrect_mask])][:10]
    
    for idx in sorted_indices:
        real_class = CLASSES[ground_truth[idx]]
        pred_class = CLASSES[predictions[idx]]
        conf = confidences[idx]
        fname = file_names[idx]
        
        report += f"Arquivo: {fname}\n"
        report += f"  Real: {real_class} | Predito: {pred_class} | Confiança: {conf*100:.2f}%\n\n"
else:
    report += "🎉 Nenhum erro! Modelo perfeito!\n"

report += f"""
{'=' * 80}
                            CONCLUSÕES
{'=' * 80}

"""

# Análise automática
if accuracy >= 0.95:
    report += "✅ Excelente! O modelo apresenta alta acurácia.\n"
elif accuracy >= 0.85:
    report += "👍 Bom! O modelo tem desempenho satisfatório.\n"
elif accuracy >= 0.70:
    report += "⚠️  Razoável. Considere mais treinamento ou dados.\n"
else:
    report += "❌ Baixa acurácia. Revise dados e arquitetura.\n"

# Verificar balanceamento
class_supports = [m['support'] for m in metrics_per_class.values()]
if max(class_supports) / min(class_supports) > 3:
    report += "⚠️  Dataset desbalanceado detectado. Considere balancear as classes.\n"

# Verificar overfitting através da confiança
if np.mean(confidences) > 0.99:
    report += "⚠️  Confiança muito alta pode indicar overfitting.\n"

report += f"""
{'=' * 80}
"""

# Salvar relatório
report_path = RESULTS_DIR / "evaluation_report.txt"
with open(report_path, 'w', encoding='utf-8') as f:
    f.write(report)

print(report)
print(f"📄 Relatório salvo em: {report_path}")

# ===========================
# GERAR GRÁFICOS
# ===========================
print("\n📊 Gerando gráficos...")

# Configurar estilo
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# Figura com múltiplos gráficos
fig = plt.figure(figsize=(16, 10))

# 1. Matriz de Confusão
ax1 = plt.subplot(2, 3, 1)
sns.heatmap(confusion_matrix, annot=True, fmt='d', cmap='Blues',
            xticklabels=[CLASSES[i] for i in range(len(CLASSES))],
            yticklabels=[CLASSES[i] for i in range(len(CLASSES))],
            ax=ax1)
ax1.set_title('Matriz de Confusão', fontsize=14, fontweight='bold')
ax1.set_ylabel('Real')
ax1.set_xlabel('Predito')

# 2. Métricas por Classe
ax2 = plt.subplot(2, 3, 2)
class_names = list(metrics_per_class.keys())
precisions = [m['precision'] for m in metrics_per_class.values()]
recalls = [m['recall'] for m in metrics_per_class.values()]
f1_scores = [m['f1_score'] for m in metrics_per_class.values()]

x = np.arange(len(class_names))
width = 0.25

ax2.bar(x - width, precisions, width, label='Precision', alpha=0.8)
ax2.bar(x, recalls, width, label='Recall', alpha=0.8)
ax2.bar(x + width, f1_scores, width, label='F1-Score', alpha=0.8)

ax2.set_xlabel('Classes')
ax2.set_ylabel('Score')
ax2.set_title('Métricas por Classe', fontsize=14, fontweight='bold')
ax2.set_xticks(x)
ax2.set_xticklabels(class_names, rotation=45, ha='right')
ax2.legend()
ax2.set_ylim([0, 1.1])
ax2.grid(True, alpha=0.3)

# 3. Distribuição de Confiança
ax3 = plt.subplot(2, 3, 3)
ax3.hist(confidences, bins=20, edgecolor='black', alpha=0.7)
ax3.axvline(np.mean(confidences), color='r', linestyle='--', 
            label=f'Média: {np.mean(confidences):.2f}')
ax3.set_xlabel('Confiança')
ax3.set_ylabel('Frequência')
ax3.set_title('Distribuição de Confiança', fontsize=14, fontweight='bold')
ax3.legend()
ax3.grid(True, alpha=0.3)

# 4. Distribuição por Classe
ax4 = plt.subplot(2, 3, 4)
class_counts = [metrics_per_class[name]['support'] for name in class_names]
colors = plt.cm.Set3(np.linspace(0, 1, len(class_names)))
ax4.pie(class_counts, labels=class_names, autopct='%1.1f%%',
        startangle=90, colors=colors)
ax4.set_title('Distribuição de Amostras por Classe', fontsize=14, fontweight='bold')

# 5. Acertos vs Erros
ax5 = plt.subplot(2, 3, 5)
correct = np.sum(predictions == ground_truth)
incorrect = np.sum(predictions != ground_truth)
ax5.bar(['Acertos', 'Erros'], [correct, incorrect], color=['green', 'red'], alpha=0.7)
ax5.set_ylabel('Quantidade')
ax5.set_title(f'Acertos vs Erros (Acurácia: {accuracy*100:.1f}%)', 
              fontsize=14, fontweight='bold')
ax5.grid(True, alpha=0.3, axis='y')

# Adicionar valores nas barras
for i, v in enumerate([correct, incorrect]):
    ax5.text(i, v + 0.5, str(v), ha='center', fontweight='bold')

# 6. Confiança: Corretos vs Incorretos
ax6 = plt.subplot(2, 3, 6)
correct_confidences = confidences[predictions == ground_truth]
incorrect_confidences = confidences[predictions != ground_truth]

data_to_plot = [correct_confidences, incorrect_confidences]
labels = ['Corretos', 'Incorretos']

box = ax6.boxplot(data_to_plot, labels=labels, patch_artist=True,
                   showmeans=True, meanline=True)

for patch, color in zip(box['boxes'], ['lightgreen', 'lightcoral']):
    patch.set_facecolor(color)

ax6.set_ylabel('Confiança')
ax6.set_title('Confiança: Corretos vs Incorretos', fontsize=14, fontweight='bold')
ax6.grid(True, alpha=0.3, axis='y')

plt.tight_layout()

# Salvar gráfico
plots_path = RESULTS_DIR / "evaluation_plots.png"
plt.savefig(plots_path, dpi=300, bbox_inches='tight')
print(f"📊 Gráficos salvos em: {plots_path}")

# Mostrar gráfico
print("\n💡 Fechando janela de gráficos em 5 segundos...")
plt.show(block=False)
plt.pause(5)
plt.close()

# ===========================
# SALVAR MÉTRICAS EM JSON
# ===========================
metrics_json = {
    'timestamp': timestamp,
    'accuracy': float(accuracy),
    'total_samples': int(len(predictions)),
    'confidence_mean': float(np.mean(confidences)),
    'confidence_std': float(np.std(confidences)),
    'classes': {
        class_name: {
            'precision': float(metrics['precision']),
            'recall': float(metrics['recall']),
            'f1_score': float(metrics['f1_score']),
            'support': int(metrics['support'])
        }
        for class_name, metrics in metrics_per_class.items()
    },
    'confusion_matrix': confusion_matrix.tolist()
}

json_path = RESULTS_DIR / "evaluation_metrics.json"
with open(json_path, 'w') as f:
    json.dump(metrics_json, f, indent=2)

print(f"💾 Métricas JSON salvas em: {json_path}")

print("\n" + "=" * 80)
print("✅ AVALIAÇÃO COMPLETA!")
print("=" * 80)
