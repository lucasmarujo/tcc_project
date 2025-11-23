"""
Monitor de tela para captura e transmissão da tela do aluno.
Captura screenshots da tela, redimensiona e envia para o servidor.
"""
import logging
import threading
import time
import base64
import numpy as np
from io import BytesIO
from typing import Optional, Callable
from PIL import Image
from ultralytics import YOLO

# Tentar importar MSS (mais rápido que PIL ImageGrab)
try:
    import mss
    MSS_AVAILABLE = True
except ImportError:
    from PIL import ImageGrab
    MSS_AVAILABLE = False

logger = logging.getLogger(__name__)


class ScreenMonitor:
    """Classe para monitoramento e captura da tela do aluno."""
    
    def __init__(self, frame_callback: Optional[Callable] = None, model_path: str = None, enable_detection: bool = True):
        """
        Inicializa o monitor de tela.
        
        Args:
            frame_callback: Função callback para processar frames (recebe frame_data dict)
            model_path: Caminho para o modelo YOLO de detecção (opcional)
            enable_detection: Habilitar detecção YOLO na tela
        """
        self.frame_callback = frame_callback
        self.running = False
        self.thread = None
        self.enable_detection = enable_detection
        self.model = None
        self.model_path = model_path
        
        # Configurações otimizadas para screen sharing
        self.fps_target = 10  # FPS aumentado de 5 para 10
        self.frame_width = 960  # Largura do frame (resolução média)
        self.frame_height = 540  # Altura do frame (540p)
        self.jpeg_quality = 60  # Qualidade JPEG otimizada
        
        # Configurações de detecção YOLO (se habilitado)
        self.detection_width = 640  # Resolução para detecção YOLO
        self.detection_height = 360
        self.detect_every_n_frames = 5  # Detectar apenas a cada 5 frames (economizar processamento)
        self.frames_since_detection = 0
        self.last_detections = []
        
        # MSS (mais rápido que PIL)
        self.use_mss = MSS_AVAILABLE
        self.sct = None
        if self.use_mss:
            try:
                self.sct = mss.mss()
                logger.info("Usando MSS para captura de tela (mais rápido)")
            except Exception as e:
                logger.warning(f"Erro ao inicializar MSS: {e}. Usando PIL ImageGrab")
                self.use_mss = False
        else:
            logger.info("MSS não disponível, usando PIL ImageGrab")
        
        # Estatísticas
        self.frames_captured = 0
        self.frames_sent = 0
        self.last_frame_time = 0
        self.last_stats_time = time.time()
        self.total_bytes_sent = 0
        
    def _initialize_model(self) -> bool:
        """
        Inicializa o modelo YOLO para detecção.
        
        Returns:
            True se inicializado com sucesso, False caso contrário
        """
        if not self.enable_detection:
            logger.info("Detecção YOLO desabilitada para screen monitor")
            return True
        
        try:
            # Se não foi especificado um caminho, tentar usar o modelo padrão
            if not self.model_path:
                from pathlib import Path
                # Tentar o modelo treinado para screen
                default_path = Path(__file__).parent.parent / 'yolov8_model' / 'scripts' / 'models' / 'final_model' / 'best.pt'
                if default_path.exists():
                    self.model_path = str(default_path)
                    logger.info(f"Usando modelo padrão: {self.model_path}")
                else:
                    logger.warning("Modelo YOLO não encontrado. Detecção será desabilitada.")
                    self.enable_detection = False
                    return True
            
            logger.info(f"Carregando modelo YOLO para screen: {self.model_path}")
            self.model = YOLO(str(self.model_path))
            
            # Tentar usar GPU se disponível
            try:
                import torch
                if torch.cuda.is_available():
                    self.model.to('cuda')
                    logger.info("Modelo YOLO usando GPU")
                else:
                    logger.info("GPU não disponível, usando CPU")
            except Exception as e:
                logger.info(f"GPU não disponível: {e}")
            
            logger.info("Modelo YOLO carregado com sucesso para screen monitor")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao carregar modelo YOLO: {e}", exc_info=True)
            self.enable_detection = False
            return False
    
    def start(self):
        """Inicia o monitoramento em uma thread separada."""
        if self.running:
            logger.warning("Screen monitor já está rodando")
            return
        
        logger.info("Iniciando screen monitor...")
        
        # Inicializar modelo se necessário
        if self.enable_detection:
            self._initialize_model()
        
        self.running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        logger.info("Screen monitor iniciado")
    
    def stop(self):
        """Para o monitoramento."""
        logger.info("Parando screen monitor...")
        self.running = False
        
        if self.thread:
            self.thread.join(timeout=5)
        
        # Fechar MSS se estiver em uso
        if self.sct:
            try:
                self.sct.close()
            except Exception as e:
                logger.debug(f"Erro ao fechar MSS: {e}")
        
        logger.info(f"Screen monitor parado. Frames capturados: {self.frames_captured}, enviados: {self.frames_sent}")
    
    def _capture_loop(self):
        """Loop principal de captura da tela - otimizado para streaming fluido."""
        frame_interval = 1.0 / self.fps_target
        next_frame_time = time.time()
        
        while self.running:
            try:
                # Controle de timing mais preciso
                current_time = time.time()
                time_since_last = current_time - self.last_frame_time
                
                if time_since_last < frame_interval:
                    # Sleep apenas o tempo necessário (mais preciso)
                    time.sleep(max(0.001, frame_interval - time_since_last))
                    continue
                
                # Capturar screenshot da tela (MSS ou PIL)
                if self.use_mss and self.sct:
                    # Usar MSS (muito mais rápido)
                    monitor = self.sct.monitors[1]  # Monitor principal
                    screenshot_raw = self.sct.grab(monitor)
                    # Converter para PIL Image
                    screenshot = Image.frombytes('RGB', screenshot_raw.size, screenshot_raw.bgra, 'raw', 'BGRX')
                else:
                    # Fallback para PIL ImageGrab
                    from PIL import ImageGrab
                    screenshot = ImageGrab.grab()
                
                if screenshot is None:
                    logger.warning("Falha ao capturar screenshot")
                    time.sleep(0.1)
                    continue
                
                self.frames_captured += 1
                self.frames_since_detection += 1
                
                # Obter dimensões originais
                original_width, original_height = screenshot.size
                
                # Calcular aspect ratio e redimensionar mantendo proporção
                aspect_ratio = original_width / original_height
                
                if aspect_ratio > (self.frame_width / self.frame_height):
                    # Largura é o limitante
                    new_width = self.frame_width
                    new_height = int(self.frame_width / aspect_ratio)
                else:
                    # Altura é o limitante
                    new_height = self.frame_height
                    new_width = int(self.frame_height * aspect_ratio)
                
                # Redimensionar usando PIL com método mais rápido
                img_resized = screenshot.resize((new_width, new_height), Image.BILINEAR)  # BILINEAR é mais rápido
                
                # Executar detecção YOLO a cada N frames (se habilitado)
                detections = []
                if self.enable_detection and self.model and self.frames_since_detection >= self.detect_every_n_frames:
                    self.frames_since_detection = 0
                    
                    try:
                        # Redimensionar para resolução de detecção
                        img_detection = screenshot.resize((self.detection_width, self.detection_height), Image.BILINEAR)
                        
                        # Converter para numpy array
                        img_array = np.array(img_detection)
                        
                        # Executar detecção YOLO (classificação)
                        results = self.model(img_array, verbose=False)
                        
                        if len(results) > 0:
                            # Para modelo de classificação
                            if hasattr(results[0], 'probs') and results[0].probs is not None:
                                probs = results[0].probs
                                top_class = int(probs.top1)
                                confidence = float(probs.top1conf)
                                class_name = self.model.names[top_class] if top_class in self.model.names else f"class_{top_class}"
                                
                                detections.append({
                                    'class': class_name,
                                    'confidence': confidence,
                                    'type': 'classification'
                                })
                            # Para modelo de detecção de objetos
                            elif hasattr(results[0], 'boxes') and results[0].boxes is not None:
                                boxes = results[0].boxes
                                for box in boxes:
                                    confidence = float(box.conf[0])
                                    class_id = int(box.cls[0])
                                    class_name = self.model.names[class_id] if class_id in self.model.names else f"class_{class_id}"
                                    
                                    detections.append({
                                        'class': class_name,
                                        'confidence': confidence,
                                        'type': 'detection'
                                    })
                        
                        # Salvar detecções
                        self.last_detections = detections
                        
                        # Log de detecções suspeitas
                        for det in detections:
                            if det['class'] == 'nao_permitido' and det['confidence'] > 0.6:
                                logger.warning(f"ALERTA: Conteúdo suspeito detectado na tela! (confiança: {det['confidence']:.2f})")
                    
                    except Exception as e:
                        logger.debug(f"Erro na detecção YOLO: {e}")
                else:
                    # Usar detecções anteriores
                    detections = self.last_detections
                
                # Converter para JPEG em memória (sem optimize para velocidade)
                buffer = BytesIO()
                img_resized.save(buffer, format='JPEG', quality=self.jpeg_quality, optimize=False)
                buffer.seek(0)
                
                # Converter para base64
                frame_base64 = base64.b64encode(jpeg_data).decode('utf-8')
                
                # Preparar dados para envio
                frame_data = {
                    'frame': frame_base64,
                    'timestamp': current_time,
                    'frame_number': self.frames_captured,
                    'width': new_width,
                    'height': new_height,
                    'original_width': original_width,
                    'original_height': original_height,
                    'detections': detections if self.enable_detection else []
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
                
                # Log de estatísticas a cada 10 segundos
                if current_time - self.last_stats_time >= 10.0:
                    fps_real = self.frames_sent / (current_time - self.last_stats_time)
                    avg_frame_size = self.total_bytes_sent / self.frames_sent if self.frames_sent > 0 else 0
                    logger.info(f"Screen Stats: {fps_real:.1f} FPS real, ~{avg_frame_size/1024:.1f}KB por frame")
                    self.last_stats_time = current_time
                    self.frames_sent = 0
                    self.total_bytes_sent = 0
                
            except Exception as e:
                logger.error(f"Erro no loop de captura de tela: {e}", exc_info=True)
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


def test_screen_monitor():
    """Função de teste para o monitor de tela."""
    
    def print_frame_info(frame_data):
        """Callback de teste que imprime informações do frame."""
        print(f"Frame #{frame_data['frame_number']}: "
              f"{frame_data['width']}x{frame_data['height']}, "
              f"tamanho: {len(frame_data['frame'])} bytes")
    
    print("Testando ScreenMonitor...")
    print("Pressione Ctrl+C para parar")
    print("-" * 60)
    
    monitor = ScreenMonitor(frame_callback=print_frame_info)
    
    try:
        monitor.start()
        
        # Deixar rodar
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
    
    test_screen_monitor()

"""
Monitor de tela para captura e transmissão da tela do aluno.
Captura screenshots da tela, redimensiona e envia para o servidor.
"""
import logging
import threading
import time
import base64
import numpy as np
from io import BytesIO
from typing import Optional, Callable
from PIL import Image, ImageGrab

logger = logging.getLogger(__name__)


class ScreenMonitor:
    """Classe para monitoramento e captura da tela do aluno."""
    
    def __init__(self, frame_callback: Optional[Callable] = None):
        """
        Inicializa o monitor de tela.
        
        Args:
            frame_callback: Função callback para processar frames (recebe frame_data dict)
        """
        self.frame_callback = frame_callback
        self.running = False
        self.thread = None
        
        # Configurações otimizadas para screen sharing sem flickering
        self.fps_target = 15  # FPS ideal para screen sharing (5 FPS = suave e sem flickering)
        self.frame_width = 960  # Largura do frame (resolução média)
        self.frame_height = 540  # Altura do frame (540p)
        self.jpeg_quality = 50  # Qualidade JPEG otimizada para tela
        
        # Estatísticas
        self.frames_captured = 0
        self.frames_sent = 0
        self.last_frame_time = 0
        self.last_stats_time = time.time()
        self.total_bytes_sent = 0
        
    def start(self):
        """Inicia o monitoramento em uma thread separada."""
        if self.running:
            logger.warning("Screen monitor já está rodando")
            return
        
        logger.info("Iniciando screen monitor...")
        self.running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        logger.info("Screen monitor iniciado")
    
    def stop(self):
        """Para o monitoramento."""
        logger.info("Parando screen monitor...")
        self.running = False
        
        if self.thread:
            self.thread.join(timeout=5)
        
        logger.info(f"Screen monitor parado. Frames capturados: {self.frames_captured}, enviados: {self.frames_sent}")
    
    def _capture_loop(self):
        """Loop principal de captura da tela - otimizado para streaming fluido."""
        frame_interval = 1.0 / self.fps_target
        next_frame_time = time.time()
        
        while self.running:
            try:
                # Controle de timing mais preciso
                current_time = time.time()
                if current_time < next_frame_time:
                    # Sleep adaptativo para não sobrecarregar CPU
                    sleep_time = min(next_frame_time - current_time, 0.005)
                    time.sleep(sleep_time)
                    continue
                
                # Atualizar próximo frame time
                next_frame_time = current_time + frame_interval
                
                # Capturar screenshot da tela (usando PIL diretamente é mais rápido)
                screenshot = ImageGrab.grab()
                
                if screenshot is None:
                    logger.warning("Falha ao capturar screenshot")
                    time.sleep(0.1)
                    continue
                
                self.frames_captured += 1
                
                # Obter dimensões originais diretamente do PIL Image
                original_width, original_height = screenshot.size
                
                # Calcular aspect ratio e redimensionar mantendo proporção
                aspect_ratio = original_width / original_height
                
                if aspect_ratio > (self.frame_width / self.frame_height):
                    # Largura é o limitante
                    new_width = self.frame_width
                    new_height = int(self.frame_width / aspect_ratio)
                else:
                    # Altura é o limitante
                    new_height = self.frame_height
                    new_width = int(self.frame_height * aspect_ratio)
                
                # Redimensionar usando BILINEAR (mais rápido que LANCZOS, qualidade boa)
                img_resized = screenshot.resize((new_width, new_height), Image.BILINEAR)
                
                # Converter para JPEG em memória com otimizações
                buffer = BytesIO()
                # progressive=True melhora loading no browser, optimize=False é mais rápido
                img_resized.save(buffer, format='JPEG', quality=self.jpeg_quality, 
                               progressive=True, optimize=False)
                jpeg_data = buffer.getvalue()
                
                # Converter para base64
                frame_base64 = base64.b64encode(jpeg_data).decode('utf-8')
                
                # Preparar dados para envio
                frame_data = {
                    'frame': frame_base64,
                    'timestamp': current_time,
                    'frame_number': self.frames_captured,
                    'width': new_width,
                    'height': new_height,
                    'original_width': original_width,
                    'original_height': original_height
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
                
                # Log de estatísticas a cada 10 segundos
                if current_time - self.last_stats_time >= 10.0:
                    fps_real = self.frames_sent / (current_time - self.last_stats_time)
                    avg_frame_size = self.total_bytes_sent / self.frames_sent if self.frames_sent > 0 else 0
                    logger.info(f"Screen Stats: {fps_real:.1f} FPS real, ~{avg_frame_size/1024:.1f}KB por frame")
                    self.last_stats_time = current_time
                    self.frames_sent = 0
                    self.total_bytes_sent = 0
                
            except Exception as e:
                logger.error(f"Erro no loop de captura de tela: {e}", exc_info=True)
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


def test_screen_monitor():
    """Função de teste para o monitor de tela."""
    
    def print_frame_info(frame_data):
        """Callback de teste que imprime informações do frame."""
        print(f"Frame #{frame_data['frame_number']}: "
              f"{frame_data['width']}x{frame_data['height']}, "
              f"tamanho: {len(frame_data['frame'])} bytes")
    
    print("Testando ScreenMonitor...")
    print("Pressione Ctrl+C para parar")
    print("-" * 60)
    
    monitor = ScreenMonitor(frame_callback=print_frame_info)
    
    try:
        monitor.start()
        
        # Deixar rodar
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
    
    test_screen_monitor()

