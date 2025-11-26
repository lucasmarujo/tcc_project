"""
Script de teste para o BrightspaceDetector.
Verifica se o detector está funcionando corretamente.
"""
import logging
import time
import sys
from brightspace_detector import BrightspaceDetector

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_detector():
    """Testa o detector do Brightspace."""
    
    print("=" * 80)
    print(" TESTE DO BRIGHTSPACE DETECTOR")
    print("=" * 80)
    print()
    print("Este script testa se o detector está configurado corretamente.")
    print()
    print("PASSOS PARA TESTAR:")
    print()
    print("1. Certifique-se de que o Chrome está rodando com debugging:")
    print("   > start_chrome_debug.bat")
    print("   OU")
    print("   > chrome.exe --remote-debugging-port=9222")
    print()
    print("2. Abra o Brightspace no Chrome")
    print()
    print("3. Navegue entre páginas de conteúdo e provas")
    print()
    print("4. Observe os logs neste terminal")
    print()
    print("=" * 80)
    print()
    
    input("Pressione ENTER quando o Chrome estiver pronto...")
    print()
    
    # Callback para alertas
    def handle_alert(alert_data):
        """Processa alertas do detector."""
        alert_type = alert_data.get('alert_type', 'unknown')
        message = alert_data.get('message', '')
        severity = alert_data.get('severity', 'info')
        
        print()
        print("=" * 80)
        if severity == 'critical':
            print("🚨 ALERTA CRÍTICO 🚨")
        elif severity == 'info':
            print("ℹ️  INFORMAÇÃO")
        else:
            print(f"⚠️  ALERTA ({severity.upper()})")
        print("=" * 80)
        print(f"Tipo: {alert_type}")
        print(f"Mensagem: {message}")
        
        if 'url' in alert_data:
            print(f"URL: {alert_data['url']}")
        
        if 'quiz_duration' in alert_data:
            duration = alert_data['quiz_duration']
            print(f"Tempo na prova: {duration:.0f} segundos")
        
        print("=" * 80)
        print()
    
    # Criar e iniciar detector
    logger.info("Criando detector...")
    detector = BrightspaceDetector(alert_callback=handle_alert)
    
    logger.info("Iniciando detector...")
    detector.start()
    
    if not detector.running:
        logger.error("Falha ao iniciar o detector!")
        logger.error("Verifique se as dependências estão instaladas:")
        logger.error("  pip install pychrome websocket-client")
        sys.exit(1)
    
    logger.info("Detector iniciado com sucesso!")
    print()
    print("Monitorando... Pressione Ctrl+C para parar")
    print()
    print("DICA: Abra uma prova no Brightspace e depois tente acessar")
    print("      uma página de conteúdo para ver o alerta de acesso indevido.")
    print()
    
    try:
        # Loop principal
        last_status_time = time.time()
        
        while True:
            time.sleep(1)
            
            # Mostrar status a cada 10 segundos
            if time.time() - last_status_time >= 10:
                status = detector.get_status()
                
                print("\n" + "-" * 80)
                print(f"STATUS DO DETECTOR:")
                print(f"  - Rodando: {status['running']}")
                print(f"  - Em prova: {status['is_in_quiz']}")
                print(f"  - Tipo de página atual: {status['current_page_type']}")
                print(f"  - Páginas verificadas: {status['pages_checked']}")
                print(f"  - Alertas enviados: {status['alerts_sent']}")
                
                if status['quiz_started_time']:
                    print(f"  - Prova iniciada em: {status['quiz_started_time']}")
                
                print("-" * 80 + "\n")
                
                last_status_time = time.time()
    
    except KeyboardInterrupt:
        print("\n\nParando teste...")
        detector.stop()
        
        # Estatísticas finais
        status = detector.get_status()
        print()
        print("=" * 80)
        print(" ESTATÍSTICAS FINAIS")
        print("=" * 80)
        print(f"Páginas verificadas: {status['pages_checked']}")
        print(f"Alertas enviados: {status['alerts_sent']}")
        print("=" * 80)
        print()
        print("Teste concluído!")


def test_connection():
    """Testa a conexão com o Chrome DevTools."""
    print("=" * 80)
    print(" TESTE DE CONEXÃO COM CHROME DEVTOOLS")
    print("=" * 80)
    print()
    
    try:
        import requests
        
        print("Tentando conectar ao Chrome DevTools (porta 9222)...")
        response = requests.get("http://127.0.0.1:9222/json", timeout=2)
        
        if response.status_code == 200:
            tabs = response.json()
            print(f"✅ Conexão bem-sucedida!")
            print(f"   {len(tabs)} tab(s) encontrada(s)")
            print()
            
            # Mostrar tabs
            for i, tab in enumerate(tabs, 1):
                if tab.get('type') == 'page':
                    print(f"   Tab {i}:")
                    print(f"     - Título: {tab.get('title', 'N/A')[:60]}")
                    print(f"     - URL: {tab.get('url', 'N/A')[:60]}")
                    print()
            
            return True
        else:
            print(f"❌ Erro: Status code {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ ERRO: Não foi possível conectar ao Chrome DevTools")
        print()
        print("SOLUÇÃO:")
        print("1. Feche TODAS as instâncias do Chrome")
        print("2. Execute: start_chrome_debug.bat")
        print("   OU")
        print("   chrome.exe --remote-debugging-port=9222")
        print()
        return False
    
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        return False


def main():
    """Função principal do teste."""
    print()
    print("╔════════════════════════════════════════════════════════════════════════════╗")
    print("║                   TESTE DO BRIGHTSPACE DETECTOR                            ║")
    print("╚════════════════════════════════════════════════════════════════════════════╝")
    print()
    
    # Menu
    print("Escolha uma opção:")
    print()
    print("1. Testar conexão com Chrome DevTools")
    print("2. Executar teste completo do detector")
    print("3. Sair")
    print()
    
    choice = input("Opção: ").strip()
    print()
    
    if choice == "1":
        test_connection()
    elif choice == "2":
        if not test_connection():
            print()
            print("⚠️  Corrija a conexão com o Chrome antes de continuar.")
            sys.exit(1)
        print()
        input("Pressione ENTER para continuar com o teste completo...")
        print()
        test_detector()
    elif choice == "3":
        print("Até logo!")
    else:
        print("Opção inválida!")


if __name__ == '__main__':
    main()

