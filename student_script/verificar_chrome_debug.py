"""
Script de verificação: Chrome com debugging ativo.
Execute este script para verificar se o Chrome está configurado corretamente.
"""
import requests
import json
import sys

def verificar_chrome_debugging():
    """Verifica se o Chrome está com debugging ativo."""
    
    print("=" * 80)
    print("    VERIFICAÇÃO: Chrome DevTools (Debugging)")
    print("=" * 80)
    print()
    
    try:
        print("🔍 Tentando conectar ao Chrome DevTools (porta 9222)...")
        response = requests.get("http://127.0.0.1:9222/json", timeout=3)
        
        if response.status_code == 200:
            tabs = response.json()
            
            print("✅ SUCESSO! Chrome DevTools está ATIVO!")
            print()
            print(f"📊 {len(tabs)} tab(s) encontrada(s):")
            print()
            
            brightspace_tabs = []
            
            for i, tab in enumerate(tabs, 1):
                if tab.get('type') == 'page':
                    url = tab.get('url', 'N/A')
                    title = tab.get('title', 'N/A')
                    
                    print(f"  Tab {i}:")
                    print(f"    Título: {title[:60]}")
                    print(f"    URL: {url[:60]}")
                    
                    # Verificar se é Brightspace
                    if 'brightspace' in url.lower() or 'd2l' in url.lower() or 'ava.anchieta.br' in url.lower():
                        brightspace_tabs.append((title, url))
                        print("    🎓 BRIGHTSPACE DETECTADO! ✓")
                    
                    print()
            
            print("=" * 80)
            
            if brightspace_tabs:
                print()
                print(f"🎓 {len(brightspace_tabs)} tab(s) do BRIGHTSPACE encontrada(s)!")
                print()
                print("✅ O detector vai funcionar com estas tabs!")
                print()
                for title, url in brightspace_tabs:
                    print(f"  • {title[:50]}")
                print()
            else:
                print()
                print("⚠️  Nenhuma tab do Brightspace aberta no Chrome.")
                print("   Abra o AVA/Brightspace no Chrome para testar.")
                print()
            
            print("=" * 80)
            print()
            print("✅ CONFIGURAÇÃO CORRETA!")
            print("   O detector do Brightspace VAI FUNCIONAR.")
            print()
            print("   Próximo passo: python monitor.py")
            print()
            print("=" * 80)
            
            return True
        
        else:
            print(f"❌ ERRO: Status code {response.status_code}")
            mostrar_solucao()
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ ERRO: Não foi possível conectar ao Chrome DevTools")
        print()
        mostrar_solucao()
        return False
    
    except Exception as e:
        print(f"❌ ERRO INESPERADO: {e}")
        mostrar_solucao()
        return False


def mostrar_solucao():
    """Mostra como resolver o problema."""
    print()
    print("=" * 80)
    print("    COMO CORRIGIR")
    print("=" * 80)
    print()
    print("O Chrome NÃO está com debugging ativo.")
    print()
    print("📌 SOLUÇÃO:")
    print()
    print("1. FECHE TODAS as instâncias do Chrome")
    print()
    print("2. Execute o script:")
    print("   > start_chrome_debug.bat")
    print()
    print("   OU inicie manualmente:")
    print('   > "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe" ^')
    print('     --remote-debugging-port=9222 ^')
    print('     --user-data-dir="%TEMP%\\chrome_debug_profile"')
    print()
    print("3. Use ESTE Chrome para acessar o Brightspace")
    print()
    print("4. Execute este script novamente para verificar:")
    print("   > python verificar_chrome_debug.py")
    print()
    print("=" * 80)
    print()


def verificar_dependencias():
    """Verifica se as dependências estão instaladas."""
    print()
    print("🔍 Verificando dependências...")
    print()
    
    dependencias_ok = True
    
    try:
        import pychrome
        print("  ✓ pychrome instalado")
    except ImportError:
        print("  ✗ pychrome NÃO instalado")
        dependencias_ok = False
    
    try:
        import websocket
        print("  ✓ websocket-client instalado")
    except ImportError:
        print("  ✗ websocket-client NÃO instalado")
        dependencias_ok = False
    
    print()
    
    if not dependencias_ok:
        print("⚠️  Algumas dependências estão faltando!")
        print()
        print("   Execute: pip install -r requirements_brightspace.txt")
        print()
        return False
    
    print("✅ Todas as dependências instaladas!")
    print()
    return True


def main():
    """Função principal."""
    print()
    print("╔════════════════════════════════════════════════════════════════════════════╗")
    print("║                                                                            ║")
    print("║            VERIFICADOR - Chrome DevTools para Brightspace                 ║")
    print("║                                                                            ║")
    print("╚════════════════════════════════════════════════════════════════════════════╝")
    print()
    
    # Verificar dependências
    if not verificar_dependencias():
        sys.exit(1)
    
    # Verificar Chrome
    resultado = verificar_chrome_debugging()
    
    if resultado:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == '__main__':
    main()

