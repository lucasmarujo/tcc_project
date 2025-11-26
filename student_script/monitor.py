"""
Script principal de monitoramento de alunos.
Monitora navegadores, processos do sistema e teclas especiais.
"""
import time
import logging
import socket
import psutil
import threading
from datetime import datetime
from typing import List, Dict, Optional

from config import (
    MONITORING_INTERVAL, HEARTBEAT_INTERVAL,
    SUPPORTED_BROWSERS, MONITORED_PROCESSES,
    LOG_FILE, LOG_LEVEL,
    get_student_info, get_student_registration, save_student_info
)
from browser_monitor import BrowserMonitor
from api_client import APIClient
from keyboard_monitor import KeyboardMonitor
from display_monitor import check_multiple_monitors, get_monitor_info_text
from webcam_monitor import WebcamMonitor
from screen_monitor import ScreenMonitor
from brightspace_detector import BrightspaceDetector  # 🆕 Detector de acesso indevido em provas
from pathlib import Path

# Configuração de logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class StudentMonitor:
    """Classe principal para monitoramento do aluno."""
    
    def __init__(self, registration_number: str, student_name: str = None, student_email: str = None):
        self.registration_number = registration_number
        self.student_name = student_name
        self.student_email = student_email
        self.api_client = APIClient(registration_number, student_name, student_email)
        self.browser_monitor = BrowserMonitor()
        self.keyboard_monitor = KeyboardMonitor(self._handle_keyboard_event)
        self.running = False
        self.machine_name = socket.gethostname()
        self.monitored_urls = set()
        self.monitored_apps = set()
        self.monitored_titles = set()  # Para evitar reportar títulos repetidos
        self.reported_key_events = set()  # Para evitar reportar teclas múltiplas vezes rapidamente
        
        # Webcam monitor
        model_path = Path(__file__).parent / 'face_detection_model' / 'yolov8m_200e.pt'
        self.webcam_monitor = WebcamMonitor(str(model_path), frame_callback=self._handle_webcam_frame)
        
        # Screen monitor
        self.screen_monitor = ScreenMonitor(frame_callback=self._handle_screen_frame)
        
        # Brightspace detector (detecção de acesso indevido durante provas)
        self.brightspace_detector = BrightspaceDetector(alert_callback=self._handle_brightspace_alert)
        
    def start(self):
        """Inicia o monitoramento."""
        logger.info("Iniciando monitoramento...")
        
        # Verificar múltiplos monitores
        has_multiple, num_monitors, monitor_info = check_multiple_monitors()
        
        if has_multiple:
            logger.error("=" * 60)
            logger.error("ERRO: MÚLTIPLOS MONITORES DETECTADOS!")
            logger.error("=" * 60)
            logger.error(f"Número de monitores: {num_monitors}")
            logger.error("")
            logger.error(get_monitor_info_text(monitor_info))
            logger.error("")
            logger.error("O monitoramento NÃO PODE ser iniciado com múltiplos monitores conectados.")
            logger.error("Por favor, desconecte os monitores adicionais e execute novamente.")
            logger.error("=" * 60)
            
            print()
            print("=" * 60)
            print("ERRO: MÚLTIPLOS MONITORES DETECTADOS!")
            print("=" * 60)
            print(f"\nNúmero de monitores: {num_monitors}\n")
            print(get_monitor_info_text(monitor_info))
            print("\nO monitoramento NÃO PODE ser iniciado com múltiplos monitores.")
            print("Por favor, desconecte os monitores adicionais e execute novamente.")
            print("=" * 60)
            
            return
        
        logger.info(f"Verificação de monitores: OK ({num_monitors} monitor detectado)")
        
        # Verificar conexão com servidor
        if not self.api_client.test_connection():
            logger.error("Não foi possível conectar ao servidor. Verifique a configuração.")
            return
        
        self.running = True
        
        # Iniciar monitor de teclado
        self.keyboard_monitor.start()
        
        # Conectar WebSocket para streaming de webcam
        logger.info("Conectando ao WebSocket para streaming de webcam...")
        if self.api_client.connect_webcam_stream():
            logger.info("WebSocket de webcam conectado, iniciando captura de webcam...")
            # Iniciar webcam monitor
            self.webcam_monitor.start()
        else:
            logger.warning("Não foi possível conectar ao WebSocket de webcam. Webcam não será transmitida.")
        
        # Conectar WebSocket para streaming de tela
        logger.info("Conectando ao WebSocket para streaming de tela...")
        if self.api_client.connect_screen_stream():
            logger.info("WebSocket de tela conectado, iniciando captura de tela...")
            # Iniciar screen monitor
            self.screen_monitor.start()
        else:
            logger.warning("Não foi possível conectar ao WebSocket de tela. Tela não será transmitida.")
        
        # Iniciar Brightspace detector
        logger.info("Iniciando detector de Brightspace/D2L...")
        logger.info("ATENÇÃO: Para funcionar corretamente, o Chrome deve ser iniciado com:")
        logger.info("  chrome.exe --remote-debugging-port=9222")
        self.brightspace_detector.start()
        
        # Iniciar threads
        monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        browser_thread = threading.Thread(target=self._browser_loop, daemon=True)
        heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        
        monitor_thread.start()
        browser_thread.start()
        heartbeat_thread.start()
        cleanup_thread.start()
        
        logger.info("Monitoramento ativo. Pressione Ctrl+C para parar.")
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Parando monitoramento...")
            self.running = False
            self.keyboard_monitor.stop()
            self.webcam_monitor.stop()
            self.screen_monitor.stop()
            self.brightspace_detector.stop()
            self.api_client.disconnect_webcam_stream()
            self.api_client.disconnect_screen_stream()
            self.api_client.disconnect_browser_stream()
    
    def _monitor_loop(self):
        """Loop principal de monitoramento (processos e relatórios lentos)."""
        while self.running:
            try:
                # Monitorar navegadores (scan completo menos frequente)
                self._check_browsers_full()
                
                # Monitorar processos
                self._check_processes()
                
                time.sleep(MONITORING_INTERVAL)
                
            except Exception as e:
                logger.error(f"Erro no loop de monitoramento: {e}", exc_info=True)
                time.sleep(MONITORING_INTERVAL)

    def _browser_loop(self):
        """Loop rápido (100ms) para monitorar janela ativa do navegador."""
        last_closed_hwnd = None  # Para evitar tentar fechar a mesma janela múltiplas vezes
        
        while self.running:
            try:
                # Obter info da janela ativa
                active_info = self.browser_monitor.get_active_window_info()
                
                if active_info:
                    # Adicionar timestamp
                    active_info['timestamp'] = datetime.now().isoformat()
                    
                    # Enviar via WebSocket
                    self.api_client.send_browser_data(active_info)
                    
                    # Se está bloqueado, fechar a janela imediatamente
                    if active_info.get('status') == 'blocked':
                        url = active_info.get('url')
                        hwnd = active_info.get('hwnd')
                        
                        if url and hwnd and hwnd != last_closed_hwnd:
                            logger.warning(f"⚠️ URL BLOQUEADA DETECTADA: {url}")
                            logger.warning(f"🚫 FECHANDO ABA AUTOMATICAMENTE...")
                            
                            # Tentar fechar a janela
                            if self.browser_monitor.close_browser_window(hwnd):
                                logger.warning(f"✅ Aba bloqueada fechada com sucesso!")
                                last_closed_hwnd = hwnd
                            else:
                                logger.error(f"❌ Falha ao fechar aba bloqueada")
                
                time.sleep(0.1)  # 100ms
                
            except Exception as e:
                logger.debug(f"Erro no loop rápido de browser: {e}")
                time.sleep(1.0)
    
    def _heartbeat_loop(self):
        """Loop de heartbeat para manter conexão com servidor."""
        while self.running:
            try:
                self.api_client.send_heartbeat()
                time.sleep(HEARTBEAT_INTERVAL)
            except Exception as e:
                logger.error(f"Erro ao enviar heartbeat: {e}")
                time.sleep(HEARTBEAT_INTERVAL)
    
    def _check_browsers_full(self):
        """Verifica URLs acessadas nos navegadores (Scan completo)."""
        # Este método continua existindo para capturar URLs em background ou abas inativas
        # mas a funcionalidade principal de tempo real agora é no _browser_loop
        for process in psutil.process_iter(['name', 'pid']):
            try:
                process_name = process.info['name'].lower()
                
                if process_name in SUPPORTED_BROWSERS:
                    browser_name = SUPPORTED_BROWSERS[process_name]
                    
                    # Obter URLs abertas no navegador (agora retorna dicionários)
                    url_infos = self.browser_monitor.get_browser_urls(process_name, process.info['pid'])
                    
                    for url_info in url_infos:
                        if not url_info or not url_info.get('url'):
                            continue
                        
                        url = url_info['url']
                        status = url_info.get('status', 'unknown')
                        match = url_info.get('match', None)
                        is_blocked = (status == 'blocked')
                        
                        # Verificar se é URL ou título
                        is_url = url.startswith('http://') or url.startswith('https://')
                        
                        # Criar chave única
                        if is_url:
                            url_key = f"url:{browser_name}:{url}"
                            check_set = self.monitored_urls
                        else:
                            url_key = f"title:{browser_name}:{url}"
                            check_set = self.monitored_titles
                        
                        # Evitar reportar múltiplas vezes
                        if url_key not in check_set:
                            check_set.add(url_key)
                            
                            # Reportar (passar informação se está bloqueada)
                            # Apenas reportamos EVENTOS para o banco de dados aqui
                            # A visualização em tempo real vai pelo WebSocket
                            self._report_url_access(url, browser_name, is_blocked, match)
                            
                            # Limitar o set para não crescer indefinidamente
                            if len(check_set) > 500:
                                # Manter apenas os últimos 250
                                items = list(check_set)
                                check_set.clear()
                                check_set.update(items[-250:])
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
            except Exception as e:
                logger.debug(f"Erro ao verificar processo: {e}")
                continue
    
    def _check_processes(self):
        """Verifica processos/aplicativos suspeitos em execução."""
        for process in psutil.process_iter(['name', 'pid', 'exe']):
            try:
                process_name = process.info['name'].lower()
                
                # Verificar se é um processo monitorado
                for monitored in MONITORED_PROCESSES:
                    if monitored in process_name:
                        # Usar apenas o nome do processo como chave (não o PID)
                        # para reportar apenas a primeira vez que detectar
                        app_key = f"app:{process_name}"
                        
                        if app_key not in self.monitored_apps:
                            self.monitored_apps.add(app_key)
                            
                            # Reportar abertura de aplicativo
                            self._report_app_launch(process.info['name'], process_name)
                            
                            # Limitar o set
                            if len(self.monitored_apps) > 200:
                                # Manter apenas os últimos 100
                                items = list(self.monitored_apps)
                                self.monitored_apps.clear()
                                self.monitored_apps.update(items[-100:])
                        
                        break
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
            except Exception as e:
                logger.debug(f"Erro ao verificar processo: {e}")
                continue
    
    def _report_url_access(self, url: str, browser: str, is_blocked: bool = False, blocked_domain: str = None):
        """Reporta acesso a uma URL para o servidor."""
        try:
            # Validar se a URL não está vazia
            if not url or url.strip() == '':
                return
            
            # Verificar se é uma URL válida ou apenas um título
            is_valid_url = url.startswith('http://') or url.startswith('https://')
            
            # Filtrar títulos que são erros ou não relevantes (já foi filtrado no browser_monitor, mas garantir)
            if not is_valid_url:
                url_lower = url.lower()
                error_indicators = ['erro', 'error', 'exception', 'traceback', 'módulo', 'module', 'python']
                
                # Se contém indicadores de erro, não reportar
                if any(indicator in url_lower for indicator in error_indicators):
                    logger.debug(f"Título filtrado como não relevante: {url}")
                    return
            
            if is_valid_url:
                # É uma URL válida, enviar como URL
                event_data = {
                    'event_type': 'url_access',
                    'url': url,
                    'browser': browser,
                    'machine_name': self.machine_name,
                    'additional_data': {
                        'timestamp': datetime.now().isoformat(),
                        'is_blocked': is_blocked
                    }
                }
                
                # Se for bloqueada, adicionar informações extras
                if is_blocked:
                    event_data['additional_data']['blocked_domain'] = blocked_domain
                    event_data['additional_data']['severity'] = 'high'
            else:
                # É apenas um título de janela, enviar como window_title
                event_data = {
                    'event_type': 'window_change',
                    'window_title': url,
                    'browser': browser,
                    'machine_name': self.machine_name,
                    'additional_data': {
                        'timestamp': datetime.now().isoformat(),
                        'note': 'Titulo de janela do navegador',
                        'is_blocked': is_blocked
                    }
                }
                
                if is_blocked:
                    event_data['additional_data']['blocked_domain'] = blocked_domain
                    event_data['additional_data']['severity'] = 'high'
            
            success = self.api_client.report_event(event_data)
            
            if success:
                tipo = "URL" if is_valid_url else "Titulo"
                blocked_msg = " [BLOQUEADA]" if is_blocked else ""
                logger.warning(f"{tipo} reportado{blocked_msg}: {url} ({browser})") if is_blocked else logger.info(f"{tipo} reportado: {url} ({browser})")
            else:
                logger.warning(f"Falha ao reportar: {url}")
                
        except Exception as e:
            logger.error(f"Erro ao reportar: {e}")
    
    def _report_app_launch(self, app_name: str, process_name: str):
        """Reporta abertura de aplicativo para o servidor."""
        try:
            event_data = {
                'event_type': 'app_launch',
                'app_name': app_name,
                'machine_name': self.machine_name,
                'additional_data': {
                    'process_name': process_name,
                    'timestamp': datetime.now().isoformat()
                }
            }
            
            success = self.api_client.report_event(event_data)
            
            if success:
                logger.info(f"Aplicativo reportado: {app_name}")
            else:
                logger.warning(f"Falha ao reportar aplicativo: {app_name}")
                
        except Exception as e:
            logger.error(f"Erro ao reportar aplicativo: {e}")
    
    def _handle_keyboard_event(self, event_name: str, event_data: dict):
        """
        Manipula eventos de teclado capturados pelo KeyboardMonitor.
        """
        try:
            # Criar chave única para o evento para evitar reportar múltiplas vezes
            event_key = f"{event_name}:{datetime.now().timestamp() // 2}"  # Agrupa por 2 segundos
            
            if event_key in self.reported_key_events:
                return
            
            self.reported_key_events.add(event_key)
            
            # Limitar o tamanho do set
            if len(self.reported_key_events) > 100:
                items = list(self.reported_key_events)
                self.reported_key_events.clear()
                self.reported_key_events.update(items[-50:])
            
            # Preparar dados do evento
            report_data = {
                'event_type': 'keyboard_event',
                'key_event': event_name,
                'machine_name': self.machine_name,
                'additional_data': event_data
            }
            
            # Enviar para o servidor
            success = self.api_client.report_event(report_data)
            
            if success:
                logger.warning(f"ALERTA: Tecla especial detectada: {event_data.get('description', event_name)}")
            else:
                logger.warning(f"Falha ao reportar evento de teclado: {event_name}")
        
        except Exception as e:
            logger.error(f"Erro ao processar evento de teclado: {e}", exc_info=True)
    
    def _handle_webcam_frame(self, frame_data: dict):
        """
        Manipula frames capturados pela webcam.
        Envia os frames para o servidor via WebSocket.
        """
        try:
            # Enviar frame via WebSocket
            success = self.api_client.send_webcam_frame(frame_data)
            
            if not success:
                logger.debug("Falha ao enviar frame da webcam")
            
            # Log de detecções (apenas se houver)
            if frame_data.get('detections'):
                detections = frame_data['detections']
                if len(detections) > 0:
                    logger.debug(f"Face detectada - {len(detections)} detecção(ões)")
        
        except Exception as e:
            logger.error(f"Erro ao processar frame da webcam: {e}", exc_info=True)
    
    def _handle_screen_frame(self, frame_data: dict):
        """
        Manipula frames capturados da tela.
        Envia os frames para o servidor via WebSocket.
        """
        try:
            # Enviar frame via WebSocket
            success = self.api_client.send_screen_frame(frame_data)
            
            if not success:
                logger.debug("Falha ao enviar frame da tela")
            
            # Log de detecções (apenas se houver)
            if frame_data.get('detections'):
                detections = frame_data['detections']
                if len(detections) > 0:
                    for det in detections:
                        class_name = det['class']
                        confidence = det['confidence']
                        
                        # Log diferentes dependendo da classe
                        if class_name == 'nao_permitido' and confidence > 0.6:
                            logger.warning(f"ALERTA TELA: Conteúdo suspeito detectado! (confiança: {confidence:.2f})")
                        else:
                            logger.debug(f"Detecção tela: {class_name} (confiança: {confidence:.2f})")
        
        except Exception as e:
            logger.error(f"Erro ao processar frame da tela: {e}", exc_info=True)
    
    def _handle_brightspace_alert(self, alert_data: dict):
        """
        Manipula alertas do detector do Brightspace.
        Envia alertas de acesso indevido durante provas para o servidor.
        
        Args:
            alert_data: Dados do alerta do Brightspace
        """
        try:
            alert_type = alert_data.get('alert_type', 'unknown')
            severity = alert_data.get('severity', 'info')
            page_type = alert_data.get('page_type', '')
            url = alert_data.get('url', '')
            message = alert_data.get('message', '')
            
            # 🆕 Preparar dados do evento baseado no tipo
            event_data = {
                'event_type': 'brightspace_event',
                'alert_type': alert_type,
                'machine_name': self.machine_name,
                'additional_data': {
                    'message': message,
                    'timestamp': alert_data.get('timestamp', datetime.now().isoformat()),
                    'severity': severity,
                    'url': url,
                    'page_type': page_type,
                    'access_type': alert_data.get('access_type', ''),
                    'quiz_duration': alert_data.get('quiz_duration', 0),
                    'is_in_quiz': alert_data.get('is_in_quiz', False)
                }
            }
            
            # 🆕 Adicionar informações extras baseado no tipo de evento
            if alert_type == 'page_view':
                # Evento de visualização normal de página
                if page_type == 'slides':
                    event_data['additional_data']['content_type'] = 'slides_conteudo'
                    event_data['additional_data']['action'] = 'visualizando_material'
                    # 🔥 MARCAR COMO ALERTA DE ALTA PRIORIDADE
                    event_data['additional_data']['is_alert'] = True
                    event_data['additional_data']['is_violation'] = True
                    event_data['additional_data']['violation_type'] = 'acesso_material_slides'
                    event_data['additional_data']['alert_reason'] = 'Aluno acessou slides/conteúdo do Brightspace'
                elif page_type == 'quiz':
                    event_data['additional_data']['content_type'] = 'prova_quiz'
                    event_data['additional_data']['action'] = 'acessou_prova'
                else:
                    event_data['additional_data']['content_type'] = 'outro_brightspace'
                    event_data['additional_data']['action'] = 'navegando'
            
            elif alert_type == 'unauthorized_access_during_quiz':
                # Acesso INDEVIDO durante prova - CRÍTICO
                event_data['additional_data']['violation_type'] = 'acesso_indevido_prova'
                event_data['additional_data']['is_violation'] = True
                
                # Verificar se é URL bloqueada também
                is_blocked, blocked_domain = self.browser_monitor.is_url_blocked(url)
                if is_blocked:
                    event_data['additional_data']['is_blocked_url'] = True
                    event_data['additional_data']['blocked_domain'] = blocked_domain
                    event_data['additional_data']['severity'] = 'critical'  # Elevar severidade
            
            # Enviar para o servidor
            success = self.api_client.report_event(event_data)
            
            # 🆕 Logs melhorados baseados no tipo e severidade
            if success:
                if alert_type == 'page_view':
                    # Visualização normal
                    if page_type == 'slides':
                        logger.error("=" * 80)
                        logger.error("⚠️  [ALERTA DE ALTA PRIORIDADE] SLIDES/CONTEÚDO DETECTADO!")
                        logger.error("=" * 80)
                        logger.error(f"   Aluno está visualizando MATERIAL/CONTEÚDO do Brightspace")
                        logger.error(f"   URL: {url}")
                        logger.error(f"   Status: {'🔴 EM PROVA - POSSÍVEL VIOLAÇÃO!' if alert_data.get('is_in_quiz') else '🟡 Navegação Normal'}")
                        logger.error(f"   Severidade: HIGH")
                        logger.error("   ✅ Evento enviado para o backend com sucesso")
                        logger.error("=" * 80)
                    elif page_type == 'quiz':
                        logger.info(f"📝 AVA: Aluno acessou página de prova")
                        logger.info(f"   URL: {url}")
                    else:
                        logger.info(f"🌐 AVA: Aluno navegando no Brightspace")
                        logger.debug(f"   URL: {url}")
                
                elif alert_type == 'unauthorized_access_during_quiz':
                    # Acesso indevido - CRÍTICO
                    logger.error("=" * 80)
                    logger.error(f"[ALERTA CRITICO] ACESSO INDEVIDO DURANTE PROVA!")
                    logger.error(f"   Mensagem: {message}")
                    logger.error(f"   URL acessada: {url}")
                    logger.error(f"   Tipo: {alert_data.get('access_type', 'desconhecido')}")
                    
                    # Verificar se também é URL bloqueada
                    is_blocked, blocked_domain = self.browser_monitor.is_url_blocked(url)
                    if is_blocked:
                        logger.error(f"   [ATENCAO] Esta URL tambem esta na lista de bloqueios!")
                        logger.error(f"   Dominio bloqueado: {blocked_domain}")
                    
                    logger.error("=" * 80)
                
                elif alert_type == 'quiz_started':
                    logger.warning("=" * 60)
                    logger.warning(f"[PROVA] PROVA INICIADA no Brightspace")
                    logger.warning(f"   URL: {url}")
                    logger.warning(f"   Monitoramento critico ATIVADO")
                    logger.warning("=" * 60)
                
                elif alert_type == 'quiz_ended':
                    duration = alert_data.get('quiz_duration', 0)
                    logger.info("=" * 60)
                    logger.info(f"[PROVA] PROVA FINALIZADA no Brightspace")
                    if duration:
                        logger.info(f"   Duracao: {duration:.0f} segundos ({duration/60:.1f} minutos)")
                    logger.info(f"   Monitoramento critico DESATIVADO")
                    logger.info("=" * 60)
                
                else:
                    logger.info(f"ℹ️  Evento Brightspace: {alert_type}")
            else:
                logger.warning(f"⚠️  Falha ao reportar evento Brightspace: {alert_type}")
        
        except Exception as e:
            logger.error(f"Erro ao processar alerta do Brightspace: {e}", exc_info=True)
    
    def _cleanup_loop(self):
        """Loop para limpar sets periodicamente."""
        while self.running:
            try:
                time.sleep(300)  # A cada 5 minutos
                
                # Limpar set de eventos de teclado
                if len(self.reported_key_events) > 50:
                    items = list(self.reported_key_events)
                    self.reported_key_events.clear()
                    self.reported_key_events.update(items[-25:])
                    logger.debug("Set de eventos de teclado limpo")
                
            except Exception as e:
                logger.error(f"Erro no loop de limpeza: {e}")


def main():
    """Função principal."""
    print("=" * 60)
    print("        SISTEMA DE MONITORAMENTO DE ALUNOS")
    print("=" * 60)
    print()
    print("Este programa monitora sua atividade durante exames.")
    print("Desenvolvido para garantir a integridade academica.")
    print()
    print("=" * 60)
    print()
    
    # Verificar se já tem informações salvas
    student_info = get_student_info()
    registration_number = None
    student_name = None
    student_email = None
    
    if student_info:
        registration_number = student_info.get('registration_number')
        student_name = student_info.get('name')
        student_email = student_info.get('email')
        
        print(f"[OK] Aluno identificado: Matricula {registration_number}")
        if student_name:
            print(f"[OK] Nome: {student_name}")
        print()
        resposta = input("Suas informacoes estao corretas? (S/n): ").strip().lower()
        if resposta == 'n':
            registration_number = None
            student_name = None
            student_email = None
    
    # Se não tem informações, coletar do aluno
    if not registration_number:
        print()
        print("PRIMEIRA EXECUCAO - Cadastro Inicial")
        print("-" * 60)
        print()
        
        while True:
            registration_number = input("Digite sua MATRICULA: ").strip()
            
            if not registration_number:
                print("[!] Por favor, informe sua matricula.")
                continue
            
            print()
            student_name = input("Digite seu NOME COMPLETO: ").strip()
            
            if not student_name:
                print("[!] Por favor, informe seu nome.")
                continue
            
            print()
            student_email = input("Digite seu EMAIL: ").strip()
            
            if not student_email or '@' not in student_email:
                print("[!] Por favor, informe um email valido.")
                continue
            
            print()
            print(f"Matricula: {registration_number}")
            print(f"Nome: {student_name}")
            print(f"Email: {student_email}")
            print()
            confirma = input("Confirma suas informacoes? (S/n): ").strip().lower()
            
            if confirma != 'n':
                # Salvar informações
                save_student_info(registration_number, student_name, student_email)
                print()
                print("[OK] Informacoes salvas com sucesso!")
                print("[OK] Nas proximas vezes, voce nao precisara informar novamente.")
                print()
                break
    
    print("=" * 60)
    print()
    
    # Iniciar monitoramento
    monitor = StudentMonitor(registration_number, student_name, student_email)
    monitor.start()


if __name__ == '__main__':
    main()

# Configuração de logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class StudentMonitor:
    """Classe principal para monitoramento do aluno."""
    
    def __init__(self, registration_number: str, student_name: str = None, student_email: str = None):
        self.registration_number = registration_number
        self.student_name = student_name
        self.student_email = student_email
        self.api_client = APIClient(registration_number, student_name, student_email)
        self.browser_monitor = BrowserMonitor()
        self.keyboard_monitor = KeyboardMonitor(self._handle_keyboard_event)
        self.running = False
        self.machine_name = socket.gethostname()
        self.monitored_urls = set()
        self.monitored_apps = set()
        self.monitored_titles = set()  # Para evitar reportar títulos repetidos
        self.reported_key_events = set()  # Para evitar reportar teclas múltiplas vezes rapidamente
        
        # Webcam monitor
        model_path = Path(__file__).parent / 'face_detection_model' / 'yolov8m_200e.pt'
        self.webcam_monitor = WebcamMonitor(str(model_path), frame_callback=self._handle_webcam_frame)
        
        # Screen monitor
        self.screen_monitor = ScreenMonitor(frame_callback=self._handle_screen_frame)
        
        # Brightspace detector (detecção de acesso indevido durante provas)
        self.brightspace_detector = BrightspaceDetector(alert_callback=self._handle_brightspace_alert)
        
    def start(self):
        """Inicia o monitoramento."""
        logger.info("Iniciando monitoramento...")
        
        # Verificar múltiplos monitores
        has_multiple, num_monitors, monitor_info = check_multiple_monitors()
        
        if has_multiple:
            logger.error("=" * 60)
            logger.error("ERRO: MÚLTIPLOS MONITORES DETECTADOS!")
            logger.error("=" * 60)
            logger.error(f"Número de monitores: {num_monitors}")
            logger.error("")
            logger.error(get_monitor_info_text(monitor_info))
            logger.error("")
            logger.error("O monitoramento NÃO PODE ser iniciado com múltiplos monitores conectados.")
            logger.error("Por favor, desconecte os monitores adicionais e execute novamente.")
            logger.error("=" * 60)
            
            print()
            print("=" * 60)
            print("ERRO: MÚLTIPLOS MONITORES DETECTADOS!")
            print("=" * 60)
            print(f"\nNúmero de monitores: {num_monitors}\n")
            print(get_monitor_info_text(monitor_info))
            print("\nO monitoramento NÃO PODE ser iniciado com múltiplos monitores.")
            print("Por favor, desconecte os monitores adicionais e execute novamente.")
            print("=" * 60)
            
            return
        
        logger.info(f"Verificação de monitores: OK ({num_monitors} monitor detectado)")
        
        # Verificar conexão com servidor
        if not self.api_client.test_connection():
            logger.error("Não foi possível conectar ao servidor. Verifique a configuração.")
            return
        
        self.running = True
        
        # Iniciar monitor de teclado
        self.keyboard_monitor.start()
        
        # Conectar WebSocket para streaming de webcam
        logger.info("Conectando ao WebSocket para streaming de webcam...")
        if self.api_client.connect_webcam_stream():
            logger.info("WebSocket de webcam conectado, iniciando captura de webcam...")
            # Iniciar webcam monitor
            self.webcam_monitor.start()
        else:
            logger.warning("Não foi possível conectar ao WebSocket de webcam. Webcam não será transmitida.")
        
        # Conectar WebSocket para streaming de tela
        logger.info("Conectando ao WebSocket para streaming de tela...")
        if self.api_client.connect_screen_stream():
            logger.info("WebSocket de tela conectado, iniciando captura de tela...")
            # Iniciar screen monitor
            self.screen_monitor.start()
        else:
            logger.warning("Não foi possível conectar ao WebSocket de tela. Tela não será transmitida.")
        
        # Iniciar Brightspace detector
        logger.info("Iniciando detector de Brightspace/D2L...")
        logger.info("ATENÇÃO: Para funcionar corretamente, o Chrome deve ser iniciado com:")
        logger.info("  chrome.exe --remote-debugging-port=9222")
        self.brightspace_detector.start()
        
        # Iniciar threads
        monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        
        monitor_thread.start()
        heartbeat_thread.start()
        cleanup_thread.start()
        
        logger.info("Monitoramento ativo. Pressione Ctrl+C para parar.")
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Parando monitoramento...")
            self.running = False
            self.keyboard_monitor.stop()
            self.webcam_monitor.stop()
            self.screen_monitor.stop()
            self.brightspace_detector.stop()
            self.api_client.disconnect_webcam_stream()
            self.api_client.disconnect_screen_stream()
    
    def _monitor_loop(self):
        """Loop principal de monitoramento."""
        while self.running:
            try:
                # Monitorar navegadores
                self._check_browsers()
                
                # Monitorar processos
                self._check_processes()
                
                time.sleep(MONITORING_INTERVAL)
                
            except Exception as e:
                logger.error(f"Erro no loop de monitoramento: {e}", exc_info=True)
                time.sleep(MONITORING_INTERVAL)
    
    def _heartbeat_loop(self):
        """Loop de heartbeat para manter conexão com servidor."""
        while self.running:
            try:
                self.api_client.send_heartbeat()
                time.sleep(HEARTBEAT_INTERVAL)
            except Exception as e:
                logger.error(f"Erro ao enviar heartbeat: {e}")
                time.sleep(HEARTBEAT_INTERVAL)
    
    def _check_browsers(self):
        """Verifica URLs acessadas nos navegadores."""
        for process in psutil.process_iter(['name', 'pid']):
            try:
                process_name = process.info['name'].lower()
                
                if process_name in SUPPORTED_BROWSERS:
                    browser_name = SUPPORTED_BROWSERS[process_name]
                    
                    # Obter URLs abertas no navegador
                    urls = self.browser_monitor.get_browser_urls(process_name, process.info['pid'])
                    
                    for url in urls:
                        if not url or url.strip() == '':
                            continue
                        
                        # Verificar se é URL ou título
                        is_url = url.startswith('http://') or url.startswith('https://')
                        
                        # Criar chave única
                        if is_url:
                            url_key = f"url:{browser_name}:{url}"
                            check_set = self.monitored_urls
                        else:
                            url_key = f"title:{browser_name}:{url}"
                            check_set = self.monitored_titles
                        
                        # Evitar reportar múltiplas vezes
                        if url_key not in check_set:
                            check_set.add(url_key)
                            
                            # Reportar
                            self._report_url_access(url, browser_name)
                            
                            # Limitar o set para não crescer indefinidamente
                            if len(check_set) > 500:
                                # Manter apenas os últimos 250
                                items = list(check_set)
                                check_set.clear()
                                check_set.update(items[-250:])
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
            except Exception as e:
                logger.debug(f"Erro ao verificar processo: {e}")
                continue
    
    def _check_processes(self):
        """Verifica processos/aplicativos suspeitos em execução."""
        for process in psutil.process_iter(['name', 'pid', 'exe']):
            try:
                process_name = process.info['name'].lower()
                
                # Verificar se é um processo monitorado
                for monitored in MONITORED_PROCESSES:
                    if monitored in process_name:
                        # Usar apenas o nome do processo como chave (não o PID)
                        # para reportar apenas a primeira vez que detectar
                        app_key = f"app:{process_name}"
                        
                        if app_key not in self.monitored_apps:
                            self.monitored_apps.add(app_key)
                            
                            # Reportar abertura de aplicativo
                            self._report_app_launch(process.info['name'], process_name)
                            
                            # Limitar o set
                            if len(self.monitored_apps) > 200:
                                # Manter apenas os últimos 100
                                items = list(self.monitored_apps)
                                self.monitored_apps.clear()
                                self.monitored_apps.update(items[-100:])
                        
                        break
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
            except Exception as e:
                logger.debug(f"Erro ao verificar processo: {e}")
                continue
    
    def _report_url_access(self, url: str, browser: str):
        """Reporta acesso a uma URL para o servidor."""
        try:
            # Validar se a URL não está vazia
            if not url or url.strip() == '':
                return
            
            # Verificar se é uma URL válida ou apenas um título
            is_valid_url = url.startswith('http://') or url.startswith('https://')
            
            # Filtrar títulos que são erros ou não relevantes (já foi filtrado no browser_monitor, mas garantir)
            if not is_valid_url:
                url_lower = url.lower()
                error_indicators = ['erro', 'error', 'exception', 'traceback', 'módulo', 'module', 'python']
                
                # Se contém indicadores de erro, não reportar
                if any(indicator in url_lower for indicator in error_indicators):
                    logger.debug(f"Título filtrado como não relevante: {url}")
                    return
            
            if is_valid_url:
                # É uma URL válida, enviar como URL
                event_data = {
                    'event_type': 'url_access',
                    'url': url,
                    'browser': browser,
                    'machine_name': self.machine_name,
                    'additional_data': {
                        'timestamp': datetime.now().isoformat()
                    }
                }
            else:
                # É apenas um título de janela, enviar como window_title
                event_data = {
                    'event_type': 'window_change',
                    'window_title': url,
                    'browser': browser,
                    'machine_name': self.machine_name,
                    'additional_data': {
                        'timestamp': datetime.now().isoformat(),
                        'note': 'Titulo de janela do navegador'
                    }
                }
            
            success = self.api_client.report_event(event_data)
            
            if success:
                tipo = "URL" if is_valid_url else "Titulo"
                logger.info(f"{tipo} reportado: {url} ({browser})")
            else:
                logger.warning(f"Falha ao reportar: {url}")
                
        except Exception as e:
            logger.error(f"Erro ao reportar: {e}")
    
    def _report_app_launch(self, app_name: str, process_name: str):
        """Reporta abertura de aplicativo para o servidor."""
        try:
            event_data = {
                'event_type': 'app_launch',
                'app_name': app_name,
                'machine_name': self.machine_name,
                'additional_data': {
                    'process_name': process_name,
                    'timestamp': datetime.now().isoformat()
                }
            }
            
            success = self.api_client.report_event(event_data)
            
            if success:
                logger.info(f"Aplicativo reportado: {app_name}")
            else:
                logger.warning(f"Falha ao reportar aplicativo: {app_name}")
                
        except Exception as e:
            logger.error(f"Erro ao reportar aplicativo: {e}")
    
    def _handle_keyboard_event(self, event_name: str, event_data: dict):
        """
        Manipula eventos de teclado capturados pelo KeyboardMonitor.
        
        Args:
            event_name: Nome do evento (ex: 'print_screen', 'ctrl_c', etc)
            event_data: Dados do evento
        """
        try:
            # Criar chave única para o evento para evitar reportar múltiplas vezes
            # nos primeiros segundos (usuário pode segurar a tecla)
            event_key = f"{event_name}:{datetime.now().timestamp() // 2}"  # Agrupa por 2 segundos
            
            if event_key in self.reported_key_events:
                return
            
            self.reported_key_events.add(event_key)
            
            # Limitar o tamanho do set
            if len(self.reported_key_events) > 100:
                items = list(self.reported_key_events)
                self.reported_key_events.clear()
                self.reported_key_events.update(items[-50:])
            
            # Preparar dados do evento
            report_data = {
                'event_type': 'keyboard_event',
                'key_event': event_name,
                'machine_name': self.machine_name,
                'additional_data': event_data
            }
            
            # Enviar para o servidor
            success = self.api_client.report_event(report_data)
            
            if success:
                logger.warning(f"ALERTA: Tecla especial detectada: {event_data.get('description', event_name)}")
            else:
                logger.warning(f"Falha ao reportar evento de teclado: {event_name}")
        
        except Exception as e:
            logger.error(f"Erro ao processar evento de teclado: {e}", exc_info=True)
    
    def _handle_webcam_frame(self, frame_data: dict):
        """
        Manipula frames capturados pela webcam.
        Envia os frames para o servidor via WebSocket.
        
        Args:
            frame_data: Dados do frame (incluindo imagem base64 e detecções)
        """
        try:
            # Enviar frame via WebSocket
            success = self.api_client.send_webcam_frame(frame_data)
            
            if not success:
                logger.debug("Falha ao enviar frame da webcam")
            
            # Log de detecções (apenas se houver)
            if frame_data.get('detections'):
                detections = frame_data['detections']
                if len(detections) > 0:
                    logger.debug(f"Face detectada - {len(detections)} detecção(ões)")
        
        except Exception as e:
            logger.error(f"Erro ao processar frame da webcam: {e}", exc_info=True)
    
    def _handle_screen_frame(self, frame_data: dict):
        """
        Manipula frames capturados da tela.
        Envia os frames para o servidor via WebSocket.
        
        Args:
            frame_data: Dados do frame (incluindo imagem base64)
        """
        try:
            # Enviar frame via WebSocket
            success = self.api_client.send_screen_frame(frame_data)
            
            if not success:
                logger.debug("Falha ao enviar frame da tela")
        
        except Exception as e:
            logger.error(f"Erro ao processar frame da tela: {e}", exc_info=True)
    
    def _handle_brightspace_alert(self, alert_data: dict):
        """
        Manipula alertas do detector do Brightspace.
        Envia alertas de acesso indevido durante provas para o servidor.
        
        Args:
            alert_data: Dados do alerta do Brightspace
        """
        try:
            alert_type = alert_data.get('alert_type', 'unknown')
            severity = alert_data.get('severity', 'info')
            page_type = alert_data.get('page_type', '')
            url = alert_data.get('url', '')
            message = alert_data.get('message', '')
            
            # 🆕 Preparar dados do evento baseado no tipo
            event_data = {
                'event_type': 'brightspace_event',
                'alert_type': alert_type,
                'machine_name': self.machine_name,
                'additional_data': {
                    'message': message,
                    'timestamp': alert_data.get('timestamp', datetime.now().isoformat()),
                    'severity': severity,
                    'url': url,
                    'page_type': page_type,
                    'access_type': alert_data.get('access_type', ''),
                    'quiz_duration': alert_data.get('quiz_duration', 0),
                    'is_in_quiz': alert_data.get('is_in_quiz', False)
                }
            }
            
            # 🆕 Adicionar informações extras baseado no tipo de evento
            if alert_type == 'page_view':
                # Evento de visualização normal de página
                if page_type == 'slides':
                    event_data['additional_data']['content_type'] = 'slides_conteudo'
                    event_data['additional_data']['action'] = 'visualizando_material'
                elif page_type == 'quiz':
                    event_data['additional_data']['content_type'] = 'prova_quiz'
                    event_data['additional_data']['action'] = 'acessou_prova'
                else:
                    event_data['additional_data']['content_type'] = 'outro_brightspace'
                    event_data['additional_data']['action'] = 'navegando'
            
            elif alert_type == 'unauthorized_access_during_quiz':
                # Acesso INDEVIDO durante prova - CRÍTICO
                event_data['additional_data']['violation_type'] = 'acesso_indevido_prova'
                event_data['additional_data']['is_violation'] = True
                
                # Verificar se é URL bloqueada também
                is_blocked, blocked_domain = self.browser_monitor.is_url_blocked(url)
                if is_blocked:
                    event_data['additional_data']['is_blocked_url'] = True
                    event_data['additional_data']['blocked_domain'] = blocked_domain
                    event_data['additional_data']['severity'] = 'critical'  # Elevar severidade
            
            # Enviar para o servidor
            success = self.api_client.report_event(event_data)
            
            # 🆕 Logs melhorados baseados no tipo e severidade
            if success:
                if alert_type == 'page_view':
                    # Visualização normal
                    if page_type == 'slides':
                        logger.warning("=" * 70)
                        logger.warning("[BACKEND] EVENTO REGISTRADO: Aluno visualizando SLIDES/CONTEUDO")
                        logger.warning(f"   URL: {url}")
                        logger.warning(f"   Status: {'EM PROVA [ALERTA]' if alert_data.get('is_in_quiz') else 'Navegacao Normal [OK]'}")
                        logger.warning("   [OK] Evento enviado para o backend com sucesso")
                        logger.warning("=" * 70)
                    elif page_type == 'quiz':
                        logger.info(f"📝 AVA: Aluno acessou página de prova")
                        logger.info(f"   URL: {url}")
                    else:
                        logger.info(f"🌐 AVA: Aluno navegando no Brightspace")
                        logger.debug(f"   URL: {url}")
                
                elif alert_type == 'unauthorized_access_during_quiz':
                    # Acesso indevido - CRÍTICO
                    logger.error("=" * 80)
                    logger.error(f"[ALERTA CRITICO] ACESSO INDEVIDO DURANTE PROVA!")
                    logger.error(f"   Mensagem: {message}")
                    logger.error(f"   URL acessada: {url}")
                    logger.error(f"   Tipo: {alert_data.get('access_type', 'desconhecido')}")
                    
                    # Verificar se também é URL bloqueada
                    is_blocked, blocked_domain = self.browser_monitor.is_url_blocked(url)
                    if is_blocked:
                        logger.error(f"   [ATENCAO] Esta URL tambem esta na lista de bloqueios!")
                        logger.error(f"   Dominio bloqueado: {blocked_domain}")
                    
                    logger.error("=" * 80)
                
                elif alert_type == 'quiz_started':
                    logger.warning("=" * 60)
                    logger.warning(f"[PROVA] PROVA INICIADA no Brightspace")
                    logger.warning(f"   URL: {url}")
                    logger.warning(f"   Monitoramento critico ATIVADO")
                    logger.warning("=" * 60)
                
                elif alert_type == 'quiz_ended':
                    duration = alert_data.get('quiz_duration', 0)
                    logger.info("=" * 60)
                    logger.info(f"[PROVA] PROVA FINALIZADA no Brightspace")
                    if duration:
                        logger.info(f"   Duracao: {duration:.0f} segundos ({duration/60:.1f} minutos)")
                    logger.info(f"   Monitoramento critico DESATIVADO")
                    logger.info("=" * 60)
                
                else:
                    logger.info(f"ℹ️  Evento Brightspace: {alert_type}")
            else:
                logger.warning(f"⚠️  Falha ao reportar evento Brightspace: {alert_type}")
        
        except Exception as e:
            logger.error(f"Erro ao processar alerta do Brightspace: {e}", exc_info=True)
    
    def _cleanup_loop(self):
        """Loop para limpar sets periodicamente."""
        while self.running:
            try:
                time.sleep(300)  # A cada 5 minutos
                
                # Limpar set de eventos de teclado
                if len(self.reported_key_events) > 50:
                    items = list(self.reported_key_events)
                    self.reported_key_events.clear()
                    self.reported_key_events.update(items[-25:])
                    logger.debug("Set de eventos de teclado limpo")
                
            except Exception as e:
                logger.error(f"Erro no loop de limpeza: {e}")


def main():
    """Função principal."""
    print("=" * 60)
    print("        SISTEMA DE MONITORAMENTO DE ALUNOS")
    print("=" * 60)
    print()
    print("Este programa monitora sua atividade durante exames.")
    print("Desenvolvido para garantir a integridade academica.")
    print()
    print("=" * 60)
    print()
    
    # Verificar se já tem informações salvas
    student_info = get_student_info()
    registration_number = None
    student_name = None
    student_email = None
    
    if student_info:
        registration_number = student_info.get('registration_number')
        student_name = student_info.get('name')
        student_email = student_info.get('email')
        
        print(f"[OK] Aluno identificado: Matricula {registration_number}")
        if student_name:
            print(f"[OK] Nome: {student_name}")
        print()
        resposta = input("Suas informacoes estao corretas? (S/n): ").strip().lower()
        if resposta == 'n':
            registration_number = None
            student_name = None
            student_email = None
    
    # Se não tem informações, coletar do aluno
    if not registration_number:
        print()
        print("PRIMEIRA EXECUCAO - Cadastro Inicial")
        print("-" * 60)
        print()
        
        while True:
            registration_number = input("Digite sua MATRICULA: ").strip()
            
            if not registration_number:
                print("[!] Por favor, informe sua matricula.")
                continue
            
            print()
            student_name = input("Digite seu NOME COMPLETO: ").strip()
            
            if not student_name:
                print("[!] Por favor, informe seu nome.")
                continue
            
            print()
            student_email = input("Digite seu EMAIL: ").strip()
            
            if not student_email or '@' not in student_email:
                print("[!] Por favor, informe um email valido.")
                continue
            
            print()
            print(f"Matricula: {registration_number}")
            print(f"Nome: {student_name}")
            print(f"Email: {student_email}")
            print()
            confirma = input("Confirma suas informacoes? (S/n): ").strip().lower()
            
            if confirma != 'n':
                # Salvar informações
                save_student_info(registration_number, student_name, student_email)
                print()
                print("[OK] Informacoes salvas com sucesso!")
                print("[OK] Nas proximas vezes, voce nao precisara informar novamente.")
                print()
                break
    
    print("=" * 60)
    print()
    
    # Iniciar monitoramento
    monitor = StudentMonitor(registration_number, student_name, student_email)
    monitor.start()


if __name__ == '__main__':
    main()

