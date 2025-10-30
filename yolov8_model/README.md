# 🎯 Monitor de Sistema - Classificador YOLOv8

Sistema de classificação de imagens usando **YOLOv8** para identificar se capturas de tela mostram sistemas permitidos ou não permitidos.

## 📋 Visão Geral

Este módulo utiliza **YOLOv8 Classification** da Ultralytics para treinar um modelo de classificação binária que distingue entre:

- ✅ **Permitido**: Sistema/aplicativo autorizado
- ❌ **Não Permitido**: Outros sistemas/aplicativos

## 🚀 Quick Start

### 1. Instalação

```bash
# Criar ambiente virtual
python -m venv .venv

# Ativar ambiente
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### 2. Preparar Dados

Organize suas imagens na seguinte estrutura:

```
data/
├── permitido/
│   ├── screenshot1.jpg
│   ├── screenshot2.png
│   └── ...
└── nao_permitido/
    ├── other_app1.jpg
    ├── other_app2.png
    └── ...
```

**Recomendações:**
- Mínimo de 30 imagens por classe (ideal: 100+)
- Imagens variadas e representativas
- Dataset balanceado

### 3. Treinar Modelo

```bash
cd scripts
python train.py
```

O treinamento irá:
- Baixar automaticamente o modelo YOLOv8 pré-treinado
- Aplicar data augmentation
- Treinar com early stopping
- Salvar o melhor modelo em `scripts/models/final_model/best.pt`
- Gerar relatório detalhado

### 4. Avaliar Modelo

```bash
cd scripts
python evaluate.py
```

Gera:
- Métricas detalhadas (accuracy, precision, recall, F1)
- Matriz de confusão
- Gráficos de análise
- Relatório em texto e JSON

### 5. Fazer Predições

```bash
cd scripts
python predict.py
```

Menu interativo com opções:
1. Predizer imagem única com visualização
2. Predizer imagem única (texto apenas)
3. Processar lote de imagens

## 📁 Estrutura do Projeto

```
tensorflow_model/
├── data/                          # Dataset
│   ├── permitido/                 # Imagens permitidas
│   └── nao_permitido/             # Imagens não permitidas
│
├── scripts/                       # Scripts principais
│   ├── train.py                   # Treinamento
│   ├── evaluate.py                # Avaliação
│   ├── predict.py                 # Predições
│   └── models/                    # Modelos treinados
│       ├── training_run/          # Artefatos do último treino
│       │   ├── weights/
│       │   │   ├── best.pt        # Melhor modelo
│       │   │   └── last.pt        # Último checkpoint
│       │   ├── results.csv        # Métricas por época
│       │   └── results.png        # Gráficos de treino
│       │
│       └── final_model/           # Modelo para produção
│           ├── best.pt            # Modelo final
│           ├── training_report.txt
│           ├── evaluation_report.txt
│           ├── evaluation_plots.png
│           └── evaluation_metrics.json
│
├── config.yaml                    # Configuração do dataset
├── requirements.txt               # Dependências
├── base.txt                       # Guia detalhado
└── README.md                      # Este arquivo
```

## ⚙️ Configurações

### Parâmetros de Treinamento (train.py)

```python
EPOCHS = 100          # Número de épocas
IMG_SIZE = 640       # Tamanho da imagem
BATCH_SIZE = 16      # Tamanho do batch
MODEL_SIZE = 'n'     # Tamanho do modelo (n/s/m/l/x)
PATIENCE = 20        # Early stopping patience
```

### Tamanhos de Modelo YOLOv8

| Modelo | Velocidade | Precisão | Uso de Memória | Recomendação |
|--------|-----------|----------|----------------|--------------|
| `n` (nano) | ⚡⚡⚡ | ⭐⭐ | 💾 | CPU, testes rápidos |
| `s` (small) | ⚡⚡ | ⭐⭐⭐ | 💾💾 | **Recomendado** para maioria dos casos |
| `m` (medium) | ⚡ | ⭐⭐⭐⭐ | 💾💾💾 | Alta precisão, GPU |
| `l` (large) | 🐌 | ⭐⭐⭐⭐⭐ | 💾💾💾💾 | Máxima precisão, GPU potente |
| `x` (xlarge) | 🐌🐌 | ⭐⭐⭐⭐⭐ | 💾💾💾💾💾 | Aplicações críticas, GPU dedicada |

## 🔧 Uso Programático

### Treinar Modelo

```python
from ultralytics import YOLO

# Inicializar modelo
model = YOLO('yolov8n-cls.pt')

# Treinar
results = model.train(
    data='config.yaml',
    epochs=100,
    imgsz=640,
    batch=16
)
```

### Fazer Predição

```python
from ultralytics import YOLO

# Carregar modelo treinado
model = YOLO('scripts/models/final_model/best.pt')

# Predizer
results = model.predict('imagem.jpg')

# Obter resultado
pred_class = results[0].probs.top1        # 0 ou 1
confidence = results[0].probs.top1conf    # 0.0 a 1.0
```

### Integração com Sistema de Monitoramento

```python
from ultralytics import YOLO
from pathlib import Path

class ScreenChecker:
    def __init__(self, model_path='scripts/models/final_model/best.pt'):
        self.model = YOLO(model_path)
        self.classes = {0: 'nao_permitido', 1: 'permitido'}
    
    def check_screenshot(self, image_path):
        """
        Verifica se screenshot é de sistema permitido
        
        Returns:
            tuple: (is_allowed: bool, confidence: float, class_name: str)
        """
        results = self.model.predict(image_path, verbose=False)
        
        class_id = int(results[0].probs.top1)
        confidence = float(results[0].probs.top1conf)
        class_name = self.classes[class_id]
        
        is_allowed = (class_id == 1)
        
        return is_allowed, confidence, class_name

# Uso
checker = ScreenChecker()
is_allowed, conf, class_name = checker.check_screenshot('screenshot.png')

if not is_allowed:
    print(f"⚠️ Sistema não permitido detectado! ({conf*100:.1f}% confiança)")
```

## 📊 Métricas de Exemplo

Após um treinamento bem-sucedido, você pode esperar métricas como:

```
Acurácia Geral:  95.5%
Precision:       94.2%
Recall:          96.8%
F1-Score:        95.4%
```

## 🐛 Troubleshooting

### Erro: CUDA out of memory

**Solução:** Reduza o `BATCH_SIZE` em `train.py`

```python
BATCH_SIZE = 8  # ou 4
```

### Erro: Modelo não encontrado

**Solução:** Execute o treinamento primeiro:

```bash
cd scripts
python train.py
```

### Baixa Acurácia (< 70%)

**Possíveis causas:**
- Dataset muito pequeno → Adicione mais imagens
- Dataset desbalanceado → Balance as classes
- Imagens de baixa qualidade → Melhore a qualidade
- Classes muito similares → Revise os dados

**Soluções:**
1. Aumente o dataset (mínimo 50 imagens por classe)
2. Use modelo maior (`MODEL_SIZE = 's'` ou `'m'`)
3. Treine por mais épocas (`EPOCHS = 150`)
4. Verifique se imagens estão nas pastas corretas

### Script não encontra GPU

**Solução:** Verifique instalação do PyTorch com CUDA:

```bash
python -c "import torch; print(torch.cuda.is_available())"
```

Se retornar `False`, reinstale PyTorch com CUDA:

```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

## 📚 Recursos

- **Documentação YOLOv8:** https://docs.ultralytics.com/
- **GitHub Ultralytics:** https://github.com/ultralytics/ultralytics
- **Guia Detalhado:** Veja `base.txt` para instruções completas

## 🤝 Contribuindo

Este é um módulo do projeto TCC Monitor. Para contribuir:

1. Mantenha a estrutura de pastas
2. Documente alterações em configurações
3. Teste antes de commit
4. Atualize este README se necessário

## 📝 Notas Importantes

- ⚠️ Mantenha backup do modelo treinado (`best.pt`)
- ⚡ GPU acelera significativamente o treinamento
- 🔄 YOLOv8 aplica data augmentation automaticamente
- 📊 Sempre avalie o modelo antes de usar em produção
- 🎯 Comece com modelo `n` para testes, escale se necessário

## 🆚 Migração do TensorFlow

Este projeto foi migrado de TensorFlow/Keras para YOLOv8. Principais vantagens:

| Aspecto | TensorFlow Manual | YOLOv8 |
|---------|------------------|---------|
| **Código** | ~500 linhas | ~100 linhas |
| **Data Aug** | Manual | Automático |
| **Velocidade** | Média | Rápida |
| **Facilidade** | Complexo | Simples |
| **Manutenção** | Alta | Baixa |
| **Performance** | Boa | Excelente |

---

**Desenvolvido para o projeto TCC Monitor**  
*Sistema de Monitoramento de Atividades de Alunos*


