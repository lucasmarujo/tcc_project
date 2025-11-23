"""
Monitor de webcam com detecção facial usando YOLO.
Captura frames da webcam, executa detecção com YOLO e envia para o servidor.
"""
import cv2
import logging
import threading
import time
import base64
import numpy as np
from pathlib import Path
from typing import Optional, Callable
from ultralytics import YOLO

logger = logging.getLogger(__name__)


class WebcamMonitor:
    """Classe para monitoramento de webcam com detecção facial YOLO."""
    
    def __init__(self, model_path: str, frame_callback: Optional[Callable] = None):
        """
        Inicializa o monitor de webcam.
        
        Args:
            model_path: Caminho para o modelo YOLO treinado
            frame_callback: Função callback para processar frames (recebe frame_data dict)
        """
        self.model_path = Path(model_path)
        self.frame_callback = frame_callback
        self.running = False
        self.capture = None
        self.model = None
        self.thread = None
        
        # Configurações
        self.fps_target = 30  # FPS para envio - aumentado para 30 FPS
        self.frame_width = 640  # Largura do frame redimensionado
        self.frame_height = 360  # Altura do frame redimensionado
        self.jpeg_quality = 50  # Qualidade JPEG reduzida para compensar mais FPS
        
        # Resolução menor para detecção YOLO (mais rápido)
        self.detection_width = 256  # Ainda menor para YOLO - mais performance
        self.detection_height = 144
        
        # Detectar apenas a cada N frames (economiza MUITO processamento)
        self.detect_every_n_frames = 6  # Detectar 1 a cada 6 frames (com 30 FPS = 5 detecções/seg)
        self.frames_since_detection = 0
        self.last_detections = []  # Cache das últimas detecções
        
        # Rastrear se há face detectada
        self.no_face_frames = 0  # Contador de frames sem detecção de face
        self.alert_threshold = 60  # Alertar após 60 frames sem face (2 segundos a 30 FPS)
        
        # Estatísticas
        self.frames_captured = 0
        self.frames_sent = 0
        self.last_frame_time = 0
        self.last_stats_time = time.time()
        self.total_bytes_sent = 0
        
    def initialize(self) -> bool:
        """
        Inicializa a webcam e o modelo YOLO.
        
        Returns:
            True se inicializado com sucesso, False caso contrário
        """
        try:
            # Verificar se o modelo existe
            if not self.model_path.exists():
                logger.error(f"Modelo YOLO não encontrado: {self.model_path}")
                return False
            
            logger.info(f"Carregando modelo YOLO: {self.model_path}")
            self.model = YOLO(str(self.model_path))
            logger.info("Modelo YOLO carregado com sucesso")
            
            # Inicializar webcam
            logger.info("Inicializando webcam...")
            self.capture = cv2.VideoCapture(0)
            
            if not self.capture.isOpened():
                logger.error("Não foi possível abrir a webcam")
                return False
            
            # Configurar resolução da webcam
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.frame_width)
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_height)
            
            # Testar captura
            ret, frame = self.capture.read()
            if not ret or frame is None:
                logger.error("Não foi possível capturar frame da webcam")
                return False
            
            logger.info(f"Webcam inicializada: {frame.shape[1]}x{frame.shape[0]}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao inicializar webcam/modelo: {e}", exc_info=True)
            return False
    
    def start(self):
        """Inicia o monitoramento em uma thread separada."""
        if self.running:
            logger.warning("Webcam monitor já está rodando")
            return
        
        if not self.initialize():
            logger.error("Falha ao inicializar webcam monitor")
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        logger.info("Webcam monitor iniciado")
    
    def stop(self):
        """Para o monitoramento."""
        logger.info("Parando webcam monitor...")
        self.running = False
        
        if self.thread:
            self.thread.join(timeout=5)
        
        if self.capture:
            self.capture.release()
        
        logger.info(f"Webcam monitor parado. Frames capturados: {self.frames_captured}, enviados: {self.frames_sent}")
    
    def _capture_loop(self):
        """Loop principal de captura e processamento."""
        frame_interval = 1.0 / self.fps_target
        
        while self.running:
            try:
                # Verificar se já passou tempo suficiente desde o último frame
                current_time = time.time()
                if current_time - self.last_frame_time < frame_interval:
                    time.sleep(0.005)  # Sleep menor para melhor timing
                    continue
                
                # Capturar frame
                ret, frame = self.capture.read()
                if not ret or frame is None:
                    logger.warning("Falha ao capturar frame")
                    time.sleep(0.1)
                    continue
                
                self.frames_captured += 1
                self.frames_since_detection += 1
                
                # Redimensionar para tamanho de exibição
                if frame.shape[1] != self.frame_width or frame.shape[0] != self.frame_height:
                    frame_display = cv2.resize(frame, (self.frame_width, self.frame_height), 
                                              interpolation=cv2.INTER_LINEAR)
                else:
                    frame_display = frame.copy()
                
                # Executar detecção YOLO apenas a cada N frames (OTIMIZAÇÃO CRÍTICA!)
                detections = []
                if self.frames_since_detection >= self.detect_every_n_frames:
                    self.frames_since_detection = 0
                    
                    # Redimensionar para tamanho de detecção (MUITO menor = MUITO mais rápido)
                    frame_detection = cv2.resize(frame, (self.detection_width, self.detection_height),
                                                interpolation=cv2.INTER_LINEAR)
                    
                    # Executar detecção YOLO
                    results = self.model(frame_detection, verbose=False, imgsz=256)
                    
                    # Calcular escala para mapear coordenadas de volta para frame de exibição
                    scale_x = self.frame_width / self.detection_width
                    scale_y = self.frame_height / self.detection_height
                    
                    if len(results) > 0 and results[0].boxes is not None:
                        boxes = results[0].boxes
                        
                        for box in boxes:
                            # Extrair informações da detecção
                            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                            confidence = float(box.conf[0].cpu().numpy())
                            class_id = int(box.cls[0].cpu().numpy())
                            
                            # Escalar coordenadas para o frame de exibição
                            x1 = x1 * scale_x
                            y1 = y1 * scale_y
                            x2 = x2 * scale_x
                            y2 = y2 * scale_y
                            
                            # Obter nome da classe REAL do modelo
                            class_name_original = self.model.names[class_id] if class_id in self.model.names else f"class_{class_id}"
                            
                            # Log para debug - mostrar o que o modelo retornou
                            if self.frames_captured <= 20:
                                logger.info(f"MODELO RETORNOU: classe_original='{class_name_original}' (ID={class_id}), confiança={confidence:.2f}")
                            
                            # SIMPLIFICADO: Se detectou qualquer coisa, considera como "face_detectada"
                            # O modelo yolov8m_200e.pt detecta faces, então qualquer detecção = face OK
                            detections.append({
                                'class': 'face_detectada',  # Sempre face detectada
                                'confidence': confidence,
                                'bbox': [float(x1), float(y1), float(x2), float(y2)],
                                'original_class': class_name_original  # Manter classe original para debug
                            })
                    
                    # Salvar detecções para usar nos próximos frames
                    self.last_detections = detections
                else:
                    # Usar detecções do frame anterior
                    detections = self.last_detections
                
                # Verificar se há face detectada
                # SIMPLES: Se tem detecções = tem face, se não tem = sem face
                has_face = len(detections) > 0
                if not has_face:
                    self.no_face_frames += 1
                else:
                    self.no_face_frames = 0
                
                # Desenhar bounding boxes no frame
                annotated_frame = frame_display.copy()
                for det in detections:
                    x1, y1, x2, y2 = det['bbox']
                    confidence = det['confidence']
                    
                    # SEMPRE VERDE - face detectada
                    color = (0, 255, 0)  # VERDE
                    thickness = 3 if confidence > 0.7 else 2
                    label = f"Face: {confidence:.2f}"
                    
                    # Desenhar retângulo verde ao redor da face
                    cv2.rectangle(annotated_frame, (int(x1), int(y1)), (int(x2), int(y2)), color, thickness)
                    
                    # Adicionar label com fundo verde
                    label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
                    cv2.rectangle(annotated_frame, (int(x1), int(y1) - label_size[1] - 10), 
                                (int(x1) + label_size[0], int(y1)), color, -1)
                    cv2.putText(annotated_frame, label, (int(x1), int(y1) - 5),
                              cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
                
                # Codificar frame anotado em JPEG
                encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.jpeg_quality]
                _, buffer = cv2.imencode('.jpg', annotated_frame, encode_param)
                
                # Converter para base64
                frame_base64 = base64.b64encode(buffer).decode('utf-8')
                
                # Preparar dados para envio
                frame_data = {
                    'frame': frame_base64,
                    'detections': detections,
                    'timestamp': current_time,
                    'frame_number': self.frames_captured,
                    'width': self.frame_width,
                    'height': self.frame_height,
                    'has_face': has_face,
                    'no_face_duration': self.no_face_frames / self.fps_target  # Duração em segundos
                }
                
                # Enviar via callback
                if self.frame_callback:
                    try:
                        self.frame_callback(frame_data)
                        self.frames_sent += 1
                        self.total_bytes_sent += len(frame_base64)
                    except Exception as e:
                        logger.error(f"Erro ao enviar frame via callback: {e}")
                
                self.last_frame_time = current_time
                
                # Log de estatísticas a cada 5 segundos
                if current_time - self.last_stats_time >= 5.0:
                    fps_real = self.frames_sent / (current_time - self.last_stats_time)
                    avg_frame_size = self.total_bytes_sent / self.frames_sent if self.frames_sent > 0 else 0
                    logger.info(f"Webcam Stats: {fps_real:.1f} FPS real, ~{avg_frame_size/1024:.1f}KB por frame")
                    self.last_stats_time = current_time
                    self.frames_sent = 0
                    self.total_bytes_sent = 0
                
            except Exception as e:
                logger.error(f"Erro no loop de captura: {e}", exc_info=True)
                time.sleep(0.5)
    
    def get_stats(self) -> dict:
        """
        Retorna estatísticas do monitor.
        
        Returns:
            Dicionário com estatísticas
        """
        return {
            'running': self.running,
            'frames_captured': self.frames_captured,
            'frames_sent': self.frames_sent,
            'fps_target': self.fps_target
        }


def test_webcam_monitor():
    """Função de teste para o monitor de webcam."""
    import os
    
    def print_frame_info(frame_data):
        """Callback de teste que imprime informações do frame."""
        print(f"Frame #{frame_data['frame_number']}: "
              f"{len(frame_data['detections'])} detecções, "
              f"tamanho: {len(frame_data['frame'])} bytes")
        
        for det in frame_data['detections']:
            print(f"  - {det['class']}: {det['confidence']:.2f}")
    
    # Caminho do modelo
    model_path = Path(__file__).parent / 'face_detection_model' / 'yolov8m_200e.pt'
    
    print(f"Testando WebcamMonitor...")
    print(f"Modelo: {model_path}")
    print(f"Pressione Ctrl+C para parar")
    print("-" * 60)
    
    monitor = WebcamMonitor(str(model_path), frame_callback=print_frame_info)
    
    try:
        monitor.start()
        
        # Deixar rodar por um tempo
        while True:
            time.sleep(1)
            stats = monitor.get_stats()
            print(f"Status: {stats}")
            
    except KeyboardInterrupt:
        print("\nParando...")
        monitor.stop()


if __name__ == '__main__':
    # Configurar logging para teste
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    test_webcam_monitor()

