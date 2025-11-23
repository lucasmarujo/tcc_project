"""
Módulo para monitoramento de navegadores.
Detecta URLs abertas no Chrome, Edge e Firefox.
"""
import logging
import platform
import re
from typing import List, Tuple
from pathlib import Path

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
    
    def __init__(self, blocked_urls_file: str = None):
        self.system = platform.system()
        self.blocked_urls = set()
        
        # Carregar URLs bloqueadas do arquivo
        if blocked_urls_file is None:
            blocked_urls_file = Path(__file__).parent / 'url_bloqueadas.txt'
        else:
            blocked_urls_file = Path(blocked_urls_file)
        
        self._load_blocked_urls(blocked_urls_file)
    
    def _load_blocked_urls(self, file_path: Path):
        """Carrega lista de URLs bloqueadas do arquivo."""
        try:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        url = line.strip().lower()
                        if url and not url.startswith('#'):
                            self.blocked_urls.add(url)
                logger.info(f"Carregadas {len(self.blocked_urls)} URLs bloqueadas")
            else:
                logger.warning(f"Arquivo de URLs bloqueadas não encontrado: {file_path}")
        except Exception as e:
            logger.error(f"Erro ao carregar URLs bloqueadas: {e}")
    
    def is_url_blocked(self, url: str) -> Tuple[bool, str]:
        """
        Verifica se uma URL está na lista de bloqueadas.
        
        Args:
            url: URL a verificar
            
        Returns:
            Tupla (está_bloqueada, url_bloqueada_encontrada)
        """
        if not url:
            return False, None
        
        # Normalizar URL
        url_lower = url.lower()
        
        # Remover protocolo para comparação
        url_clean = url_lower.replace('https://', '').replace('http://', '').replace('www.', '')
        
        # Verificar se alguma URL bloqueada está contida na URL atual
        for blocked_url in self.blocked_urls:
            blocked_clean = blocked_url.replace('https://', '').replace('http://', '').replace('www.', '')
            
            # Verificar se o domínio bloqueado está na URL
            if blocked_clean in url_clean or url_clean.startswith(blocked_clean):
                return True, blocked_url
        
        return False, None
        
    def get_browser_urls(self, browser_name: str, pid: int) -> List[dict]:
        """
        Obtém URLs abertas em um navegador específico.
        
        Args:
            browser_name: Nome do processo do navegador
            pid: PID do processo
            
        Returns:
            Lista de dicionários com informações das URLs:
            [
                {
                    'url': str,
                    'title': str,
                    'is_blocked': bool,
                    'blocked_domain': str (se bloqueada)
                }
            ]
        """
        urls = []
        
        if self.system == 'Windows' and WINDOWS_AVAILABLE:
            urls = self._get_urls_windows(browser_name, pid)
        else:
            logger.debug("Monitoramento de URLs não suportado neste sistema")
        
        return urls
    
    def _get_urls_windows(self, browser_name: str, pid: int) -> List[dict]:
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
                            # Extrair URL do título
                            url_info = self._extract_url_from_title(title, browser_name)
                            if url_info:
                                # Verificar se a URL está bloqueada
                                is_blocked, blocked_domain = self.is_url_blocked(url_info['url'])
                                url_info['is_blocked'] = is_blocked
                                if is_blocked:
                                    url_info['blocked_domain'] = blocked_domain
                                
                                urls.append(url_info)
            
            # Enumerar todas as janelas
            win32gui.EnumWindows(window_callback, None)
            
        except Exception as e:
            logger.debug(f"Erro ao obter URLs do Windows: {e}")
        
        return urls
    
    def _extract_url_from_title(self, title: str, browser_name: str) -> dict:
        """
        Extrai URL do título da janela do navegador.
        
        Args:
            title: Título da janela
            browser_name: Nome do navegador
            
        Returns:
            Dicionário com informações: {'url': str, 'title': str, 'has_explicit_url': bool}
            ou None se não conseguir extrair
        """
        try:
            # Validar título
            if not title or title.strip() == '':
                return None
            
            original_title = title
            has_explicit_url = False
            extracted_url = None
            
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
            
            # Se contém http/https explicitamente, é uma URL
            if 'http://' in title or 'https://' in title:
                has_explicit_url = True
                # Tentar extrair a URL usando regex
                url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
                matches = re.findall(url_pattern, title)
                if matches:
                    extracted_url = matches[0]
                else:
                    # Fallback: tentar por split
                    parts = title.split()
                    for part in parts:
                        if part.startswith('http://') or part.startswith('https://'):
                            extracted_url = part
                            break
            
            # Se não encontrou URL explícita, tentar inferir do título
            if not extracted_url:
                extracted_url = self._infer_url_from_title(title, browser_name)
            
            if not extracted_url:
                return None
            
            return {
                'url': extracted_url,
                'title': title,
                'original_title': original_title,
                'has_explicit_url': has_explicit_url
            }
        
        except Exception as e:
            logger.debug(f"Erro ao extrair URL do título: {e}")
            return None
    
    def _infer_url_from_title(self, title: str, browser_name: str) -> str:
        """
        Tenta inferir URL a partir do título da janela.
        
        Args:
            title: Título da janela
            browser_name: Nome do navegador
            
        Returns:
            URL inferida ou título limpo
        """
        try:
            # Validar se o título não está vazio
            if not title or title.strip() == '':
                return None
            
            # Filtrar títulos que são claramente erros ou não relevantes
            error_indicators = ['erro', 'error', 'exception', 'traceback', 'módulo', 'module', 'python']
            title_lower = title.lower()
            
            if any(indicator in title_lower for indicator in error_indicators):
                logger.debug(f"Título filtrado como não relevante: {title}")
                return None
            
            # Tentar extrair domínios comuns do título
            # Ex: "Facebook - Google Chrome" -> "facebook.com"
            common_sites = {
                'google': 'google.com',
                'facebook': 'facebook.com',
                'youtube': 'youtube.com',
                'twitter': 'twitter.com',
                'instagram': 'instagram.com',
                'linkedin': 'linkedin.com',
                'github': 'github.com',
                'stackoverflow': 'stackoverflow.com',
                'reddit': 'reddit.com',
                'wikipedia': 'wikipedia.org',
                'amazon': 'amazon.com',
                'netflix': 'netflix.com',
                'whatsapp': 'web.whatsapp.com',
                'gmail': 'mail.google.com',
                'outlook': 'outlook.com',
                'chatgpt': 'chat.openai.com',
                'claude': 'claude.ai',
                'gemini': 'gemini.google.com',
                'bard': 'bard.google.com',
                'copilot': 'copilot.microsoft.com',
                'bing': 'bing.com',
            }
            
            for site_keyword, site_url in common_sites.items():
                if site_keyword in title_lower:
                    return f"https://{site_url}"
            
            # Se não encontrou nada específico, retornar o título como indicador
            # O título será usado no monitoramento mesmo que não seja uma URL completa
            return title.strip()
        
        except Exception as e:
            logger.debug(f"Erro ao inferir URL do título: {e}")
            return None


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

