"""
WebSocket consumers for real-time monitoring.
"""
import json
from channels.generic.websocket import AsyncWebsocketConsumer


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

