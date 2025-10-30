"""
Módulo para monitoramento de teclas especiais.
Detecta ações como Print Screen, Win+Shift+S, F11, Ctrl+C e Ctrl+V.
"""
import logging
from datetime import datetime
from typing import Callable, Optional
from pynput import keyboard
from pynput.keyboard import Key, KeyCode

logger = logging.getLogger(__name__)


class KeyboardMonitor:
    """Monitora teclas especiais pressionadas pelo usuário."""
    
    def __init__(self, callback: Callable[[str, dict], None]):
        """
        Inicializa o monitor de teclado.
        
        Args:
            callback: Função a ser chamada quando uma tecla especial é detectada.
                     Recebe (event_name: str, event_data: dict)
        """
        self.callback = callback
        self.listener = None
        self.pressed_keys = set()
        
        # Mapeamento de teclas especiais
        self.special_keys = {
            'print_screen': Key.print_screen,
            'f11': Key.f11,
        }
    
    def start(self):
        """Inicia o monitoramento de teclado."""
        self.listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        self.listener.start()
        logger.info("Monitor de teclado iniciado")
    
    def stop(self):
        """Para o monitoramento de teclado."""
        if self.listener:
            self.listener.stop()
            logger.info("Monitor de teclado parado")
    
    def _on_key_press(self, key):
        """
        Callback chamado quando uma tecla é pressionada.
        
        Args:
            key: Tecla pressionada
        """
        try:
            # Adicionar tecla ao conjunto de teclas pressionadas
            self.pressed_keys.add(key)
            
            # Verificar Print Screen
            if key == Key.print_screen:
                self._report_event('print_screen', {
                    'description': 'Tentativa de captura de tela (Print Screen)',
                    'key': 'Print Screen'
                })
                return
            
            # Verificar F11
            if key == Key.f11:
                self._report_event('f11_pressed', {
                    'description': 'Tecla F11 pressionada (modo tela cheia)',
                    'key': 'F11'
                })
                return
            
            # Verificar se é uma tecla de caractere
            char = None
            try:
                char = key.char
            except AttributeError:
                pass
            
            # Se temos um caractere, verificar combinações
            if char:
                # Verificar Ctrl + C
                if char.lower() == 'c' and self._is_ctrl_pressed():
                    self._report_event('ctrl_c', {
                        'description': 'Copiar (Ctrl + C)',
                        'key': 'Ctrl + C'
                    })
                    return
                
                # Verificar Ctrl + V
                if char.lower() == 'v' and self._is_ctrl_pressed():
                    self._report_event('ctrl_v', {
                        'description': 'Colar (Ctrl + V)',
                        'key': 'Ctrl + V'
                    })
                    return
                
                # Verificar Win + Shift + S
                if char.lower() == 's' and self._is_win_pressed() and self._is_shift_pressed():
                    self._report_event('win_shift_s', {
                        'description': 'Tentativa de captura de tela (Win + Shift + S)',
                        'key': 'Win + Shift + S'
                    })
                    return
        
        except Exception as e:
            logger.error(f"Erro ao processar tecla pressionada: {e}", exc_info=True)
    
    def _on_key_release(self, key):
        """
        Callback chamado quando uma tecla é solta.
        
        Args:
            key: Tecla solta
        """
        try:
            # Remover tecla do conjunto
            if key in self.pressed_keys:
                self.pressed_keys.discard(key)
        except Exception as e:
            logger.error(f"Erro ao processar tecla solta: {e}", exc_info=True)
    
    def _is_ctrl_pressed(self) -> bool:
        """Verifica se a tecla Ctrl está pressionada."""
        return (Key.ctrl_l in self.pressed_keys or 
                Key.ctrl_r in self.pressed_keys or
                Key.ctrl in self.pressed_keys)
    
    def _is_shift_pressed(self) -> bool:
        """Verifica se a tecla Shift está pressionada."""
        return (Key.shift_l in self.pressed_keys or 
                Key.shift_r in self.pressed_keys or
                Key.shift in self.pressed_keys)
    
    def _is_win_pressed(self) -> bool:
        """Verifica se a tecla Windows está pressionada."""
        return (Key.cmd in self.pressed_keys or 
                Key.cmd_l in self.pressed_keys or
                Key.cmd_r in self.pressed_keys)
    
    
    def _report_event(self, event_name: str, event_data: dict):
        """
        Reporta um evento de tecla especial.
        
        Args:
            event_name: Nome do evento
            event_data: Dados do evento
        """
        try:
            # Adicionar timestamp
            event_data['timestamp'] = datetime.now().isoformat()
            
            # Chamar callback
            if self.callback:
                self.callback(event_name, event_data)
                logger.info(f"Evento de teclado detectado: {event_name} - {event_data.get('description', '')}")
        
        except Exception as e:
            logger.error(f"Erro ao reportar evento: {e}", exc_info=True)

