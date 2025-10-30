"""
Módulo para monitoramento de navegadores.
Detecta URLs abertas no Chrome, Edge e Firefox.
"""
import logging
import platform
from typing import List

logger = logging.getLogger(__name__)

# Tentar importar bibliotecas específicas do Windows
try:
    if platform.system() == 'Windows':
        import win32gui
        import win32process
        import win32api
        import win32con
        WINDOWS_AVAILABLE = True
    else:
        WINDOWS_AVAILABLE = False
except ImportError:
    WINDOWS_AVAILABLE = False
    logger.warning("Bibliotecas Windows não disponíveis. Funcionalidade limitada.")


class BrowserMonitor:
    """Classe para monitorar URLs dos navegadores."""
    
    def __init__(self):
        self.system = platform.system()
        
    def get_browser_urls(self, browser_name: str, pid: int) -> List[str]:
        """
        Obtém URLs abertas em um navegador específico.
        
        Args:
            browser_name: Nome do processo do navegador
            pid: PID do processo
            
        Returns:
            Lista de URLs abertas
        """
        urls = []
        
        if self.system == 'Windows' and WINDOWS_AVAILABLE:
            urls = self._get_urls_windows(browser_name, pid)
        else:
            logger.debug("Monitoramento de URLs não suportado neste sistema")
        
        return urls
    
    def _get_urls_windows(self, browser_name: str, pid: int) -> List[str]:
        """Obtém URLs no Windows através dos títulos das janelas."""
        urls = []
        
        try:
            def window_callback(hwnd, extra):
                """Callback para enumerar janelas."""
                if win32gui.IsWindowVisible(hwnd):
                    # Obter PID da janela
                    _, window_pid = win32process.GetWindowThreadProcessId(hwnd)
                    
                    if window_pid == pid:
                        # Obter título da janela
                        title = win32gui.GetWindowText(hwnd)
                        
                        if title:
                            # Extrair URL do título (navegadores geralmente mostram URL ou título da página)
                            url = self._extract_url_from_title(title, browser_name)
                            if url:
                                urls.append(url)
            
            # Enumerar todas as janelas
            win32gui.EnumWindows(window_callback, None)
            
        except Exception as e:
            logger.debug(f"Erro ao obter URLs do Windows: {e}")
        
        return urls
    
    def _extract_url_from_title(self, title: str, browser_name: str) -> str:
        """
        Extrai URL do título da janela do navegador.
        
        Args:
            title: Título da janela
            browser_name: Nome do navegador
            
        Returns:
            URL extraída ou título da página
        """
        try:
            # Validar título
            if not title or title.strip() == '':
                return ''
            
            # Remover sufixos comuns dos navegadores
            suffixes = [
                ' - Google Chrome',
                ' - Microsoft Edge',
                ' - Mozilla Firefox',
                ' — Mozilla Firefox',
            ]
            
            for suffix in suffixes:
                if title.endswith(suffix):
                    title = title[:-len(suffix)].strip()
            
            # Se contém http/https, é uma URL
            if 'http://' in title or 'https://' in title:
                # Tentar extrair a URL
                parts = title.split()
                for part in parts:
                    if part.startswith('http://') or part.startswith('https://'):
                        return part
            
            # Tentar construir URL básica a partir do título
            # (navegadores modernos nem sempre mostram a URL completa no título)
            # Neste caso, usamos técnicas alternativas
            
            return self._guess_url_from_accessibility_api(title, browser_name)
        
        except Exception as e:
            logger.debug(f"Erro ao extrair URL do título: {e}")
            return ''
    
    def _guess_url_from_accessibility_api(self, title: str, browser_name: str) -> str:
        """
        Tenta obter URL usando APIs de acessibilidade (implementação básica).
        
        Em produção, seria necessário usar bibliotecas mais específicas como:
        - Para Chrome: chrome-remote-interface ou selenium
        - Para Firefox: marionette
        - Para Edge: WebDriver
        
        Por enquanto, retornamos o título como indicador.
        """
        try:
            # Esta é uma implementação simplificada
            # Em um sistema real, você usaria APIs específicas de cada navegador
            # ou extensões para capturar a URL real da barra de endereços
            
            # Validar se o título não está vazio ou é válido
            if not title or title.strip() == '':
                return ''
            
            # Filtrar títulos que são claramente erros ou não relevantes
            error_indicators = ['erro', 'error', 'exception', 'traceback', 'módulo', 'module']
            title_lower = title.lower()
            
            if any(indicator in title_lower for indicator in error_indicators):
                logger.debug(f"Título filtrado como não relevante: {title}")
                return ''
            
            return title.strip()
        
        except Exception as e:
            logger.debug(f"Erro ao processar título: {e}")
            return ''


class BrowserURLExtractor:
    """
    Classe avançada para extração de URLs (requer mais dependências).
    
    Esta implementação seria usada em produção com:
    - Chrome DevTools Protocol para Chrome/Edge
    - Marionette para Firefox
    - Ou usando injeção de DLL/extensões de navegador
    """
    
    @staticmethod
    def get_chrome_urls() -> List[str]:
        """
        Obtém URLs do Chrome usando Chrome DevTools Protocol.
        Requer chrome-remote-interface ou pychrome.
        """
        # Implementação futura com CDP
        return []
    
    @staticmethod
    def get_firefox_urls() -> List[str]:
        """
        Obtém URLs do Firefox usando Marionette.
        """
        # Implementação futura com Marionette
        return []
    
    @staticmethod
    def get_edge_urls() -> List[str]:
        """
        Obtém URLs do Edge (baseado em Chromium).
        """
        # Similar ao Chrome
        return []

