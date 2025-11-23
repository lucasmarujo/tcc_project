"""
Script de teste para verificar se o ambiente está configurado corretamente
"""

import sys

def test_imports():
    """Testa se todas as bibliotecas necessárias estão instaladas"""
    print("=" * 60)
    print("TESTE DE CONFIGURAÇÃO - Script AVA")
    print("=" * 60)
    print()
    
    # Teste 1: Selenium
    print("1. Testando Selenium...")
    try:
        import selenium
        print(f"   ✓ Selenium instalado (versão {selenium.__version__})")
    except ImportError as e:
        print(f"   ✗ ERRO: Selenium não está instalado")
        print(f"   → Execute: pip install selenium")
        return False
    
    # Teste 2: WebDriver Manager
    print("\n2. Testando WebDriver Manager...")
    try:
        import webdriver_manager
        print(f"   ✓ WebDriver Manager instalado")
    except ImportError as e:
        print(f"   ✗ ERRO: WebDriver Manager não está instalado")
        print(f"   → Execute: pip install webdriver-manager")
        return False
    
    # Teste 3: PyAutoGUI (para captura de tela)
    print("\n3. Testando PyAutoGUI...")
    try:
        import pyautogui
        print(f"   ✓ PyAutoGUI instalado")
    except ImportError as e:
        print(f"   ✗ ERRO: PyAutoGUI não está instalado")
        print(f"   → Execute: pip install pyautogui")
        return False
    
    # Teste 4: Pillow
    print("\n4. Testando Pillow...")
    try:
        from PIL import Image
        print(f"   ✓ Pillow instalado")
    except ImportError as e:
        print(f"   ✗ ERRO: Pillow não está instalado")
        print(f"   → Execute: pip install Pillow")
        return False
    
    # Teste 5: Chrome Driver
    print("\n5. Testando Chrome Driver...")
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.chrome.options import Options
        from webdriver_manager.chrome import ChromeDriverManager
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--no-sandbox')
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.get("https://www.google.com")
        title = driver.title
        driver.quit()
        
        print(f"   ✓ Chrome Driver funcionando corretamente")
        print(f"   ✓ Teste de navegação bem-sucedido (acessou Google)")
        
    except Exception as e:
        print(f"   ✗ ERRO: Problema com Chrome Driver")
        print(f"   → Erro: {str(e)}")
        print(f"   → Certifique-se de ter o Google Chrome instalado")
        return False
    
    print("\n" + "=" * 60)
    print("✓ TODOS OS TESTES PASSARAM!")
    print("✓ O ambiente está configurado corretamente")
    print("✓ Você pode executar: python main.py")
    print("=" * 60)
    
    return True


def test_credentials():
    """Exibe informações sobre as credenciais"""
    print("\n" + "=" * 60)
    print("INFORMAÇÕES DAS CREDENCIAIS")
    print("=" * 60)
    print("\nCredenciais configuradas no main.py:")
    print("  • Usuário: 2108723")
    print("  • Senha: 42071471873!")
    print("\nSe precisar alterar, edite as linhas 476-477 em main.py")
    print("=" * 60)


if __name__ == "__main__":
    print("\n")
    success = test_imports()
    
    if success:
        test_credentials()
        print("\n✅ Sistema pronto para uso!\n")
        sys.exit(0)
    else:
        print("\n❌ Corrija os erros acima antes de prosseguir.\n")
        sys.exit(1)

