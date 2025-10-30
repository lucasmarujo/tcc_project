"""
Script para testar a API do sistema.
Útil para verificar se tudo está funcionando corretamente.
"""
import requests
import json
from datetime import datetime

# Configurações
BASE_URL = 'http://localhost:8000'
REGISTRATION_NUMBER = '202301'  # Substitua pela matrícula de um aluno cadastrado

def test_heartbeat():
    """Testa o endpoint de heartbeat."""
    print("\n" + "="*60)
    print("Testando Heartbeat...")
    print("="*60)
    
    url = f"{BASE_URL}/api/heartbeat/"
    data = {'registration_number': REGISTRATION_NUMBER}
    
    try:
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"Erro: {e}")
        return False


def test_report_url_access():
    """Testa o envio de um evento de acesso a URL."""
    print("\n" + "="*60)
    print("Testando Report - Acesso a URL...")
    print("="*60)
    
    url = f"{BASE_URL}/api/report/"
    data = {
        'registration_number': REGISTRATION_NUMBER,
        'event_type': 'url_access',
        'url': 'https://www.google.com/search?q=test',
        'browser': 'Google Chrome',
        'machine_name': 'PC-TESTE-API',
        'additional_data': {
            'test': True,
            'timestamp': datetime.now().isoformat()
        }
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 201
    except Exception as e:
        print(f"Erro: {e}")
        return False


def test_report_app_launch():
    """Testa o envio de um evento de abertura de aplicativo."""
    print("\n" + "="*60)
    print("Testando Report - Abertura de Aplicativo...")
    print("="*60)
    
    url = f"{BASE_URL}/api/report/"
    data = {
        'registration_number': REGISTRATION_NUMBER,
        'event_type': 'app_launch',
        'app_name': 'WhatsApp.exe',
        'machine_name': 'PC-TESTE-API',
        'additional_data': {
            'test': True,
            'timestamp': datetime.now().isoformat()
        }
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 201
    except Exception as e:
        print(f"Erro: {e}")
        return False


def test_invalid_registration():
    """Testa com matrícula inválida."""
    print("\n" + "="*60)
    print("Testando Matrícula Inválida (deve falhar)...")
    print("="*60)
    
    url = f"{BASE_URL}/api/heartbeat/"
    data = {'registration_number': '999999'}
    
    try:
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 401
    except Exception as e:
        print(f"Erro: {e}")
        return False


def main():
    """Executa todos os testes."""
    print("\n" + "="*60)
    print("  TESTES DA API - Sistema de Monitoramento")
    print("="*60)
    print(f"\nBase URL: {BASE_URL}")
    print(f"Matrícula de Teste: {REGISTRATION_NUMBER}")
    print("\nCERTIFIQUE-SE DE QUE:")
    print("1. O servidor Django está rodando")
    print("2. Existe um aluno com essa matrícula cadastrado")
    print("3. O aluno com essa matrícula está ativo")
    
    input("\nPressione Enter para continuar...")
    
    results = {
        'Heartbeat': test_heartbeat(),
        'Report URL Access': test_report_url_access(),
        'Report App Launch': test_report_app_launch(),
        'Invalid Registration': test_invalid_registration(),
    }
    
    # Resumo
    print("\n" + "="*60)
    print("  RESUMO DOS TESTES")
    print("="*60)
    
    for test_name, result in results.items():
        status = "✓ PASSOU" if result else "✗ FALHOU"
        print(f"{test_name}: {status}")
    
    total = len(results)
    passed = sum(results.values())
    
    print("\n" + "="*60)
    print(f"Total: {passed}/{total} testes passaram")
    print("="*60)
    
    if passed == total:
        print("\n🎉 Todos os testes passaram! Sistema funcionando corretamente.")
    else:
        print("\n⚠️  Alguns testes falharam. Verifique a configuração.")


if __name__ == '__main__':
    main()

