"""
Script para testar o Screen Analyzer.
Testa a detecção de provas vs slides usando textos de exemplo.
"""
import sys
import logging
from pathlib import Path

# Adicionar student_script ao path
sys.path.insert(0, str(Path(__file__).parent))

from screen_analyzer import ScreenAnalyzer

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_keyword_detection():
    """Testa detecção de palavras-chave."""
    print("\n" + "="*70)
    print(" TESTE DE DETECÇÃO DE PALAVRAS-CHAVE")
    print("="*70 + "\n")
    
    analyzer = ScreenAnalyzer(use_llm=False)
    
    # Casos de teste
    test_cases = [
        {
            'name': 'PROVA - Questão Múltipla Escolha',
            'text': """
            Questão 5 de 20
            Tempo restante: 35 minutos
            
            Assinale a alternativa correta sobre Python:
            
            a) É uma linguagem compilada
            b) É uma linguagem interpretada
            c) Não suporta orientação a objetos
            d) Foi criada em 1950
            
            Marcar resposta    Próxima questão
            """,
            'expected': 'prova'
        },
        {
            'name': 'PROVA - Questão Dissertativa',
            'text': """
            Questão 12 de 15
            Pontuação: 10 pontos
            
            Dissertativa: Explique o conceito de herança em POO.
            
            Resposta:
            [Campo de texto]
            
            Salvar resposta    Enviar prova
            """,
            'expected': 'prova'
        },
        {
            'name': 'SLIDES - Apresentação',
            'text': """
            Slide 8 de 30
            Capítulo 3: Programação Orientada a Objetos
            
            Conteúdo da Aula:
            • Conceitos fundamentais
            • Definição de classes
            • Exemplos práticos
            
            Bibliografia:
            - Python OOP for Beginners
            
            Anterior    Próximo slide
            """,
            'expected': 'material'
        },
        {
            'name': 'SLIDES - Material PDF',
            'text': """
            Introdução à Programação - Módulo 2
            
            Tópicos desta seção:
            1. Variáveis e tipos de dados
            2. Estruturas de controle
            3. Funções e procedimentos
            
            Resumo:
            Neste capítulo vamos aprender sobre...
            
            Referências e leitura complementar...
            """,
            'expected': 'material'
        },
        {
            'name': 'AVA - Página Normal',
            'text': """
            Bem-vindo ao AVA Anchieta
            
            Suas atividades:
            - Fórum de discussão (novo!)
            - Trabalho 1 - Prazo: 30/11
            - Leitura: Capítulo 5
            
            Últimas notícias da turma...
            """,
            'expected': 'outro'
        }
    ]
    
    # Executar testes
    passed = 0
    failed = 0
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. {test['name']}")
        print("-" * 70)
        
        score, details = analyzer.calculate_keyword_score(test['text'])
        
        # Determinar classificação
        if score > 5:
            classification = 'prova'
        elif score < -5:
            classification = 'material'
        else:
            classification = 'outro'
        
        # Verificar resultado
        success = classification == test['expected']
        status = "[OK] PASSOU" if success else "[FALHOU]"
        
        print(f"Score: {score:+d}")
        print(f"Classificação: {classification}")
        print(f"Esperado: {test['expected']}")
        print(f"Status: {status}")
        
        if details['prova_matches']:
            print(f"\nPalavras de PROVA encontradas ({len(details['prova_matches'])}):")
            for keyword, weight in details['prova_matches'][:5]:  # Mostrar top 5
                print(f"  - '{keyword}' (peso {weight})")
        
        if details['material_matches']:
            print(f"\nPalavras de MATERIAL encontradas ({len(details['material_matches'])}):")
            for keyword, weight in details['material_matches'][:5]:  # Mostrar top 5
                print(f"  - '{keyword}' (peso {weight})")
        
        if success:
            passed += 1
        else:
            failed += 1
    
    # Resumo
    print("\n" + "="*70)
    print(" RESUMO DOS TESTES")
    print("="*70)
    print(f"Total: {len(test_cases)} testes")
    print(f"[OK] Passaram: {passed}")
    print(f"[X] Falharam: {failed}")
    print(f"Taxa de acerto: {(passed/len(test_cases)*100):.1f}%")
    print()
    
    return failed == 0


def test_with_real_image():
    """Testa com uma imagem real (se disponível)."""
    print("\n" + "="*70)
    print(" TESTE COM IMAGEM REAL (se disponível)")
    print("="*70 + "\n")
    
    try:
        from PIL import Image
        
        # Tentar carregar uma imagem de teste
        test_image_path = Path(__file__).parent.parent / 'yolov8_model' / 'data' / 'train' / 'permitido' / 'ok (1).jpg'
        
        if not test_image_path.exists():
            print("[!] Nenhuma imagem de teste encontrada")
            print(f"Procurou em: {test_image_path}")
            return True
        
        print(f"Testando com: {test_image_path.name}")
        
        analyzer = ScreenAnalyzer(use_llm=False)
        image = Image.open(test_image_path)
        
        # Analisar
        result = analyzer.analyze_screen(image)
        
        print(f"\nResultado:")
        print(f"  Classificação: {result['classification']}")
        print(f"  Confiança: {result['confidence']:.2f}")
        print(f"  Permitido: {result['is_allowed']}")
        print(f"  Razão: {result['reason']}")
        print(f"  Texto extraído: {result['text_extracted'][:200]}...")
        
        return True
    
    except ImportError as e:
        print(f"[!] OCR nao disponivel: {e}")
        print("Instale com: pip install easyocr")
        return True
    
    except Exception as e:
        print(f"[X] Erro ao testar com imagem: {e}")
        return False


def main():
    """Função principal."""
    print("\n" + "=" * 70)
    print("  TESTE DO SCREEN ANALYZER - Detecção Prova vs Slides")
    print("=" * 70)
    
    # Teste 1: Palavras-chave
    success1 = test_keyword_detection()
    
    # Teste 2: Imagem real
    success2 = test_with_real_image()
    
    # Resultado final
    print("\n" + "="*70)
    if success1 and success2:
        print("[OK] TODOS OS TESTES PASSARAM!")
        print("\nProximos passos:")
        print("1. Instale OCR: pip install -r requirements_ocr.txt")
        print("2. Customize palavras-chave em screen_analyzer.py")
        print("3. Integre no screen_monitor.py")
        print("4. Teste com provas reais do seu AVA")
    else:
        print("[X] ALGUNS TESTES FALHARAM")
        print("Revise o codigo e ajuste os parametros")
    print("="*70 + "\n")
    
    return 0 if (success1 and success2) else 1


if __name__ == '__main__':
    sys.exit(main())

