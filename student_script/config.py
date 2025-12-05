"""
Configurações do script de monitoramento.
"""
import sys
import os
import json
from pathlib import Path

def get_bundle_dir():
    """Retorna o diretório base para arquivos de dados (PyInstaller ou execução normal)."""
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent

def get_config_dir():
    """Retorna o diretório para salvar configurações persistentes."""
    if getattr(sys, 'frozen', False):
        # Quando compilado, salvar na pasta do executável
        return Path(sys.executable).parent
    return Path(__file__).parent

# Configurações do servidor
SERVER_URL = os.getenv('MONITOR_SERVER_URL', 'http://localhost:8000')

# Endpoints
REPORT_ENDPOINT = f"{SERVER_URL}/api/report/"
ALERT_ENDPOINT = f"{SERVER_URL}/api/alert/"
HEARTBEAT_ENDPOINT = f"{SERVER_URL}/api/heartbeat/"

# Arquivo de configuração local do aluno (deve ser persistente)
CONFIG_FILE = get_config_dir() / 'student_config.json'

def get_student_info():
    """Obtém as informações do aluno do arquivo de configuração."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config
        except:
            return None
    return None

def get_student_registration():
    """Obtém apenas a matrícula do aluno."""
    info = get_student_info()
    return info.get('registration_number') if info else None

def save_student_info(registration_number, name=None, email=None):
    """Salva as informações do aluno no arquivo de configuração."""
    config = {'registration_number': registration_number}
    if name:
        config['name'] = name
    if email:
        config['email'] = email
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def clear_student_registration():
    """Remove o arquivo de configuração."""
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()

# Configurações de monitoramento
MONITORING_INTERVAL = 5  # segundos entre cada verificação
HEARTBEAT_INTERVAL = 10  # segundos entre cada heartbeat (mais frequente para detecção rápida)

# Navegadores suportados
SUPPORTED_BROWSERS = {
    'chrome.exe': 'Google Chrome',
    'msedge.exe': 'Microsoft Edge',
    'firefox.exe': 'Mozilla Firefox',
}

# URLs permitidas
ALLOWED_URLS = [
    'ava.anchieta.br'
]

# Processos/Apps a monitorar (suspeitos)
MONITORED_PROCESSES = [
    'whatsapp', 'telegram', 'discord', 'slack', 'teams',
    'notepad++', 'code', 'pycharm', 'visualstudio',
    'cmd', 'powershell', 'terminal',
    'anydesk', 'teamviewer', 'chrome remote desktop'
]

# Configurações de log
LOG_FILE = 'monitor.log'
LOG_LEVEL = 'INFO'

