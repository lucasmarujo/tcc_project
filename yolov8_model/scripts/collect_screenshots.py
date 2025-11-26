"""
Script para coletar screenshots para melhorar o dataset.
Facilita a coleta organizada de imagens para treinar o modelo.
"""
import time
import sys
from PIL import ImageGrab
from datetime import datetime
from pathlib import Path

def collect_screenshots(category: str, interval: int = 5, count: int = 10):
    """
    Coleta screenshots para o dataset.
    
    Args:
        category: 'prova', 'slides', 'ava_normal' ou 'chatbot'
        interval: Segundos entre cada captura
        count: Número de capturas
    """
    # Diretório de saída
    base_dir = Path(__file__).parent.parent / 'data' / 'train'
    output_dir = base_dir / category
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print(f"COLETA DE SCREENSHOTS - Categoria: {category}")
    print("=" * 60)
    print(f"Quantidade: {count} imagens")
    print(f"Intervalo: {interval} segundos entre capturas")
    print(f"Destino: {output_dir}")
    print()
    print("INSTRUÇÕES:")
    print("1. Abra a janela/tela que deseja capturar")
    print("2. Deixe o conteúdo visível")
    print("3. Pressione Enter para iniciar a contagem regressiva")
    print()
    
    input("Pressione Enter quando estiver pronto...")
    
    # Contagem regressiva
    for i in range(3, 0, -1):
        print(f"{i}...")
        time.sleep(1)
    
    print("\n🎬 INICIANDO CAPTURAS!\n")
    
    captured = 0
    for i in range(count):
        try:
            print(f"[{i+1}/{count}] Capturando...", end=" ")
            
            # Capturar screenshot
            screenshot = ImageGrab.grab()
            
            # Gerar nome do arquivo
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{category}_{timestamp}_{i:03d}.png"
            filepath = output_dir / filename
            
            # Salvar
            screenshot.save(filepath)
            captured += 1
            
            print(f"✓ Salvo: {filename}")
            
            # Aguardar próxima captura (se não for a última)
            if i < count - 1:
                for remaining in range(interval, 0, -1):
                    print(f"  Próxima captura em {remaining}s...", end="\r")
                    time.sleep(1)
                print()  # Nova linha
        
        except KeyboardInterrupt:
            print("\n\n⚠ Captura interrompida pelo usuário")
            break
        
        except Exception as e:
            print(f"\n❌ Erro ao capturar: {e}")
            continue
    
    print()
    print("=" * 60)
    print(f"✅ COLETA CONCLUÍDA!")
    print(f"   {captured}/{count} imagens salvas em: {output_dir}")
    print("=" * 60)
    print()
    print("PRÓXIMOS PASSOS:")
    print("1. Revise as imagens capturadas")
    print("2. Remova imagens com problemas (se houver)")
    print("3. Colete mais imagens de outras categorias")
    print("4. Quando tiver 50+ de cada, execute: python train.py")
    print()


def show_help():
    """Mostra ajuda de uso."""
    print("""
╔══════════════════════════════════════════════════════════════╗
║         COLETOR DE SCREENSHOTS PARA TREINAMENTO              ║
╚══════════════════════════════════════════════════════════════╝

USO:
    python collect_screenshots.py <categoria> [intervalo] [count]

CATEGORIAS:
    prova        - Telas de provas/avaliações online
    slides       - Slides/apresentações da matéria
    ava_normal   - Páginas normais do AVA (fórum, lista atividades)
    chatbot      - Chatbots IA e ferramentas proibidas

PARÂMETROS:
    categoria    - OBRIGATÓRIO: Uma das categorias acima
    intervalo    - Opcional: Segundos entre capturas (padrão: 5)
    count        - Opcional: Número de capturas (padrão: 10)

EXEMPLOS:
    # Coletar 50 screenshots de provas (1 a cada 5 segundos)
    python collect_screenshots.py prova 5 50

    # Coletar 30 screenshots de slides (1 a cada 3 segundos)
    python collect_screenshots.py slides 3 30

    # Coletar 10 screenshots do AVA com intervalo padrão
    python collect_screenshots.py ava_normal

DICAS:
    - Para PROVAS: navegue entre diferentes questões
    - Para SLIDES: vá mudando os slides durante a captura
    - Para AVA: navegue por diferentes páginas
    - Capture diferentes resoluções e layouts
    - Mínimo recomendado: 50 imagens por categoria

ESTRUTURA DE PASTAS:
    yolov8_model/
    └── data/
        └── train/
            ├── prova/          (50+ imagens)
            ├── slides/         (50+ imagens)
            ├── ava_normal/     (30+ imagens)
            └── chatbot/        (40 imagens - já existe)
""")


def main():
    """Função principal."""
    # Parse argumentos
    if len(sys.argv) < 2 or sys.argv[1] in ['-h', '--help', 'help']:
        show_help()
        sys.exit(0)
    
    category = sys.argv[1]
    interval = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    count = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    
    # Validar categoria
    valid_categories = ['prova', 'slides', 'ava_normal', 'chatbot']
    if category not in valid_categories:
        print(f"❌ Erro: Categoria inválida '{category}'")
        print(f"Categorias válidas: {', '.join(valid_categories)}")
        print()
        print("Use --help para mais informações")
        sys.exit(1)
    
    # Validar parâmetros
    if interval < 1 or interval > 60:
        print("❌ Erro: Intervalo deve estar entre 1 e 60 segundos")
        sys.exit(1)
    
    if count < 1 or count > 1000:
        print("❌ Erro: Count deve estar entre 1 e 1000")
        sys.exit(1)
    
    # Executar coleta
    try:
        collect_screenshots(category, interval, count)
    except KeyboardInterrupt:
        print("\n\n⚠ Programa interrompido pelo usuário")
        sys.exit(0)


if __name__ == '__main__':
    main()

