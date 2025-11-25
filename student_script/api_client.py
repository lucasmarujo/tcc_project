"""
Cliente para comunicação com a API do servidor Django.
"""
import logging
import socket
import requests
import json
import threading
import time
from typing import Dict, Optional
import websocket

from config import REPORT_ENDPOINT, HEARTBEAT_ENDPOINT, SERVER_URL

logger = logging.getLogger(__name__)


class APIClient:
    """Cliente para interagir com a API do servidor."""
    
    def __init__(self, registration_number: str, student_name: str = None, student_email: str = None):
        self.registration_number = registration_number
        self.student_name = student_name
        self.student_email = student_email
        self.machine_name = socket.gethostname()
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'StudentMonitor/1.0'
        })
        
        # WebSocket para streaming de webcam
        self.ws = None
        self.ws_connected = False
        self.ws_thread = None
        self.ws_running = False
        
        # WebSocket para streaming de tela
        self.ws_screen = None
        self.ws_screen_connected = False
        self.ws_screen_thread = None
        self.ws_screen_running = False
        
        # WebSocket para browser data
        self.ws_browser = None
        self.ws_browser_connected = False
        self.ws_browser_thread = None
        self.ws_browser_running = False
    
    def test_connection(self) -> bool:
        """
        Testa a conexão com o servidor.
        
        Returns:
            True se conectado, False caso contrário
        """
        try:
            response = self.send_heartbeat()
            return response is not None
        except Exception as e:
            logger.error(f"Erro ao testar conexão: {e}")
            return False
    
    def send_heartbeat(self) -> Optional[Dict]:
        """
        Envia heartbeat para o servidor.
        Inclui nome, email e machine_name se disponíveis (para auto-cadastro).
        
        Returns:
            Resposta do servidor ou None em caso de erro
        """
        try:
            data = {
                'registration_number': self.registration_number,
                'machine_name': self.machine_name
            }
            
            # Adicionar nome e email se disponíveis (para cadastro automático)
            if self.student_name:
                data['student_name'] = self.student_name
            if self.student_email:
                data['student_email'] = self.student_email
            
            response = self.session.post(
                HEARTBEAT_ENDPOINT,
                json=data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                if result.get('new_student'):
                    logger.info(f"Aluno cadastrado automaticamente: {result.get('student')}")
                return result
            elif response.status_code == 404:
                # Aluno não existe e precisa de mais informações
                return response.json()
            else:
                logger.warning(f"Heartbeat falhou: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao enviar heartbeat: {e}")
            return None
    
    def report_event(self, event_data: Dict) -> bool:
        """
        Reporta um evento para o servidor.
        
        Args:
            event_data: Dicionário com dados do evento
            
        Returns:
            True se enviado com sucesso, False caso contrário
        """
        try:
            # Adicionar matrícula aos dados
            event_data['registration_number'] = self.registration_number
            
            response = self.session.post(
                REPORT_ENDPOINT,
                json=event_data,
                timeout=10
            )
            
            if response.status_code == 201:
                logger.debug(f"Evento reportado: {event_data.get('event_type')}")
                return True
            else:
                logger.warning(
                    f"Falha ao reportar evento: {response.status_code} - {response.text}"
                )
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao reportar evento: {e}")
            return False
    
    def get_monitoring_status(self) -> Optional[Dict]:
        """
        Obtém status do monitoramento do servidor.
        
        Returns:
            Status do monitoramento ou None
        """
        try:
            response = self.send_heartbeat()
            return response
        except Exception as e:
            logger.error(f"Erro ao obter status: {e}")
            return None
    
    def connect_webcam_stream(self) -> bool:
        """
        Conecta ao WebSocket para streaming de webcam.
        
        Returns:
            True se conectado com sucesso, False caso contrário
        """
        try:
            if self.ws_connected:
                logger.warning("WebSocket já está conectado")
                return True
            
            # Construir URL do WebSocket
            ws_url = SERVER_URL.replace('http://', 'ws://').replace('https://', 'wss://')
            ws_url = f"{ws_url}/ws/webcam/{self.registration_number}/"
            
            logger.info(f"Conectando WebSocket: {ws_url}")
            
            # Criar WebSocket
            self.ws = websocket.WebSocketApp(
                ws_url,
                on_open=self._on_ws_open,
                on_message=self._on_ws_message,
                on_error=self._on_ws_error,
                on_close=self._on_ws_close
            )
            
            # Iniciar thread do WebSocket
            self.ws_running = True
            self.ws_thread = threading.Thread(target=self._ws_run, daemon=True)
            self.ws_thread.start()
            
            # Aguardar conexão (timeout de 5 segundos)
            timeout = 5
            start_time = time.time()
            while not self.ws_connected and time.time() - start_time < timeout:
                time.sleep(0.1)
            
            if self.ws_connected:
                logger.info("WebSocket conectado com sucesso")
                return True
            else:
                logger.error("Timeout ao conectar WebSocket")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao conectar WebSocket: {e}", exc_info=True)
            return False
    
    def disconnect_webcam_stream(self):
        """Desconecta o WebSocket."""
        logger.info("Desconectando WebSocket...")
        self.ws_running = False
        
        if self.ws:
            self.ws.close()
        
        if self.ws_thread:
            self.ws_thread.join(timeout=3)
        
        self.ws_connected = False
        logger.info("WebSocket desconectado")
    
    def send_webcam_frame(self, frame_data: Dict) -> bool:
        """
        Envia um frame de webcam via WebSocket.
        
        Args:
            frame_data: Dicionário com dados do frame
            
        Returns:
            True se enviado com sucesso, False caso contrário
        """
        try:
            if not self.ws_connected or not self.ws:
                return False
            
            # Adicionar informações do aluno
            message = {
                'type': 'webcam_frame',
                'registration_number': self.registration_number,
                'student_name': self.student_name,
                'machine_name': self.machine_name,
                'data': frame_data
            }
            
            # Enviar via WebSocket (não bloqueante)
            message_json = json.dumps(message)
            self.ws.send(message_json)
            return True
            
        except Exception as e:
            # Não logar cada erro para não sobrecarregar
            if hasattr(self, '_last_error_log_time'):
                if time.time() - self._last_error_log_time > 5:  # Log a cada 5 segundos
                    logger.error(f"Erro ao enviar frame via WebSocket: {e}")
                    self._last_error_log_time = time.time()
            else:
                self._last_error_log_time = time.time()
            return False
    
    def _ws_run(self):
        """Thread que executa o WebSocket."""
        try:
            self.ws.run_forever()
        except Exception as e:
            logger.error(f"Erro no WebSocket run_forever: {e}")
    
    def _on_ws_open(self, ws):
        """Callback quando WebSocket é aberto."""
        logger.info("WebSocket aberto")
        self.ws_connected = True
    
    def _on_ws_message(self, ws, message):
        """Callback quando mensagem é recebida."""
        try:
            data = json.loads(message)
            logger.debug(f"Mensagem recebida do WebSocket: {data}")
        except Exception as e:
            logger.error(f"Erro ao processar mensagem do WebSocket: {e}")
    
    def _on_ws_error(self, ws, error):
        """Callback quando ocorre erro no WebSocket."""
        logger.error(f"Erro no WebSocket: {error}")
        self.ws_connected = False
    
    def _on_ws_close(self, ws, close_status_code, close_msg):
        """Callback quando WebSocket é fechado."""
        logger.info(f"WebSocket fechado: {close_status_code} - {close_msg}")
        self.ws_connected = False
    
    # ===== SCREEN SHARING WEBSOCKET =====
    
    def connect_screen_stream(self) -> bool:
        """
        Conecta ao WebSocket para streaming de tela.
        
        Returns:
            True se conectado com sucesso, False caso contrário
        """
        try:
            if self.ws_screen_connected:
                logger.warning("WebSocket de tela já está conectado")
                return True
            
            # Construir URL do WebSocket
            ws_url = SERVER_URL.replace('http://', 'ws://').replace('https://', 'wss://')
            ws_url = f"{ws_url}/ws/screen/{self.registration_number}/"
            
            logger.info(f"Conectando WebSocket de tela: {ws_url}")
            
            # Criar WebSocket
            self.ws_screen = websocket.WebSocketApp(
                ws_url,
                on_open=self._on_ws_screen_open,
                on_message=self._on_ws_screen_message,
                on_error=self._on_ws_screen_error,
                on_close=self._on_ws_screen_close
            )
            
            # Iniciar thread do WebSocket
            self.ws_screen_running = True
            self.ws_screen_thread = threading.Thread(target=self._ws_screen_run, daemon=True)
            self.ws_screen_thread.start()
            
            # Aguardar conexão (timeout de 5 segundos)
            timeout = 5
            start_time = time.time()
            while not self.ws_screen_connected and time.time() - start_time < timeout:
                time.sleep(0.1)
            
            if self.ws_screen_connected:
                logger.info("WebSocket de tela conectado com sucesso")
                return True
            else:
                logger.error("Timeout ao conectar WebSocket de tela")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao conectar WebSocket de tela: {e}", exc_info=True)
            return False
    
    def disconnect_screen_stream(self):
        """Desconecta o WebSocket de tela."""
        logger.info("Desconectando WebSocket de tela...")
        self.ws_screen_running = False
        
        if self.ws_screen:
            self.ws_screen.close()
        
        if self.ws_screen_thread:
            self.ws_screen_thread.join(timeout=3)
        
        self.ws_screen_connected = False
        logger.info("WebSocket de tela desconectado")
    
    def send_screen_frame(self, frame_data: Dict) -> bool:
        """
        Envia um frame de tela via WebSocket.
        
        Args:
            frame_data: Dicionário com dados do frame
            
        Returns:
            True se enviado com sucesso, False caso contrário
        """
        try:
            if not self.ws_screen_connected or not self.ws_screen:
                return False
            
            # Adicionar informações do aluno
            message = {
                'type': 'screen_frame',
                'registration_number': self.registration_number,
                'student_name': self.student_name,
                'machine_name': self.machine_name,
                'data': frame_data
            }
            
            # Enviar via WebSocket (não bloqueante)
            message_json = json.dumps(message)
            self.ws_screen.send(message_json)
            return True
            
        except Exception as e:
            # Não logar cada erro para não sobrecarregar
            if hasattr(self, '_last_screen_error_log_time'):
                if time.time() - self._last_screen_error_log_time > 5:
                    logger.error(f"Erro ao enviar frame de tela via WebSocket: {e}")
                    self._last_screen_error_log_time = time.time()
            else:
                self._last_screen_error_log_time = time.time()
            return False
    
    def _ws_screen_run(self):
        """Thread que executa o WebSocket de tela."""
        try:
            self.ws_screen.run_forever()
        except Exception as e:
            logger.error(f"Erro no WebSocket de tela run_forever: {e}")
    
    def _on_ws_screen_open(self, ws):
        """Callback quando WebSocket de tela é aberto."""
        logger.info("WebSocket de tela aberto")
        self.ws_screen_connected = True
    
    def _on_ws_screen_message(self, ws, message):
        """Callback quando mensagem é recebida."""
        try:
            data = json.loads(message)
            logger.debug(f"Mensagem recebida do WebSocket de tela: {data}")
        except Exception as e:
            logger.error(f"Erro ao processar mensagem do WebSocket de tela: {e}")
    
    def _on_ws_screen_error(self, ws, error):
        """Callback quando ocorre erro no WebSocket de tela."""
        logger.error(f"Erro no WebSocket de tela: {error}")
        self.ws_screen_connected = False
    
    def _on_ws_screen_close(self, ws, close_status_code, close_msg):
        """Callback quando WebSocket de tela é fechado."""
        logger.info(f"WebSocket de tela fechado: {close_status_code} - {close_msg}")
        self.ws_screen_connected = False

    # ===== BROWSER DATA WEBSOCKET =====
    
    def connect_browser_stream(self) -> bool:
        """Conecta ao WebSocket para dados de navegador."""
        try:
            if self.ws_browser_connected:
                return True
            
            # Construir URL do WebSocket
            ws_url = SERVER_URL.replace('http://', 'ws://').replace('https://', 'wss://')
            ws_url = f"{ws_url}/ws/browser/{self.registration_number}/"
            
            logger.info(f"Conectando WebSocket de browser: {ws_url}")
            
            self.ws_browser = websocket.WebSocketApp(
                ws_url,
                on_open=self._on_ws_browser_open,
                on_message=self._on_ws_browser_message,
                on_error=self._on_ws_browser_error,
                on_close=self._on_ws_browser_close
            )
            
            self.ws_browser_running = True
            self.ws_browser_thread = threading.Thread(target=self._ws_browser_run, daemon=True)
            self.ws_browser_thread.start()
            
            # Timeout
            timeout = 5
            start_time = time.time()
            while not self.ws_browser_connected and time.time() - start_time < timeout:
                time.sleep(0.1)
            
            if self.ws_browser_connected:
                logger.info("WebSocket de browser conectado com sucesso")
                return True
            else:
                logger.error("Timeout ao conectar WebSocket de browser")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao conectar WebSocket de browser: {e}", exc_info=True)
            return False

    def disconnect_browser_stream(self):
        """Desconecta o WebSocket de browser."""
        self.ws_browser_running = False
        if self.ws_browser:
            self.ws_browser.close()
        if self.ws_browser_thread:
            self.ws_browser_thread.join(timeout=3)
        self.ws_browser_connected = False

    def send_browser_data(self, data: Dict) -> bool:
        """Envia dados de navegação via WebSocket."""
        try:
            if not self.ws_browser_connected or not self.ws_browser:
                return False
            
            message = {
                'type': 'browser_data',
                'registration_number': self.registration_number,
                'data': data
            }
            
            self.ws_browser.send(json.dumps(message))
            return True
        except Exception as e:
            if hasattr(self, '_last_browser_error_log_time'):
                if time.time() - self._last_browser_error_log_time > 5:
                    logger.error(f"Erro ao enviar dados de browser: {e}")
                    self._last_browser_error_log_time = time.time()
            else:
                self._last_browser_error_log_time = time.time()
            return False

    def _ws_browser_run(self):
        try:
            self.ws_browser.run_forever()
        except Exception:
            pass

    def _on_ws_browser_open(self, ws):
        logger.info("WebSocket de browser aberto")
        self.ws_browser_connected = True

    def _on_ws_browser_message(self, ws, message):
        pass

    def _on_ws_browser_error(self, ws, error):
        logger.error(f"Erro no WebSocket de browser: {error}")
        self.ws_browser_connected = False

    def _on_ws_browser_close(self, ws, close_status_code, close_msg):
        self.ws_browser_connected = False
