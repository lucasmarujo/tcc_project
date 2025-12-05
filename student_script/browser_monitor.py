"""
Módulo para monitoramento de navegadores.
Detecta URLs abertas no Chrome, Edge e Firefox.
"""
import sys
import os
import logging
import platform
import re
import time
from typing import List, Tuple, Dict, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

def get_bundle_dir():
    """Retorna o diretório base (para PyInstaller ou execução normal)."""
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent

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
    
    def __init__(self, blocked_urls_file: str = None, allowed_urls_file: str = None):
        self.system = platform.system()
        self.blocked_urls = set()
        self.allowed_urls = set()
        
        # Carregar URLs bloqueadas
        if blocked_urls_file is None:
            blocked_urls_file = get_bundle_dir() / 'url_bloqueadas.txt'
        else:
            blocked_urls_file = Path(blocked_urls_file)
        
        self._load_blocked_urls(blocked_urls_file)
        
        # Carregar URLs permitidas
        if allowed_urls_file is None:
            allowed_urls_file = get_bundle_dir() / 'urls_permitidas.txt'
        else:
            allowed_urls_file = Path(allowed_urls_file)
            
        self._load_allowed_urls(allowed_urls_file)
        
        # Mapeamento de navegadores
        self.browser_processes = {
            'chrome.exe': 'Google Chrome',
            'msedge.exe': 'Microsoft Edge',
            'firefox.exe': 'Mozilla Firefox'
        }
    
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
    
    def _load_allowed_urls(self, file_path: Path):
        """Carrega lista de URLs permitidas do arquivo."""
        try:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        url = line.strip().lower()
                        if url and not url.startswith('#'):
                            self.allowed_urls.add(url)
                logger.info(f"Carregadas {len(self.allowed_urls)} URLs permitidas")
            else:
                logger.warning(f"Arquivo de URLs permitidas não encontrado: {file_path}")
        except Exception as e:
            logger.error(f"Erro ao carregar URLs permitidas: {e}")
    
    def check_url_status(self, url: str) -> Tuple[str, str]:
        """
        Verifica o status de uma URL.
            
        Returns:
            Tuple (status, message)
            status: 'blocked' (RED), 'allowed' (GREEN), 'warning' (YELLOW)
        """
        if not url:
            return 'unknown', ''
        
        url_lower = url.lower()
        url_clean = url_lower.replace('https://', '').replace('http://', '').replace('www.', '')
        
        # 1. Verificar se está bloqueada (Prioridade Alta)
        for blocked_url in self.blocked_urls:
            blocked_clean = blocked_url.replace('https://', '').replace('http://', '').replace('www.', '')
            if blocked_clean in url_clean or url_clean.startswith(blocked_clean):
                return 'blocked', blocked_url
        
        # 2. Verificar se está permitida
        for allowed_url in self.allowed_urls:
            if allowed_url.endswith('*'):
                # Se termina com *, trata como wildcard
                prefix = allowed_url[:-1].lower()  # Remove o *
                prefix_clean = prefix.replace('https://', '').replace('http://', '').replace('www.', '')
                
                # Verifica se a URL começa com o prefixo
                if url_clean.startswith(prefix_clean):
                    return 'allowed', allowed_url
            else:
                # Comportamento padrão para URLs sem wildcard
                allowed_clean = allowed_url.replace('https://', '').replace('http://', '').replace('www.', '')
                # Verifica correspondência exata ou subcaminho explícito
                if allowed_clean == url_clean or url_clean.startswith(allowed_clean + '/'):
                    return 'allowed', allowed_url
                
        # 3. Se não é nem bloqueada nem permitida = Suspeita
        return 'warning', 'Site possivelmente usado para trapaça'

    def get_active_window_info(self) -> Optional[Dict]:
        """
        Obtém informações da janela ativa APENAS se for um navegador.
        Muito mais rápido que enumerar todas as janelas.
        """
        if self.system != 'Windows' or not WINDOWS_AVAILABLE:
            return None
            
        try:
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return None
                
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            
            try:
                import psutil
                process = psutil.Process(pid)
                process_name = process.name().lower()
                
                if process_name in self.browser_processes:
                    browser_name = self.browser_processes[process_name]
                    title = win32gui.GetWindowText(hwnd)
                    
                    if title:
                        # Extrair URL do título
                        url_info = self._extract_url_from_title(title, browser_name)
                        
                        if url_info:
                            status, match = self.check_url_status(url_info['url'])
                            url_info['status'] = status
                            url_info['match'] = match
                            url_info['browser'] = browser_name
                            url_info['hwnd'] = hwnd  # Adicionar handle da janela
                            return url_info
                            
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
                
        except Exception as e:
            logger.debug(f"Erro ao obter janela ativa: {e}")
            
        return None
    
    def close_browser_window(self, hwnd: int) -> bool:
        """
        Fecha uma janela de navegador específica usando seu handle.
        
        Args:
            hwnd: Handle da janela (HWND)
            
        Returns:
            True se conseguiu fechar, False caso contrário
        """
        if self.system != 'Windows' or not WINDOWS_AVAILABLE:
            logger.warning("Fechar janela não disponível neste sistema")
            return False
        
        try:
            # Verificar se a janela ainda existe
            if not win32gui.IsWindow(hwnd):
                logger.debug(f"Janela {hwnd} não existe mais")
                return False
            
            # Tentar fechar a janela enviando WM_CLOSE
            # WM_CLOSE = 0x0010
            win32gui.PostMessage(hwnd, 0x0010, 0, 0)
            logger.info(f"Comando de fechar janela enviado para HWND {hwnd}")
            
            # Aguardar um pouco para ver se a janela fecha
            time.sleep(0.2)
            
            # Verificar se a janela foi fechada
            if not win32gui.IsWindow(hwnd):
                logger.info("Janela fechada com sucesso")
                return True
            else:
                # Se ainda existe, tentar forçar com WM_QUIT
                # WM_QUIT = 0x0012
                win32gui.PostMessage(hwnd, 0x0012, 0, 0)
                logger.warning("Janela não fechou com WM_CLOSE, tentando WM_QUIT")
                time.sleep(0.2)
                
                return not win32gui.IsWindow(hwnd)
            
        except Exception as e:
            logger.error(f"Erro ao fechar janela: {e}")
            return False
    
    def is_url_blocked(self, url: str) -> Tuple[bool, str]:
        """Mantido para compatibilidade, mas usando nova lógica internamente."""
        status, match = self.check_url_status(url)
        return status == 'blocked', match
        
    def get_browser_urls(self, browser_name: str, pid: int) -> List[dict]:
        """
        Obtém URLs abertas em um navegador específico.
        Mantido para o loop lento (verificação profunda).
        """
        urls = []
        
        if self.system == 'Windows' and WINDOWS_AVAILABLE:
            urls = self._get_urls_windows(browser_name, pid)
        
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
                                # Verificar status usando nova lógica
                                status, match = self.check_url_status(url_info['url'])
                                url_info['status'] = status
                                url_info['match'] = match
                                
                                # Compatibilidade
                                url_info['is_blocked'] = (status == 'blocked')
                                if status == 'blocked':
                                    url_info['blocked_domain'] = match
                                
                                urls.append(url_info)
            
            # Enumerar todas as janelas
            win32gui.EnumWindows(window_callback, None)
            
        except Exception as e:
            logger.debug(f"Erro ao obter URLs do Windows: {e}")
        
        return urls
    
    def _extract_url_from_title(self, title: str, browser_name: str) -> dict:
        """
        Extrai URL do título da janela do navegador.
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
            # Priorizar AVA e outros sites educacionais primeiro
            common_sites = {
                'anchieta': 'ava.anchieta.br',  # Prioridade para AVA
                'inteligência artificial': 'ava.anchieta.br',  # Página específica do AVA
                'página inicial': 'ava.anchieta.br',  # Página inicial do AVA
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
            return title.strip()
        
        except Exception as e:
            logger.debug(f"Erro ao inferir URL do título: {e}")
            return None
