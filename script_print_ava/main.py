"""
Script para tirar prints automaticamente do sistema AVA UniAnchieta
Navega por todas as páginas acessíveis e captura screenshots
"""

import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException, StaleElementReferenceException
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urlparse, urljoin
import logging
import pyautogui

# Configuração de logging (com encoding UTF-8 para Windows)
import sys
sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ava_screenshots.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class AVAScreenshotBot:
    def __init__(self, username, password, max_elements_per_page=20):
        self.username = username
        self.password = password
        self.base_url = "https://ava.anchieta.br/"
        self.visited_urls = set()
        self.screenshot_count = 0
        self.max_elements_per_page = max_elements_per_page  # Limitar elementos por página
        
        # Lista de termos a ignorar (elementos que não devem ser clicados)
        # Adicione aqui novos termos que devem ser ignorados durante a exploração
        self.ignore_terms = [
            'logout', 'sair', 'exit', 'signout',  # Logout
            'biblioteca',  # Abre em nova janela/guia (bug)
            # Adicione mais termos aqui se necessário, ex: 'download', 'pdf', etc.
        ]
        
        # Criar pasta para screenshots (única pasta unificada)
        self.screenshot_dir = f"screenshots_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(self.screenshot_dir, exist_ok=True)
        
        # Configurar Chrome
        self.driver = self._setup_driver()
        
    def _setup_driver(self):
        """Configura o driver do Chrome"""
        chrome_options = Options()
        # chrome_options.add_argument('--headless')  # Descomente para executar sem interface
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_argument('--disable-notifications')
        chrome_options.add_argument('--disable-popup-blocking')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # DESABILITAR POPUP DE SALVAR SENHA
        chrome_options.add_experimental_option('prefs', {
            'credentials_enable_service': False,
            'profile.password_manager_enabled': False
        })
        
        # Usar webdriver-manager para instalar automaticamente o ChromeDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.implicitly_wait(10)
        return driver
    
    def _sanitize_filename(self, text):
        """Remove caracteres inválidos para nome de arquivo"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            text = text.replace(char, '_')
        return text[:100]  # Limitar tamanho do nome
    
    def _safe_click(self, element, use_js_fallback=True):
        """
        Tenta clicar em um elemento com tratamento de erros
        Retorna True se conseguiu clicar, False caso contrário
        """
        try:
            element.click()
            return True
        except StaleElementReferenceException:
            logging.warning("  -> Elemento stale, pulando...")
            return False
        except ElementClickInterceptedException:
            if use_js_fallback:
                try:
                    logging.info("  -> Tentando clicar com JavaScript...")
                    self.driver.execute_script("arguments[0].click();", element)
                    return True
                except StaleElementReferenceException:
                    logging.warning("  -> Elemento stale (JS), pulando...")
                    return False
                except Exception as e:
                    logging.warning(f"  -> Falha ao clicar com JS: {str(e)[:50]}")
                    return False
            return False
        except Exception as e:
            logging.warning(f"  -> Erro ao clicar: {str(e)[:100]}")
            return False
    
    def _take_screenshots(self, page_name):
        """Tira dois tipos de screenshot: tela toda do PC e apenas conteúdo da página"""
        try:
            self.screenshot_count += 1
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_name = self._sanitize_filename(page_name)
            
            # Aguardar um pouco para garantir renderização (REDUZIDO)
            time.sleep(0.3)
            
            # Screenshot da TELA TODA DO PC (incluindo barra do Chrome)
            # Usar pyautogui para capturar a tela real
            try:
                full_path = os.path.join(
                    self.screenshot_dir,
                    f"{self.screenshot_count:03d}_{timestamp}_{safe_name}_FULL.png"
                )
                # Capturar a tela inteira do computador
                screenshot = pyautogui.screenshot()
                screenshot.save(full_path)
                logging.info(f"Screenshot da tela toda salvo: {full_path}")
            except Exception as e:
                logging.error(f"Erro ao tirar screenshot da tela toda: {e}")
            
            # Aguardar um pouco entre screenshots (REDUZIDO)
            time.sleep(0.3)
            
            # Screenshot apenas do CONTEÚDO da página (sem barra do navegador)
            try:
                # Usar o screenshot do Selenium que captura apenas a página web
                content_path = os.path.join(
                    self.screenshot_dir,
                    f"{self.screenshot_count:03d}_{timestamp}_{safe_name}_CONTENT.png"
                )
                self.driver.save_screenshot(content_path)
                logging.info(f"Screenshot do conteúdo salvo: {content_path}")
            except Exception as e:
                logging.warning(f"Não foi possível tirar screenshot do conteúdo: {e}")
            
            return True
        except Exception as e:
            logging.error(f"Erro ao tirar screenshot: {e}")
            return False
    
    def login(self):
        """Faz login no sistema AVA"""
        try:
            logging.info("Acessando página de login...")
            self.driver.get(self.base_url)
            
            # Aguardar página carregar
            wait = WebDriverWait(self.driver, 20)
            
            # Tirar print da tela de login
            self._take_screenshots("01_login_page")
            
            # Encontrar campos de login
            # Tentar diferentes seletores possíveis
            username_selectors = [
                "input[name='userName']",
                "input[type='text']",
                "#userName",
                "input[placeholder*='usuário']",
                "input[placeholder*='Nome']"
            ]
            
            password_selectors = [
                "input[name='password']",
                "input[type='password']",
                "#password",
                "input[placeholder*='senha']",
                "input[placeholder*='Senha']"
            ]
            
            # Tentar encontrar campo de usuário
            username_field = None
            for selector in username_selectors:
                try:
                    username_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    logging.info(f"Campo de usuário encontrado com seletor: {selector}")
                    break
                except TimeoutException:
                    continue
            
            if not username_field:
                logging.error("Campo de usuário não encontrado!")
                return False
            
            # Tentar encontrar campo de senha
            password_field = None
            for selector in password_selectors:
                try:
                    password_field = self.driver.find_element(By.CSS_SELECTOR, selector)
                    logging.info(f"Campo de senha encontrado com seletor: {selector}")
                    break
                except NoSuchElementException:
                    continue
            
            if not password_field:
                logging.error("Campo de senha não encontrado!")
                return False
            
            # Preencher credenciais
            logging.info("Preenchendo credenciais...")
            username_field.clear()
            username_field.send_keys(self.username)
            time.sleep(0.3)
            
            password_field.clear()
            password_field.send_keys(self.password)
            time.sleep(0.3)
            
            # Tirar print com credenciais preenchidas
            self._take_screenshots("02_login_filled")
            
            # Encontrar e clicar no botão de login
            login_button_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button[class*='login']",
                ".d2l-button",
                "button"
            ]
            
            login_button = None
            for selector in login_button_selectors:
                try:
                    buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for btn in buttons:
                        text = btn.text.lower()
                        if 'login' in text or 'entrar' in text or 'fazer login' in text or not text:
                            login_button = btn
                            logging.info(f"Botão de login encontrado: {selector}")
                            break
                    if login_button:
                        break
                except NoSuchElementException:
                    continue
            
            if not login_button:
                logging.error("Botão de login não encontrado!")
                return False
            
            # Clicar no botão de login
            logging.info("Clicando no botão de login...")
            login_button.click()
            
            # Aguardar login ser processado (REDUZIDO)
            time.sleep(3)
            
            # Verificar se o login foi bem-sucedido
            current_url = self.driver.current_url
            logging.info(f"URL após login: {current_url}")
            
            # Tirar print da página após login
            self._take_screenshots("03_homepage_after_login")
            
            # NÃO adicionar ao visited_urls aqui - deixar o explore_page fazer isso
            # para que ele possa explorar a página inicial corretamente
            
            return True
            
        except Exception as e:
            logging.error(f"Erro durante login: {e}")
            self._take_screenshots("ERROR_login")
            return False
    
    def _get_discipline_cards(self):
        """Encontra especificamente os cards de disciplinas no AVA"""
        discipline_cards = []
        
        try:
            # Seletores específicos para cards de disciplinas no D2L Brightspace AVA
            discipline_selectors = [
                "a[href*='/d2l/le/content/']",  # Links para conteúdo de disciplinas
                ".d2l-card a[href*='/d2l/']",
                "div[class*='course-card'] a",
                "div[class*='widget'] a[href*='/d2l/']",
                "a[title*='999_']",  # IDs de disciplinas começam com 999_
            ]
            
            seen_urls = set()
            
            for selector in discipline_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        try:
                            if not elem.is_displayed():
                                continue
                            
                            href = elem.get_attribute("href")
                            text = elem.text.strip()
                            
                            if href and href not in seen_urls and href not in self.visited_urls:
                                # Filtrar apenas URLs de disciplinas válidas
                                if '/d2l/' in href and not any(term in href.lower() for term in self.ignore_terms):
                                    seen_urls.add(href)
                                    discipline_cards.append({
                                        'element': elem,
                                        'type': 'discipline',
                                        'url': href,
                                        'text': text or 'Disciplina'
                                    })
                        except Exception:
                            continue
                except Exception:
                    continue
            
            logging.info(f"Encontrados {len(discipline_cards)} cards de disciplinas")
            return discipline_cards
            
        except Exception as e:
            logging.error(f"Erro ao buscar cards de disciplinas: {e}")
            return []
    
    def _get_clickable_elements(self):
        """Encontra todos os elementos clicáveis na página"""
        clickable_elements = []
        seen_elements = set()
        
        try:
            # Encontrar links
            links = self.driver.find_elements(By.TAG_NAME, "a")
            for link in links:
                try:
                    # Verificar se o elemento está visível e tem tamanho
                    if not link.is_displayed() or link.size['width'] == 0:
                        continue
                    
                    href = link.get_attribute("href")
                    text = link.text.strip()
                    target = link.get_attribute("target")
                    
                    # IGNORAR links que abrem em nova guia/janela
                    if target and target.lower() in ['_blank', '_new']:
                        logging.info(f"  -> Ignorando link (abre em nova guia): {text}")
                        continue
                    
                    # IGNORAR elementos com termos da lista de ignore
                    if text and any(term in text.lower() for term in self.ignore_terms):
                        logging.info(f"  -> Ignorando link: {text}")
                        continue
                    
                    if href and href not in self.visited_urls:
                        # Filtrar URLs indesejadas
                        ignore_url_patterns = ['javascript:', '#'] + self.ignore_terms
                        if not any(x in href.lower() for x in ignore_url_patterns):
                            # Evitar duplicatas
                            if href not in seen_elements:
                                seen_elements.add(href)
                                clickable_elements.append({
                                    'element': link,
                                    'type': 'link',
                                    'url': href,
                                    'text': text or href[-50:]
                                })
                except Exception:
                    continue
            
            # Encontrar botões
            buttons = self.driver.find_elements(By.TAG_NAME, "button")
            for button in buttons:
                try:
                    if not button.is_displayed() or button.size['width'] == 0:
                        continue
                    
                    text = button.text.strip()
                    
                    # Filtrar botões indesejados
                    if text and any(term in text.lower() for term in self.ignore_terms):
                        continue
                    
                    # Gerar ID único para o botão
                    button_id = f"btn_{text[:30]}_{button.location['x']}_{button.location['y']}"
                    if button_id not in seen_elements:
                        seen_elements.add(button_id)
                        clickable_elements.append({
                            'element': button,
                            'type': 'button',
                            'url': self.driver.current_url,
                            'text': text or 'Button'
                        })
                except Exception:
                    continue
            
            # Encontrar cards e divs clicáveis (elementos interativos comuns)
            try:
                clickable_selectors = [
                    "[onclick]",
                    ".card[href]",
                    "div[role='button']",
                    "div[role='link']",
                    ".clickable",
                    "[class*='card']",
                    "[class*='item']"
                ]
                
                for selector in clickable_selectors:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for elem in elements:
                        try:
                            if not elem.is_displayed() or elem.size['width'] == 0:
                                continue
                            
                            text = elem.text.strip()[:50]
                            
                            # Filtrar elementos indesejados
                            if text and any(term in text.lower() for term in self.ignore_terms):
                                continue
                            
                            # Verificar se abre em nova guia
                            target = elem.get_attribute("target")
                            if target and target.lower() in ['_blank', '_new']:
                                continue
                            
                            # Gerar ID único
                            elem_id = f"elem_{text[:20]}_{elem.location['x']}_{elem.location['y']}"
                            
                            if elem_id not in seen_elements and text:
                                seen_elements.add(elem_id)
                                clickable_elements.append({
                                    'element': elem,
                                    'type': 'interactive',
                                    'url': self.driver.current_url,
                                    'text': text or 'Interactive element'
                                })
                        except Exception:
                            continue
            except Exception:
                pass
            
            logging.info(f"Encontrados {len(clickable_elements)} elementos clicáveis únicos")
            return clickable_elements
            
        except Exception as e:
            logging.error(f"Erro ao buscar elementos clicáveis: {e}")
            return []
    
    def explore_disciplines(self):
        """Explora especificamente as disciplinas do AVA"""
        logging.info("=" * 50)
        logging.info("EXPLORANDO DISCIPLINAS")
        logging.info("=" * 50)
        
        home_url = self.driver.current_url
        
        # Buscar cards de disciplinas
        discipline_cards = self._get_discipline_cards()
        
        if not discipline_cards:
            logging.warning("Nenhum card de disciplina encontrado!")
            return
        
        for idx, card_info in enumerate(discipline_cards):
            try:
                logging.info(f"\n[DISCIPLINA {idx+1}/{len(discipline_cards)}] {card_info['text']}")
                
                # Ir para a disciplina
                discipline_url = card_info['url']
                logging.info(f"  -> Acessando: {discipline_url}")
                self.driver.get(discipline_url)
                time.sleep(2)
                
                # Tirar prints da disciplina
                self._take_screenshots(f"disciplina_{idx+1:02d}_{card_info['text']}")
                self.visited_urls.add(discipline_url)
                
                # Scroll e tirar outro print
                self._scroll_page()
                self._take_screenshots(f"disciplina_{idx+1:02d}_{card_info['text']}_scrolled")
                
                # Explorar módulos dentro da disciplina
                self.explore_page(depth=1, max_depth=3, is_discipline_page=True)
                
                # Voltar para a home
                logging.info(f"  -> Voltando para home...")
                self.driver.get(home_url)
                time.sleep(2)
                
            except Exception as e:
                logging.error(f"Erro ao explorar disciplina: {e}")
                # Tentar voltar para home mesmo com erro
                try:
                    self.driver.get(home_url)
                    time.sleep(2)
                except Exception:
                    pass
                continue
        
        logging.info("=" * 50)
        logging.info("EXPLORAÇÃO DE DISCIPLINAS CONCLUÍDA")
        logging.info("=" * 50)
    
    def explore_page(self, depth=0, max_depth=3, is_discipline_page=False):
        """Explora recursivamente a página atual"""
        if depth > max_depth:
            logging.info(f"Profundidade maxima atingida ({max_depth})")
            return
        
        try:
            current_url = self.driver.current_url
            
            # Verificar se já visitamos esta URL (mas não retornar se for depth 0, para explorar a home)
            if current_url in self.visited_urls and depth > 0:
                logging.info(f"Pagina ja visitada: {current_url}")
                return
            
            self.visited_urls.add(current_url)
            
            # Aguardar página carregar (REDUZIDO para ser mais rápido)
            time.sleep(1.5)
            
            # Tirar screenshots da página atual
            page_title = self.driver.title or f"page_{len(self.visited_urls)}"
            logging.info(f"Explorando: {page_title} (Depth: {depth})")
            self._take_screenshots(f"{len(self.visited_urls):03d}_{page_title}")
            
            # Scroll para carregar conteúdo dinâmico
            self._scroll_page()
            
            # Tirar screenshot após scroll
            self._take_screenshots(f"{len(self.visited_urls):03d}_{page_title}_scrolled")
            
            # Obter elementos clicáveis
            clickable_elements = self._get_clickable_elements()
            
            # Limitar número de elementos por página
            if len(clickable_elements) > self.max_elements_per_page:
                logging.info(f"Limitando de {len(clickable_elements)} para {self.max_elements_per_page} elementos")
                clickable_elements = clickable_elements[:self.max_elements_per_page]
            
            logging.info(f"Explorando {len(clickable_elements)} elementos nesta página")
            
            # Visitar cada elemento clicável
            for idx, element_info in enumerate(clickable_elements):
                try:
                    # Garantir que estamos na janela principal
                    if len(self.driver.window_handles) > 1:
                        main_window = self.driver.window_handles[0]
                        for handle in self.driver.window_handles[1:]:
                            try:
                                self.driver.switch_to.window(handle)
                                self.driver.close()
                            except Exception:
                                pass
                        self.driver.switch_to.window(main_window)
                    
                    element = element_info['element']
                    element_type = element_info['type']
                    element_text = element_info['text']
                    target_url = element_info.get('url', '')
                    
                    logging.info(f"[{idx+1}/{len(clickable_elements)}] Tentando clicar em {element_type}: {element_text}")
                    
                    # Pular se a URL já foi visitada (para links)
                    if element_type == 'link' and target_url in self.visited_urls:
                        logging.info(f"  -> Link ja visitado, pulando...")
                        continue
                    
                    # Scroll até o elemento (MAIS RÁPIDO)
                    try:
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                        time.sleep(0.3)
                    except StaleElementReferenceException:
                        logging.warning(f"  -> Elemento stale ao fazer scroll, pulando...")
                        continue
                    except Exception:
                        pass
                    
                    # Tentar clicar usando função segura
                    if not self._safe_click(element):
                        continue
                    
                    # Aguardar após o clique (REDUZIDO)
                    time.sleep(1.5)
                    
                    # Verificar se abriu nova janela/guia acidentalmente
                    if len(self.driver.window_handles) > 1:
                        logging.warning(f"  -> Nova janela detectada! Fechando...")
                        # Fechar todas as janelas extras
                        main_window = self.driver.window_handles[0]
                        for handle in self.driver.window_handles[1:]:
                            self.driver.switch_to.window(handle)
                            self.driver.close()
                        # Voltar para a janela principal
                        self.driver.switch_to.window(main_window)
                        time.sleep(1)
                        continue  # Pular este elemento e ir para o próximo
                    
                    # Verificar se mudamos de página
                    new_url = self.driver.current_url
                    if new_url != current_url:
                        logging.info(f"  -> Nova pagina detectada: {new_url}")
                        
                        if new_url not in self.visited_urls:
                            # Explorar nova página recursivamente
                            self.explore_page(depth + 1, max_depth)
                        
                        # Voltar para a página anterior
                        try:
                            logging.info(f"  -> Voltando para: {current_url}")
                            self.driver.back()
                            time.sleep(1.5)  # Aguardar página recarregar (REDUZIDO)
                            
                            # Re-obter os elementos após voltar (a página pode ter mudado)
                            # Precisamos re-obter TODOS os elementos, não só se ainda há elementos
                            try:
                                clickable_elements = self._get_clickable_elements()
                                # Limitar novamente se necessário
                                if len(clickable_elements) > self.max_elements_per_page:
                                    clickable_elements = clickable_elements[:self.max_elements_per_page]
                                logging.info(f"  -> Re-obtidos {len(clickable_elements)} elementos apos voltar")
                            except Exception as e:
                                logging.warning(f"  -> Erro ao re-obter elementos: {e}")
                                break
                        except Exception as e:
                            logging.error(f"  -> Erro ao voltar: {e}")
                            break
                    else:
                        logging.info(f"  -> Permaneceu na mesma pagina")
                    
                except Exception as e:
                    logging.warning(f"Erro ao processar elemento: {e}")
                    continue
            
            logging.info(f"Exploração da página concluída (Depth: {depth})")
            
        except Exception as e:
            logging.error(f"Erro ao explorar página: {e}")
    
    def _scroll_page(self):
        """Faz scroll pela página para carregar conteúdo dinâmico"""
        try:
            # Obter altura total da página
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            # Scroll gradual (MAIS RÁPIDO)
            scroll_pause = 0.5
            scroll_step = 800
            
            for i in range(0, last_height, scroll_step):
                self.driver.execute_script(f"window.scrollTo(0, {i});")
                time.sleep(0.1)
            
            # Scroll até o final
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(scroll_pause)
            
            # Voltar ao topo
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(scroll_pause)
            
        except Exception as e:
            logging.warning(f"Erro ao fazer scroll: {e}")
    
    def run(self):
        """Executa o processo completo"""
        try:
            logging.info("=" * 50)
            logging.info("Iniciando AVA Screenshot Bot")
            logging.info("=" * 50)
            
            # Fazer login
            if not self.login():
                logging.error("Falha no login. Encerrando.")
                return False
            
            logging.info("Login realizado com sucesso!")
            
            # Tirar print da home completa (com scroll)
            logging.info("Explorando página home...")
            self._scroll_page()
            self._take_screenshots("home_completa_scrolled")
            
            # EXPLORAR DISCIPLINAS ESPECIFICAMENTE
            logging.info("\n" + "=" * 50)
            logging.info("Iniciando exploração de DISCIPLINAS...")
            logging.info("=" * 50)
            self.explore_disciplines()
            
            # Explorar outros elementos da home (se houver)
            logging.info("\nExplorando outros elementos da home...")
            self.driver.get(self.driver.current_url)  # Recarregar home
            time.sleep(1)
            self.explore_page(depth=0, max_depth=2)  # Exploração geral mais superficial
            
            logging.info("=" * 50)
            logging.info(f"Exploração concluída!")
            logging.info(f"Total de páginas visitadas: {len(self.visited_urls)}")
            logging.info(f"Total de screenshots: {self.screenshot_count * 2}")
            logging.info(f"Screenshots salvos em: {self.screenshot_dir}")
            logging.info("=" * 50)
            
            return True
            
        except Exception as e:
            logging.error(f"Erro durante execução: {e}")
            return False
        
        finally:
            # Manter navegador aberto por 2 segundos antes de fechar
            logging.info("Aguardando 2 segundos antes de fechar...")
            time.sleep(2)
            self.driver.quit()
            logging.info("Navegador fechado.")


def main():
    """Função principal"""
    # Credenciais
    USERNAME = "2108723"
    PASSWORD = "42071471873!"
    
    # Configurações
    MAX_ELEMENTS_PER_PAGE = 50  # Máximo de elementos a clicar por página (aumentado)
    
    # Criar e executar bot
    bot = AVAScreenshotBot(USERNAME, PASSWORD, max_elements_per_page=MAX_ELEMENTS_PER_PAGE)
    
    try:
        bot.run()
    except KeyboardInterrupt:
        logging.info("\nInterrompido pelo usuário.")
        bot.driver.quit()
    except Exception as e:
        logging.error(f"Erro fatal: {e}")
        bot.driver.quit()


if __name__ == "__main__":
    main()

