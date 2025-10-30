"""
Script de teste para verificar eventos de teclado.
Simula o envio de eventos de teclado do script do aluno para o servidor.
"""
import requests
import json
from datetime import datetime

# Configuração
BASE_URL = 'http://localhost:8000'
REPORT_URL = f'{BASE_URL}/api/report/'

# Dados do aluno de teste
STUDENT_DATA = {
    'registration_number': '202301234',
    'student_name': 'Aluno Teste',
    'student_email': 'teste@aluno.com'
}

# Eventos de teclado para testar
KEYBOARD_EVENTS = [
    {
        'event_type': 'keyboard_event',
        'key_event': 'print_screen',
        'description': 'Tentativa de captura de tela (Print Screen)',
        'key': 'Print Screen'
    },
    {
        'event_type': 'keyboard_event',
        'key_event': 'win_shift_s',
        'description': 'Tentativa de captura de tela (Win + Shift + S)',
        'key': 'Win + Shift + S'
    },
    {
        'event_type': 'keyboard_event',
        'key_event': 'f11',
        'description': 'Tecla F11 pressionada (modo tela cheia)',
        'key': 'F11'
    },
    {
        'event_type': 'keyboard_event',
        'key_event': 'ctrl_c',
        'description': 'Copiar (Ctrl + C)',
        'key': 'Ctrl + C'
    },
    {
        'event_type': 'keyboard_event',
        'key_event': 'ctrl_v',
        'description': 'Colar (Ctrl + V)',
        'key': 'Ctrl + V'
    }
]


def enviar_evento_teclado(key_event_data):
    """Envia um evento de teclado para o servidor."""
    
    payload = {
        'registration_number': STUDENT_DATA['registration_number'],
        'event_type': key_event_data['event_type'],
        'key_event': key_event_data['key_event'],
        'machine_name': 'TESTE-PC',
        'additional_data': {
            'description': key_event_data['description'],
            'key': key_event_data['key'],
            'timestamp': datetime.now().isoformat()
        }
    }
    
    try:
        print(f"\n{'='*60}")
        print(f"Enviando evento: {key_event_data['key_event']}")
        print(f"Descrição: {key_event_data['description']}")
        print(f"{'='*60}")
        
        response = requests.post(
            REPORT_URL,
            json=payload,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Resposta: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        
        if response.status_code == 201:
            print("✅ Evento enviado com SUCESSO!")
            return True
        else:
            print("❌ Erro ao enviar evento")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ ERRO: Não foi possível conectar ao servidor")
        print(f"   Certifique-se de que o servidor está rodando em {BASE_URL}")
        return False
    except Exception as e:
        print(f"❌ ERRO: {e}")
        return False


def verificar_aluno():
    """Verifica se o aluno de teste existe."""
    
    print("\n" + "="*60)
    print("VERIFICANDO ALUNO DE TESTE")
    print("="*60)
    
    heartbeat_url = f'{BASE_URL}/api/heartbeat/'
    
    try:
        response = requests.post(
            heartbeat_url,
            json=STUDENT_DATA,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            print(f"\n✅ Aluno: {data.get('student')}")
            print(f"✅ Matrícula: {data.get('student_registration')}")
            
            if data.get('new_student'):
                print("ℹ️  Aluno criado automaticamente")
            else:
                print("ℹ️  Aluno já existia no banco")
            
            return True
        else:
            print(f"❌ Erro ao verificar aluno: {response.json()}")
            return False
            
    except Exception as e:
        print(f"❌ ERRO: {e}")
        return False


def main():
    """Função principal."""
    
    print("\n" + "="*60)
    print("TESTE DE EVENTOS DE TECLADO")
    print("="*60)
    print("\nEste script simula o envio de eventos de teclado")
    print("do script do aluno para o servidor Django.")
    print("\nCertifique-se de que:")
    print("1. O servidor Django está rodando (python manage.py runserver)")
    print("2. As migrações foram aplicadas (python manage.py migrate)")
    
    input("\nPressione ENTER para continuar...")
    
    # Verificar aluno
    if not verificar_aluno():
        print("\n❌ Não foi possível verificar/criar aluno. Abortando.")
        return
    
    # Enviar eventos de teclado
    print("\n" + "="*60)
    print("ENVIANDO EVENTOS DE TECLADO")
    print("="*60)
    
    sucessos = 0
    falhas = 0
    
    for i, evento in enumerate(KEYBOARD_EVENTS, 1):
        print(f"\n[{i}/{len(KEYBOARD_EVENTS)}]")
        
        if enviar_evento_teclado(evento):
            sucessos += 1
        else:
            falhas += 1
        
        # Pequena pausa entre envios
        import time
        time.sleep(1)
    
    # Resumo
    print("\n" + "="*60)
    print("RESUMO")
    print("="*60)
    print(f"\n✅ Eventos enviados com sucesso: {sucessos}")
    print(f"❌ Eventos com falha: {falhas}")
    print(f"📊 Total: {sucessos + falhas}")
    
    if sucessos > 0:
        print("\n" + "="*60)
        print("PRÓXIMOS PASSOS")
        print("="*60)
        print(f"\n1. Acesse a dashboard: {BASE_URL}/dashboard/")
        print("2. Vá para 'Eventos' para ver os eventos de teclado")
        print("3. Vá para 'Alertas' para ver os alertas automáticos")
        print("4. Verifique os detalhes de cada alerta")
        print("\nOs eventos devem aparecer com ícone de teclado (⌨️)")
        print("e os alertas devem ter severidades apropriadas.")
    
    print("\n" + "="*60)


if __name__ == '__main__':
    main()

