"""
WebSocket consumers for real-time monitoring.
"""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)


class MonitoringConsumer(AsyncWebsocketConsumer):
    """Consumer para atualizações em tempo real de monitoramento."""
    
    async def connect(self):
        """Conecta ao WebSocket."""
        self.room_group_name = 'monitoring_updates'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        """Desconecta do WebSocket."""
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Recebe mensagem do WebSocket."""
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type')
        
        # Processar diferentes tipos de mensagens se necessário
        if message_type == 'ping':
            await self.send(text_data=json.dumps({
                'type': 'pong'
            }))
    
    async def monitoring_event(self, event):
        """Envia evento de monitoramento para o WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'monitoring_event',
            'data': event['data']
        }))
    
    async def monitoring_alert(self, event):
        """Envia alerta de monitoramento para o WebSocket."""
        await self.send(text_data=json.dumps({
            'type': 'monitoring_alert',
            'data': event['data']
        }))


class WebcamConsumer(AsyncWebsocketConsumer):
    """Consumer para receber streaming de webcam dos alunos."""
    
    async def connect(self):
        """Conecta ao WebSocket da webcam de um aluno."""
        # Obter matrícula do aluno da URL
        self.registration_number = self.scope['url_route']['kwargs'].get('registration_number')
        
        if not self.registration_number:
            logger.error("Matrícula não fornecida na URL")
            await self.close()
            return
        
        # Nome do grupo para este aluno específico
        self.room_group_name = f'webcam_{self.registration_number}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"WebSocket conectado para aluno {self.registration_number}")
    
    async def disconnect(self, close_code):
        """Desconecta do WebSocket."""
        if hasattr(self, 'room_group_name'):
            # Leave room group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        
        logger.info(f"WebSocket desconectado para aluno {self.registration_number}")
    
    async def receive(self, text_data):
        """
        Recebe frames da webcam do aluno.
        
        Formato esperado:
        {
            'type': 'webcam_frame',
            'registration_number': '...',
            'student_name': '...',
            'machine_name': '...',
            'data': {
                'frame': 'base64_encoded_image',
                'detections': [...],
                'timestamp': ...,
                'frame_number': ...,
                'width': ...,
                'height': ...
            }
        }
        """
        try:
            message = json.loads(text_data)
            message_type = message.get('type')
            
            if message_type == 'webcam_frame':
                # Broadcast para todos os viewers conectados ao grupo deste aluno
                await self.channel_layer.group_send(
                    f'webcam_view_{self.registration_number}',
                    {
                        'type': 'webcam_frame_broadcast',
                        'message': message
                    }
                )
                
                # Log de detecções importantes
                detections = message.get('data', {}).get('detections', [])
                for det in detections:
                    if det.get('class') == 'nao_permitido':
                        logger.warning(
                            f"ALERTA: Situação não permitida detectada para aluno {self.registration_number} "
                            f"(confiança: {det.get('confidence', 0):.2f})"
                        )
            
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar JSON: {e}")
        except Exception as e:
            logger.error(f"Erro ao processar mensagem da webcam: {e}", exc_info=True)


class WebcamViewerConsumer(AsyncWebsocketConsumer):
    """Consumer para viewers (admin) assistirem streams de webcam."""
    
    async def connect(self):
        """Conecta ao WebSocket para visualizar webcam de um aluno."""
        # Obter matrícula do aluno da URL
        self.registration_number = self.scope['url_route']['kwargs'].get('registration_number')
        
        if not self.registration_number:
            logger.error("Matrícula não fornecida na URL")
            await self.close()
            return
        
        # Verificar autenticação (usuário deve estar logado)
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            logger.warning(f"Tentativa de conexão não autenticada para visualizar webcam")
            await self.close()
            return
        
        # Nome do grupo para visualizadores deste aluno
        self.room_group_name = f'webcam_view_{self.registration_number}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"Viewer conectado para aluno {self.registration_number}")
    
    async def disconnect(self, close_code):
        """Desconecta do WebSocket."""
        if hasattr(self, 'room_group_name'):
            # Leave room group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        
        logger.info(f"Viewer desconectado para aluno {self.registration_number}")
    
    async def webcam_frame_broadcast(self, event):
        """Envia frame da webcam para o viewer."""
        try:
            message = event['message']
            await self.send(text_data=json.dumps(message))
        except Exception as e:
            logger.error(f"Erro ao enviar frame para viewer: {e}")

