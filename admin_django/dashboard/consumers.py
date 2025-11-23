"""
WebSocket consumers for real-time monitoring.
"""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from datetime import timedelta

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
        
        # Controle de alertas de face não detectada
        self.last_no_face_alert = None
        self.alert_cooldown = 30  # Segundos entre alertas
        
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
                'height': ...,
                'has_face': bool,
                'no_face_duration': float
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
                
                frame_data = message.get('data', {})
                detections = frame_data.get('detections', [])
                has_face = frame_data.get('has_face', False)
                no_face_duration = frame_data.get('no_face_duration', 0)
                
                # Verificar se há face detectada
                # SIMPLES: Se não detectou nada por 2+ segundos = alerta
                if not has_face and no_face_duration >= 2.0:
                    # Criar alerta se passou o cooldown
                    now = timezone.now()
                    should_alert = True
                    
                    if self.last_no_face_alert:
                        elapsed = (now - self.last_no_face_alert).total_seconds()
                        if elapsed < self.alert_cooldown:
                            should_alert = False
                    
                    if should_alert:
                        await self._create_no_face_alert(
                            message.get('registration_number'),
                            message.get('student_name', 'Desconhecido'),
                            no_face_duration
                        )
                        self.last_no_face_alert = now
                        logger.warning(
                            f"ALERTA: Face não detectada para aluno {self.registration_number} "
                            f"por {no_face_duration:.1f} segundos"
                        )
            
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar JSON: {e}")
        except Exception as e:
            logger.error(f"Erro ao processar mensagem da webcam: {e}", exc_info=True)
    
    @database_sync_to_async
    def _create_no_face_alert(self, registration_number, student_name, duration):
        """Cria alerta de face não detectada no banco de dados."""
        try:
            from students.models import Student
            from monitoring.models import Alert, MonitoringEvent
            
            # Buscar aluno
            student = Student.objects.filter(registration_number=registration_number).first()
            if not student:
                logger.error(f"Aluno não encontrado: {registration_number}")
                return
            
            # Criar evento de monitoramento
            event = MonitoringEvent.objects.create(
                student=student,
                event_type='other',
                description=f"Face não detectada por {duration:.1f} segundos",
                additional_data={
                    'type': 'no_face_detected',
                    'duration': duration,
                    'student_name': student_name
                }
            )
            
            # Criar alerta
            Alert.objects.create(
                event=event,
                student=student,
                severity='high',
                title='Face não detectada',
                description=f'O rosto do aluno {student_name} não foi detectado pela webcam por {duration:.1f} segundos.',
                reason='A face do aluno deve estar sempre visível durante o monitoramento'
            )
            
            logger.info(f"Alerta de face não detectada criado para {student_name}")
            
        except Exception as e:
            logger.error(f"Erro ao criar alerta de face não detectada: {e}", exc_info=True)
    


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


class ScreenConsumer(AsyncWebsocketConsumer):
    """Consumer para receber streaming de tela dos alunos."""
    
    async def connect(self):
        """Conecta ao WebSocket da tela de um aluno."""
        # Obter matrícula do aluno da URL
        self.registration_number = self.scope['url_route']['kwargs'].get('registration_number')
        
        if not self.registration_number:
            logger.error("Matrícula não fornecida na URL")
            await self.close()
            return
        
        # Nome do grupo para este aluno específico
        self.room_group_name = f'screen_{self.registration_number}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"WebSocket de tela conectado para aluno {self.registration_number}")
    
    async def disconnect(self, close_code):
        """Desconecta do WebSocket."""
        if hasattr(self, 'room_group_name'):
            # Leave room group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        
        logger.info(f"WebSocket de tela desconectado para aluno {self.registration_number}")
    
    async def receive(self, text_data):
        """
        Recebe frames de tela do aluno.
        
        Formato esperado:
        {
            'type': 'screen_frame',
            'registration_number': '...',
            'student_name': '...',
            'machine_name': '...',
            'data': {
                'frame': 'base64_encoded_image',
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
            
            if message_type == 'screen_frame':
                # Broadcast para todos os viewers conectados ao grupo deste aluno
                await self.channel_layer.group_send(
                    f'screen_view_{self.registration_number}',
                    {
                        'type': 'screen_frame_broadcast',
                        'message': message
                    }
                )
            
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar JSON de tela: {e}")
        except Exception as e:
            logger.error(f"Erro ao processar mensagem de tela: {e}", exc_info=True)


class ScreenViewerConsumer(AsyncWebsocketConsumer):
    """Consumer para viewers (admin) assistirem streams de tela."""
    
    async def connect(self):
        """Conecta ao WebSocket para visualizar tela de um aluno."""
        # Obter matrícula do aluno da URL
        self.registration_number = self.scope['url_route']['kwargs'].get('registration_number')
        
        if not self.registration_number:
            logger.error("Matrícula não fornecida na URL")
            await self.close()
            return
        
        # Verificar autenticação (usuário deve estar logado)
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            logger.warning(f"Tentativa de conexão não autenticada para visualizar tela")
            await self.close()
            return
        
        # Nome do grupo para visualizadores deste aluno
        self.room_group_name = f'screen_view_{self.registration_number}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        logger.info(f"Viewer de tela conectado para aluno {self.registration_number}")
    
    async def disconnect(self, close_code):
        """Desconecta do WebSocket."""
        if hasattr(self, 'room_group_name'):
            # Leave room group
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        
        logger.info(f"Viewer de tela desconectado para aluno {self.registration_number}")
    
    async def screen_frame_broadcast(self, event):
        """Envia frame da tela para o viewer."""
        try:
            message = event['message']
            await self.send(text_data=json.dumps(message))
        except Exception as e:
            logger.error(f"Erro ao enviar frame de tela para viewer: {e}")

