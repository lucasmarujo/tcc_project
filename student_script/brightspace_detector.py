"""
Módulo para detecção de páginas do Brightspace/D2L.
Detecta quando o aluno está em páginas de SLIDES/CONTEÚDO ou PROVA,
e alerta quando há acesso indevido durante provas.

IMPORTANTE: Usa detecção por DOM, não por URL.
"""
import logging
import threading
import time
import json
from typing import Optional, Callable, Dict, Set
from datetime import datetime

logger = logging.getLogger(__name__)

# Tentar importar bibliotecas para Chrome DevTools Protocol
try:
    import pychrome
    PYCHROME_AVAILABLE = True
except ImportError:
    PYCHROME_AVAILABLE = False
    logger.warning("pychrome não disponível. Instale com: pip install pychrome")

# Tentar importar websocket para conexão direta
try:
    import websocket as ws_lib
    WEBSOCKET_AVAILABLE = True
except ImportError:
    WEBSOCKET_AVAILABLE = False


class BrightspaceDetector:
    """
    Classe para detectar páginas do Brightspace e monitorar acesso indevido durante provas.
    """
    
    def __init__(self, alert_callback: Optional[Callable] = None):
        """
        Inicializa o detector do Brightspace.
        
        Args:
            alert_callback: Função callback para alertas de acesso indevido
                           Recebe um dicionário com informações do alerta
        """
        self.alert_callback = alert_callback
        self.running = False
        self.thread = None
        
        # Estado do monitoramento
        self.is_in_quiz = False  # Se o aluno está atualmente em uma prova
        self.quiz_started_time = None  # Quando a prova foi iniciada
        self.current_page_type = None  # 'quiz', 'slides', 'content', 'other'
        self.previous_page_type = None
        
        # Configurações
        self.check_interval = 2.0  # Verificar a cada 2 segundos
        self.chrome_debugging_port = 9222  # Porta padrão do Chrome DevTools
        
        # Estatísticas
        self.alerts_sent = 0
        self.pages_checked = 0
        
        # Cache para evitar múltiplos alertas do mesmo evento
        self.recent_alerts: Set[str] = set()
        self.alert_cache_duration = 10  # segundos
        
        logger.info("BrightspaceDetector inicializado")
    
    def start(self):
        """Inicia o monitoramento em uma thread separada."""
        if self.running:
            logger.warning("BrightspaceDetector já está rodando")
            return
        
        if not PYCHROME_AVAILABLE and not WEBSOCKET_AVAILABLE:
            logger.error("Bibliotecas necessárias não disponíveis. BrightspaceDetector não será iniciado.")
            logger.error("Instale com: pip install pychrome websocket-client")
            return
        
        logger.info("Iniciando BrightspaceDetector...")
        self.running = True
        self.thread = threading.Thread(target=self._detection_loop, daemon=True)
        self.thread.start()
        logger.info("BrightspaceDetector iniciado")
    
    def stop(self):
        """Para o monitoramento."""
        logger.info("Parando BrightspaceDetector...")
        self.running = False
        
        if self.thread:
            self.thread.join(timeout=5)
        
        logger.info(f"BrightspaceDetector parado. Alertas enviados: {self.alerts_sent}")
    
    def _detection_loop(self):
        """Loop principal de detecção."""
        connection_checked = False
        
        while self.running:
            try:
                # Verificar conexão na primeira execução
                if not connection_checked:
                    if self._test_chrome_connection():
                        logger.info("[OK] Chrome DevTools conectado - Detector funcionando!")
                    else:
                        logger.warning("[AVISO] Chrome DevTools NAO conectado!")
                        logger.warning("   Execute: start_chrome_debug.bat")
                        logger.warning("   Ou inicie Chrome com: chrome.exe --remote-debugging-port=9222")
                    connection_checked = True
                
                # Verificar páginas abertas nos navegadores
                self._check_browser_pages()
                
                # Aguardar antes da próxima verificação
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"Erro no loop de detecção: {e}", exc_info=True)
                time.sleep(self.check_interval)
    
    def _test_chrome_connection(self) -> bool:
        """
        Testa se consegue conectar ao Chrome DevTools.
        
        Returns:
            True se conectado, False caso contrário
        """
        try:
            import requests
            response = requests.get(
                f"http://127.0.0.1:{self.chrome_debugging_port}/json",
                timeout=2
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def _check_browser_pages(self):
        """Verifica as páginas abertas no navegador via Chrome DevTools Protocol."""
        try:
            # USAR REQUESTS DIRETO - MAIS SIMPLES E CONFIÁVEL
            import requests
            
            # Obter lista de tabs
            response = requests.get(
                f"http://127.0.0.1:{self.chrome_debugging_port}/json",
                timeout=2
            )
            
            if response.status_code != 200:
                logger.debug(f"[DEBUG] Nao conseguiu obter tabs do Chrome (status {response.status_code})")
                return
            
            tabs = response.json()
            brightspace_tabs_found = 0
            total_tabs = len(tabs)
            
            # Log SEMPRE para debug
            logger.info(f"[DEBUG] Chrome: {total_tabs} tabs abertas no total")
            
            for tab in tabs:
                try:
                    # tabs aqui já vem como dict do requests.json()
                    if tab.get('type') != 'page':
                        continue
                    
                    url = tab.get('url', '')
                    title = tab.get('title', 'N/A')
                    
                    # Log de TODAS as tabs para debug
                    logger.info(f"[DEBUG] Tab: {title[:50]} | URL: {url[:70]}")
                    
                    # Verificar se é uma página do Brightspace/D2L
                    if not self._is_brightspace_url(url):
                        continue
                    
                    brightspace_tabs_found += 1
                    logger.warning(f"[BRIGHTSPACE] >>> TAB DO AVA DETECTADA <<<")
                    logger.warning(f"[BRIGHTSPACE] Titulo: {title}")
                    logger.warning(f"[BRIGHTSPACE] URL: {url}")
                    
                    # Conectar via websocket e verificar DOM
                    ws_url = tab.get('webSocketDebuggerUrl')
                    if ws_url:
                        logger.info("[DEBUG] Conectando ao DOM da pagina via websocket...")
                        page_type = self._detect_page_type_via_websocket(ws_url)
                        
                        if page_type:
                            logger.warning(f"[BRIGHTSPACE] !!! TIPO DE PAGINA DETECTADO: {page_type.upper()} !!!")
                            self._handle_page_detection(page_type, url)
                        else:
                            logger.error("[BRIGHTSPACE] XXX Nao conseguiu detectar tipo da pagina XXX")
                    else:
                        logger.error("[BRIGHTSPACE] XXX Tab nao tem webSocketDebuggerUrl XXX")
                    
                    self.pages_checked += 1
                    
                except Exception as e:
                    logger.error(f"[ERRO] Ao verificar tab: {e}", exc_info=True)
                    continue
            
            # Log a cada verificação para ver se está encontrando
            if brightspace_tabs_found > 0:
                logger.warning(f"[BRIGHTSPACE] === {brightspace_tabs_found} TABS DO AVA ENCONTRADAS ===")
            else:
                logger.info(f"[DEBUG] Nenhuma tab do Brightspace encontrada ({total_tabs} tabs no total)")
            
        except Exception as e:
            logger.error(f"[ERRO] Nao foi possivel conectar ao Chrome DevTools: {e}")
            logger.error(f"[ERRO] Certifique-se de que o Chrome foi iniciado com --remote-debugging-port=9222")
    
    
    def _is_brightspace_url(self, url: str) -> bool:
        """
        Verifica se a URL é do Brightspace/D2L.
        
        Args:
            url: URL a verificar
            
        Returns:
            True se for Brightspace, False caso contrário
        """
        if not url:
            return False
        
        # Indicadores comuns de Brightspace/D2L
        brightspace_indicators = [
            'd2l',
            'brightspace',
            'desire2learn',
            '/d2l/',
            'ava.anchieta.br'  # Domínio específico do AVA
        ]
        
        url_lower = url.lower()
        return any(indicator in url_lower for indicator in brightspace_indicators)
    
    def _detect_page_type_via_websocket(self, ws_url: str) -> Optional[str]:
        """
        Detecta o tipo de página através de websocket direto.
        
        Args:
            ws_url: URL do websocket do debugger
            
        Returns:
            'quiz', 'slides', 'content', ou None
        """
        try:
            logger.info(f"[DEBUG] Conectando ao websocket: {ws_url[:80]}...")
            ws = ws_lib.create_connection(ws_url, timeout=3)
            
            # Habilitar Runtime
            logger.info("[DEBUG] Habilitando Runtime...")
            ws.send(json.dumps({
                "id": 1,
                "method": "Runtime.enable"
            }))
            ws.recv()
            
            # JavaScript para detecção - SIMPLIFICADO E MAIS AGRESSIVO
            js_code = """
            (function() {
                function isSlidesPage() {
                    // Verificar elementos comuns de conteúdo/slides do D2L
                    if (document.querySelector('#d2l-sequence-viewer')) return true;
                    if (document.querySelector('d2l-sequence-viewer-main')) return true;
                    if (document.querySelector('iframe[src*="sequences"]')) return true;
                    if (document.querySelector('.d2l-sequence-content')) return true;
                    if (document.querySelector('.d2l-le-content')) return true;
                    if (document.querySelector('[data-location="content"]')) return true;
                    
                    // Verificar pela URL
                    if (window.location.href.includes('/content/')) return true;
                    if (window.location.href.includes('/le/')) return true;
                    
                    return false;
                }
                
                function isQuizPage() {
                    // Verificar elementos de quiz
                    if (document.querySelector('#quizContainer')) return true;
                    if (document.querySelector('form[action*="quizzing"]')) return true;
                    if (document.querySelector('.d2l-quiz-actions')) return true;
                    if (document.querySelector('d2l-quiz-content')) return true;
                    if (document.querySelector('.d2l_quiz')) return true;
                    
                    // Verificar pela URL
                    if (window.location.href.includes('/quizzing/')) return true;
                    if (window.location.href.includes('/quiz/')) return true;
                    
                    // Verificar pelo título
                    if (document.title.toLowerCase().includes('quiz')) return true;
                    if (document.title.toLowerCase().includes('prova')) return true;
                    
                    return false;
                }
                
                if (isQuizPage()) return 'quiz';
                if (isSlidesPage()) return 'slides';
                return 'other';
            })();
            """
            
            # Executar JavaScript
            logger.info("[DEBUG] Executando JavaScript no DOM...")
            ws.send(json.dumps({
                "id": 2,
                "method": "Runtime.evaluate",
                "params": {
                    "expression": js_code,
                    "returnByValue": True
                }
            }))
            
            # Receber resultado
            response_text = ws.recv()
            logger.info(f"[DEBUG] Resposta recebida: {response_text[:200]}...")
            response = json.loads(response_text)
            
            ws.close()
            
            if 'result' in response and 'result' in response['result']:
                page_type = response['result']['result'].get('value', 'other')
                logger.info(f"[DEBUG] Tipo detectado pelo JavaScript: {page_type}")
                return page_type
            else:
                logger.error(f"[ERRO] Resposta nao tem o formato esperado: {response}")
            
            return None
            
        except Exception as e:
            logger.error(f"[ERRO] Ao detectar tipo de pagina via websocket: {e}", exc_info=True)
            return None
    
    def _handle_page_detection(self, page_type: str, url: str):
        """
        Manipula a detecção de tipo de página.
        
        Args:
            page_type: Tipo de página detectada ('quiz', 'slides', 'other')
            url: URL da página
        """
        # Atualizar estado anterior
        self.previous_page_type = self.current_page_type
        self.current_page_type = page_type
        
        # Detectar mudanças
        if self.previous_page_type != self.current_page_type:
            logger.info(f"Mudança de página detectada: {self.previous_page_type} -> {self.current_page_type}")
            
            # 🆕 REGISTRAR EVENTO DE MUDANÇA DE PÁGINA (sempre)
            self._register_page_view(page_type, url)
        
        # Verificar se entrou em uma prova
        if page_type == 'quiz' and not self.is_in_quiz:
            self._enter_quiz_mode(url)
        
        # Verificar se saiu de uma prova
        if page_type != 'quiz' and self.is_in_quiz:
            self._exit_quiz_mode()
        
        # VERIFICAÇÃO CRÍTICA: Se está em prova e acessou página de slides
        if self.is_in_quiz and page_type == 'slides':
            self._trigger_unauthorized_access_alert('slides', url)
        
        # VERIFICAÇÃO: Se está em prova e acessou outra página que não seja quiz
        if self.is_in_quiz and page_type == 'other':
            # Verificar se ainda é uma página do Brightspace
            if self._is_brightspace_url(url):
                # Acesso a outra página do Brightspace durante prova
                self._trigger_unauthorized_access_alert('other_brightspace', url)
    
    def _register_page_view(self, page_type: str, url: str):
        """
        Registra visualização de página como evento normal.
        
        Args:
            page_type: Tipo de página ('quiz', 'slides', 'other')
            url: URL da página
        """
        # Criar descrição amigável
        descriptions = {
            'quiz': '📝 Aluno acessou página de PROVA no Brightspace',
            'slides': '📖 Aluno está visualizando SLIDES/CONTEÚDO no Brightspace',
            'other': '🌐 Aluno acessou outra página no Brightspace'
        }
        
        description = descriptions.get(page_type, '🌐 Aluno navegando no Brightspace')
        
        # Log DESTACADO para SLIDES (para usuario ver que esta funcionando)
        if page_type == 'slides':
            logger.error("=" * 80)
            logger.error("⚠️  [ALERTA DE ALTA PRIORIDADE] SLIDES/CONTEÚDO DETECTADO!")
            logger.error("=" * 80)
            logger.error(f"   Aluno está visualizando MATERIAL/CONTEÚDO do Brightspace")
            logger.error(f"   URL: {url}")
            logger.error(f"   Status: {'🔴 EM PROVA - POSSÍVEL VIOLAÇÃO!' if self.is_in_quiz else '🟡 Navegação Normal'}")
            logger.error(f"   Severidade: HIGH")
            logger.error("=" * 80)
        else:
            # Log normal para outros tipos
            logger.info(f"{description}")
            logger.info(f"   URL: {url}")
        
        # Enviar via callback como evento informativo
        if self.alert_callback:
            self.alert_callback({
                'alert_type': 'page_view',
                'page_type': page_type,
                'message': description,
                'url': url,
                'timestamp': datetime.now().isoformat(),
                'severity': 'high' if page_type == 'slides' else 'info',  # Slides como HIGH PRIORITY
                'is_in_quiz': self.is_in_quiz
            })
    
    def _enter_quiz_mode(self, url: str = None):
        """
        Entra no modo de prova.
        
        Args:
            url: URL da prova (opcional)
        """
        self.is_in_quiz = True
        self.quiz_started_time = datetime.now()
        logger.warning("=" * 60)
        logger.warning("[PROVA] MODO PROVA ATIVADO")
        logger.warning("O aluno esta em uma pagina de prova/quiz")
        logger.warning("Monitorando acessos indevidos...")
        if url:
            logger.warning(f"URL da prova: {url}")
        logger.warning("=" * 60)
        
        # Notificar via callback
        if self.alert_callback:
            self.alert_callback({
                'alert_type': 'quiz_started',
                'message': 'Aluno iniciou uma prova no Brightspace',
                'url': url if url else '',
                'timestamp': self.quiz_started_time.isoformat(),
                'severity': 'warning'
            })
    
    def _exit_quiz_mode(self):
        """Sai do modo de prova."""
        quiz_duration = None
        if self.quiz_started_time:
            quiz_duration = (datetime.now() - self.quiz_started_time).total_seconds()
        
        self.is_in_quiz = False
        logger.warning("=" * 60)
        logger.warning("[PROVA] MODO PROVA DESATIVADO")
        logger.warning("O aluno saiu da pagina de prova/quiz")
        if quiz_duration:
            logger.warning(f"Duracao da prova: {quiz_duration:.0f} segundos")
        logger.warning("=" * 60)
        
        # Notificar via callback
        if self.alert_callback:
            self.alert_callback({
                'alert_type': 'quiz_ended',
                'message': 'Aluno saiu da prova no Brightspace',
                'timestamp': datetime.now().isoformat(),
                'quiz_duration': quiz_duration,
                'severity': 'info'
            })
        
        self.quiz_started_time = None
    
    def _trigger_unauthorized_access_alert(self, access_type: str, url: str):
        """
        Dispara alerta de acesso não autorizado durante prova.
        
        Args:
            access_type: Tipo de acesso ('slides', 'other_brightspace', etc)
            url: URL acessada
        """
        # Criar chave de cache para evitar alertas duplicados
        cache_key = f"{access_type}:{url}:{int(time.time() / self.alert_cache_duration)}"
        
        if cache_key in self.recent_alerts:
            return  # Já alertado recentemente
        
        self.recent_alerts.add(cache_key)
        
        # Limpar cache antigo
        if len(self.recent_alerts) > 50:
            self.recent_alerts.clear()
        
        # Preparar mensagem de alerta
        if access_type == 'slides':
            message = "ALERTA: Aluno acessou pagina de SLIDES/CONTEUDO durante a PROVA!"
        elif access_type == 'other_brightspace':
            message = "ALERTA: Aluno acessou outra pagina do Brightspace durante a PROVA!"
        else:
            message = f"ALERTA: Acesso indevido durante PROVA: {access_type}"
        
        logger.error("=" * 80)
        logger.error("[ALERTA CRITICO] ACESSO NAO AUTORIZADO DETECTADO!")
        logger.error("=" * 80)
        logger.error(message)
        logger.error(f"URL acessada: {url}")
        logger.error(f"Tempo na prova: {(datetime.now() - self.quiz_started_time).total_seconds():.0f}s")
        logger.error("=" * 80)
        
        self.alerts_sent += 1
        
        # Enviar alerta via callback
        if self.alert_callback:
            alert_data = {
                'alert_type': 'unauthorized_access_during_quiz',
                'access_type': access_type,
                'message': message,
                'url': url,
                'timestamp': datetime.now().isoformat(),
                'quiz_duration': (datetime.now() - self.quiz_started_time).total_seconds(),
                'severity': 'critical'
            }
            
            self.alert_callback(alert_data)
    
    def get_status(self) -> dict:
        """
        Retorna o status atual do detector.
        
        Returns:
            Dicionário com status
        """
        return {
            'running': self.running,
            'is_in_quiz': self.is_in_quiz,
            'current_page_type': self.current_page_type,
            'quiz_started_time': self.quiz_started_time.isoformat() if self.quiz_started_time else None,
            'alerts_sent': self.alerts_sent,
            'pages_checked': self.pages_checked
        }


def test_brightspace_detector():
    """Função de teste para o detector do Brightspace."""
    
    def print_alert(alert_data: dict):
        """Callback de teste que imprime alertas."""
        print("\n" + "=" * 60)
        print(f"ALERTA: {alert_data['alert_type']}")
        print(f"Mensagem: {alert_data['message']}")
        print(f"Timestamp: {alert_data['timestamp']}")
        print("=" * 60)
    
    print("Testando BrightspaceDetector...")
    print("IMPORTANTE: Certifique-se de que o Chrome está rodando com:")
    print("  chrome.exe --remote-debugging-port=9222")
    print()
    print("Pressione Ctrl+C para parar")
    print("-" * 60)
    
    detector = BrightspaceDetector(alert_callback=print_alert)
    
    try:
        detector.start()
        
        # Deixar rodar
        while True:
            time.sleep(5)
            status = detector.get_status()
            print(f"\nStatus: {status}")
            
    except KeyboardInterrupt:
        print("\nParando...")
        detector.stop()


if __name__ == '__main__':
    # Configurar logging para teste
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    test_brightspace_detector()

