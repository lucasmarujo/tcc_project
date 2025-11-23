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

