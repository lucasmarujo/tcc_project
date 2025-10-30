"""
Cliente para comunicação com a API do servidor Django.
"""
import logging
import requests
from typing import Dict, Optional

from config import REPORT_ENDPOINT, HEARTBEAT_ENDPOINT

logger = logging.getLogger(__name__)


class APIClient:
    """Cliente para interagir com a API do servidor."""
    
    def __init__(self, registration_number: str, student_name: str = None, student_email: str = None):
        self.registration_number = registration_number
        self.student_name = student_name
        self.student_email = student_email
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'User-Agent': 'StudentMonitor/1.0'
        })
    
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
        Inclui nome e email se disponíveis (para auto-cadastro).
        
        Returns:
            Resposta do servidor ou None em caso de erro
        """
        try:
            data = {
                'registration_number': self.registration_number
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

