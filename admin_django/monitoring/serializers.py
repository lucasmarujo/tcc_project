"""
Serializers for Monitoring API.
"""
from rest_framework import serializers
from .models import MonitoringEvent, Alert
from students.models import Student


class MonitoringEventSerializer(serializers.ModelSerializer):
    """Serializer para eventos de monitoramento."""
    
    student_name = serializers.CharField(source='student.name', read_only=True)
    
    class Meta:
        model = MonitoringEvent
        fields = [
            'id', 'student', 'student_name', 'exam_session', 'event_type',
            'timestamp', 'url', 'browser', 'app_name', 'window_title',
            'key_event', 'machine_name', 'ip_address', 'additional_data'
        ]
        read_only_fields = ['id', 'timestamp', 'student_name']


class MonitoringEventCreateSerializer(serializers.Serializer):
    """Serializer para criação de eventos via API do script."""
    
    registration_number = serializers.CharField(required=True, write_only=True)
    event_type = serializers.ChoiceField(choices=MonitoringEvent.EVENT_TYPES)
    url = serializers.URLField(required=False, allow_blank=True)
    browser = serializers.CharField(required=False, allow_blank=True, max_length=50)
    app_name = serializers.CharField(required=False, allow_blank=True, max_length=200)
    window_title = serializers.CharField(required=False, allow_blank=True, max_length=500)
    key_event = serializers.CharField(required=False, allow_blank=True, max_length=100)
    machine_name = serializers.CharField(required=False, allow_blank=True, max_length=200)
    additional_data = serializers.JSONField(required=False, default=dict)
    
    def validate_registration_number(self, value):
        """Valida a matrícula do aluno."""
        try:
            student = Student.objects.get(registration_number=value, is_active=True)
            self.context['student'] = student
            return value
        except Student.DoesNotExist:
            raise serializers.ValidationError("Matrícula não encontrada ou aluno inativo.")
    
    def create(self, validated_data):
        """Cria o evento de monitoramento."""
        validated_data.pop('registration_number')
        student = self.context['student']
        
        # Obter IP da requisição
        request = self.context.get('request')
        if request:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0]
            else:
                ip_address = request.META.get('REMOTE_ADDR')
            validated_data['ip_address'] = ip_address
        
        event = MonitoringEvent.objects.create(
            student=student,
            **validated_data
        )
        
        # Verificar se deve criar alerta
        self._check_and_create_alert(event)
        
        return event
    
    def _check_and_create_alert(self, event):
        """Verifica se o evento deve gerar um alerta."""
        from django.conf import settings
        
        should_alert = False
        alert_title = ""
        alert_description = ""
        alert_reason = ""
        severity = "medium"
        
        # Verificar acesso a URL não permitida
        if event.event_type == 'url_access' and event.url:
            allowed = False
            for allowed_url in settings.ALLOWED_URLS:
                if allowed_url in event.url.lower():
                    allowed = True
                    break
            
            if not allowed:
                should_alert = True
                alert_title = "Acesso a URL não permitida"
                alert_description = f"Aluno acessou URL fora da lista permitida: {event.url}"
                alert_reason = "URL não está na whitelist de sites permitidos"
                
                # Verificar palavras-chave suspeitas para aumentar severidade
                url_lower = event.url.lower()
                for keyword in settings.SUSPICIOUS_KEYWORDS:
                    if keyword in url_lower:
                        severity = "high"
                        alert_reason += f" e contém palavra-chave suspeita: '{keyword}'"
                        break
        
        # Verificar abertura de aplicativo
        elif event.event_type == 'app_launch' and event.app_name:
            suspicious_apps = [
                'whatsapp', 'telegram', 'discord', 'slack', 'teams',
                'notepad++', 'vscode', 'pycharm', 'visualstudio',
                'cmd', 
            ]
            
            app_lower = event.app_name.lower()
            for sus_app in suspicious_apps:
                if sus_app in app_lower:
                    should_alert = True
                    alert_title = "Aplicativo suspeito detectado"
                    alert_description = f"Aluno abriu aplicativo: {event.app_name}"
                    alert_reason = f"Aplicativo '{event.app_name}' pode ser usado para trapaça"
                    severity = "medium"
                    break
        
        # Verificar eventos de teclado
        elif event.event_type == 'keyboard_event' and event.key_event:
            key_event = event.key_event.lower()
            description = event.additional_data.get('description', '')
            
            # Definir severidade baseada no tipo de tecla
            if 'print_screen' in key_event or 'win_shift_s' in key_event:
                should_alert = True
                alert_title = "Tentativa de captura de tela detectada"
                alert_description = f"Aluno tentou capturar a tela: {description}"
                alert_reason = "Captura de tela não é permitida durante o exame"
                severity = "high"
            
            elif 'f11' in key_event:
                should_alert = True
                alert_title = "Modo tela cheia detectado (F11)"
                alert_description = f"Aluno pressionou F11: {description}"
                alert_reason = "Tecla F11 pode indicar tentativa de ocultar atividades"
                severity = "medium"
            
            elif 'ctrl_c' in key_event or 'ctrl_v' in key_event:
                should_alert = True
                action = "copiou" if 'ctrl_c' in key_event else "colou"
                alert_title = f"Copiar/Colar detectado ({action})"
                alert_description = f"Aluno {action} conteúdo: {description}"
                alert_reason = f"Uso de {action} pode indicar consulta a fontes externas"
                severity = "medium"
        
        # 🆕 Verificar eventos de Brightspace (slides, acessos durante provas, etc)
        elif event.event_type == 'brightspace_event':
            # Verificar flags no additional_data
            additional_data = event.additional_data or {}
            is_alert_flagged = additional_data.get('is_alert', False)
            is_violation = additional_data.get('is_violation', False)
            page_type = additional_data.get('page_type', '')
            alert_type = additional_data.get('alert_type', '')
            
            # Se está marcado como alerta (slides ou acesso indevido)
            if is_alert_flagged or is_violation:
                should_alert = True
                
                # Determinar severidade
                event_severity = additional_data.get('severity', 'medium')
                if event_severity == 'high':
                    severity = 'high'
                elif event_severity == 'critical':
                    severity = 'critical'
                else:
                    severity = 'medium'
                
                # Título e descrição baseados no tipo
                if page_type == 'slides':
                    alert_title = "⚠️ Acesso a Slides/Conteúdo do Brightspace"
                    url_accessed = additional_data.get('url', 'URL não informada')
                    is_in_quiz = additional_data.get('is_in_quiz', False)
                    
                    if is_in_quiz:
                        alert_description = f"🔴 ALERTA CRÍTICO: Aluno acessou material/slides DURANTE UMA PROVA!"
                        alert_reason = f"Acesso a conteúdo do AVA durante prova é considerado violação. URL: {url_accessed}"
                        severity = 'critical'
                    else:
                        alert_description = f"Aluno acessou slides/conteúdo do Brightspace/AVA"
                        alert_reason = additional_data.get('alert_reason', f"Acesso a material de estudo detectado. URL: {url_accessed}")
                
                elif alert_type == 'unauthorized_access_during_quiz':
                    alert_title = "🔴 ACESSO INDEVIDO DURANTE PROVA"
                    alert_description = additional_data.get('message', 'Acesso não autorizado detectado durante prova')
                    alert_reason = f"Tipo de acesso: {additional_data.get('access_type', 'desconhecido')}. URL: {additional_data.get('url', 'N/A')}"
                    severity = 'critical'
                
                else:
                    # Outro tipo de evento do Brightspace marcado como alerta
                    alert_title = f"Alerta Brightspace: {alert_type}"
                    alert_description = additional_data.get('message', 'Evento suspeito no Brightspace')
                    alert_reason = additional_data.get('alert_reason', 'Evento marcado como alerta pelo sistema')
        
        # Criar alerta se necessário
        if should_alert:
            Alert.objects.create(
                event=event,
                student=event.student,
                severity=severity,
                title=alert_title,
                description=alert_description,
                reason=alert_reason
            )


class AlertSerializer(serializers.ModelSerializer):
    """Serializer para alertas."""
    
    student_name = serializers.CharField(source='student.name', read_only=True)
    event_details = MonitoringEventSerializer(source='event', read_only=True)
    
    class Meta:
        model = Alert
        fields = [
            'id', 'event', 'event_details', 'student', 'student_name',
            'severity', 'status', 'title', 'description', 'reason',
            'created_at', 'updated_at', 'resolved_at', 'admin_notes'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

