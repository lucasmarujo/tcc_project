"""
Analisador inteligente de tela com múltiplas camadas de detecção.
Combina OCR + palavras-chave + detecção visual para determinar se o aluno
está na tela da prova ou em outro conteúdo.
"""
import logging
import re
from typing import Dict, List, Tuple, Optional
from PIL import Image
import numpy as np

logger = logging.getLogger(__name__)

# Tentar importar OCR
try:
    import easyocr
    OCR_AVAILABLE = 'easyocr'
except ImportError:
    try:
        import pytesseract
        OCR_AVAILABLE = 'pytesseract'
    except ImportError:
        OCR_AVAILABLE = None
        logger.warning("Nenhum OCR disponível. Instale easyocr ou pytesseract")


class ScreenAnalyzer:
    """Analisador multi-camada de conteúdo da tela."""
    
    def __init__(self, use_llm: bool = False, openrouter_key: str = None):
        """
        Inicializa o analisador.
        
        Args:
            use_llm: Se deve usar LLM para análise contextual avançada
            openrouter_key: Chave da API OpenRouter (se usar LLM)
        """
        self.use_llm = use_llm
        self.openrouter_key = openrouter_key
        self.ocr_reader = None
        
        # Inicializar OCR
        if OCR_AVAILABLE == 'easyocr':
            try:
                self.ocr_reader = easyocr.Reader(['pt', 'en'], gpu=False)
                logger.info("OCR EasyOCR inicializado (PT + EN)")
            except Exception as e:
                logger.error(f"Erro ao inicializar EasyOCR: {e}")
        elif OCR_AVAILABLE == 'pytesseract':
            logger.info("Usando Pytesseract para OCR")
        
        # Palavras-chave que indicam PROVA (peso positivo)
        self.prova_keywords = {
            # Palavras fortes (peso 3)
            'forte': [
                'questão', 'questao', 'pergunta', 'resposta',
                'tempo restante', 'enviar prova', 'finalizar prova',
                'prova online', 'avaliação', 'avaliacao',
                'nota:', 'pontos:', 'pontuação', 'pontuacao',
                'marcar resposta', 'alternativa correta',
                'múltipla escolha', 'multipla escolha',
                'dissertativa', 'verdadeiro ou falso',
                'próxima questão', 'proxima questao',
                'questão anterior', 'questao anterior',
                'salvar resposta', 'confirmar envio'
            ],
            # Palavras médias (peso 2)
            'medio': [
                'exame', 'teste', 'quiz',
                'assinale', 'marque', 'indique',
                'correto', 'incorreto', 'certo', 'errado',
                'complete', 'preencha',
                'letra a)', 'letra b)', 'letra c)', 'letra d)', 'letra e)',
                'item i', 'item ii', 'item iii',
                'enunciado', 'considerando', 'baseado',
            ],
            # Palavras fracas (peso 1)
            'fraco': [
                'responder', 'resolver', 'exercício', 'exercicio',
                'atividade', 'tarefa', 'trabalho',
                'desafio', 'problema'
            ]
        }
        
        # Palavras-chave que indicam SLIDES/MATERIAL (peso negativo)
        self.material_keywords = {
            'forte': [
                'slide', 'apresentação', 'apresentacao',
                'conteúdo da aula', 'conteudo da aula',
                'capítulo', 'capitulo', 'seção', 'secao',
                'bibliografia', 'referências', 'referencias',
                'leitura complementar', 'material de apoio',
                'próximo slide', 'proximo slide', 'slide anterior',
                'agenda da aula', 'objetivos da aula'
            ],
            'medio': [
                'introdução', 'introducao', 'conclusão', 'conclusao',
                'resumo', 'síntese', 'sintese',
                'conceito', 'definição', 'definicao',
                'exemplo', 'aplicação', 'aplicacao',
                'teoria', 'fundamentos', 'princípios', 'principios'
            ],
            'fraco': [
                'aula', 'módulo', 'modulo', 'unidade',
                'tópico', 'topico', 'tema',
                'aprender', 'estudar', 'compreender'
            ]
        }
        
        # Inicializar LLM se necessário
        if self.use_llm and self.openrouter_key:
            self._initialize_llm()
    
    def _initialize_llm(self):
        """Inicializa LangChain com OpenRouter."""
        try:
            from langchain_openai import ChatOpenAI
            from langchain.prompts import ChatPromptTemplate
            
            self.llm = ChatOpenAI(
                model="anthropic/claude-3.5-sonnet",
                openai_api_key=self.openrouter_key,
                openai_api_base="https://openrouter.ai/api/v1",
                temperature=0.1
            )
            
            self.llm_prompt = ChatPromptTemplate.from_messages([
                ("system", """Você é um especialista em análise de conteúdo educacional.
Sua tarefa é determinar se um texto extraído de uma tela corresponde a:
- PROVA: Uma avaliação online com questões que o aluno deve responder
- MATERIAL: Slides, apostilas ou conteúdo de estudo
- OUTRO: Qualquer outro tipo de conteúdo

Analise o texto e responda apenas com: PROVA, MATERIAL ou OUTRO"""),
                ("user", "Texto extraído da tela:\n\n{text}\n\nClassificação:")
            ])
            
            logger.info("LLM inicializado (Claude 3.5 Sonnet via OpenRouter)")
        except Exception as e:
            logger.error(f"Erro ao inicializar LLM: {e}")
            self.use_llm = False
    
    def extract_text_from_image(self, image: Image.Image) -> str:
        """
        Extrai texto de uma imagem usando OCR.
        
        Args:
            image: Imagem PIL
            
        Returns:
            Texto extraído
        """
        try:
            if OCR_AVAILABLE == 'easyocr':
                # EasyOCR
                img_array = np.array(image)
                results = self.ocr_reader.readtext(img_array, detail=0)
                text = ' '.join(results)
                return text.lower()
            
            elif OCR_AVAILABLE == 'pytesseract':
                # Pytesseract
                text = pytesseract.image_to_string(image, lang='por+eng')
                return text.lower()
            
            else:
                logger.warning("OCR não disponível")
                return ""
        
        except Exception as e:
            logger.error(f"Erro ao extrair texto: {e}")
            return ""
    
    def calculate_keyword_score(self, text: str) -> Tuple[float, Dict]:
        """
        Calcula score baseado em palavras-chave.
        
        Args:
            text: Texto extraído
            
        Returns:
            (score, detalhes) onde:
            - score > 0: Indica PROVA
            - score < 0: Indica MATERIAL
            - score ~ 0: Ambíguo
        """
        score = 0
        details = {
            'prova_matches': [],
            'material_matches': [],
            'prova_score': 0,
            'material_score': 0
        }
        
        text_lower = text.lower()
        
        # Buscar palavras de PROVA
        for strength, keywords in self.prova_keywords.items():
            weight = {'forte': 3, 'medio': 2, 'fraco': 1}[strength]
            
            for keyword in keywords:
                if keyword in text_lower:
                    score += weight
                    details['prova_matches'].append((keyword, weight))
                    details['prova_score'] += weight
        
        # Buscar palavras de MATERIAL
        for strength, keywords in self.material_keywords.items():
            weight = {'forte': 3, 'medio': 2, 'fraco': 1}[strength]
            
            for keyword in keywords:
                if keyword in text_lower:
                    score -= weight
                    details['material_matches'].append((keyword, weight))
                    details['material_score'] += weight
        
        return score, details
    
    async def analyze_with_llm(self, text: str) -> str:
        """
        Analisa texto usando LLM.
        
        Args:
            text: Texto extraído
            
        Returns:
            'PROVA', 'MATERIAL' ou 'OUTRO'
        """
        if not self.use_llm or not self.llm:
            return 'OUTRO'
        
        try:
            # Limitar tamanho do texto (max 2000 chars)
            text_sample = text[:2000] if len(text) > 2000 else text
            
            chain = self.llm_prompt | self.llm
            response = await chain.ainvoke({"text": text_sample})
            
            classification = response.content.strip().upper()
            
            if classification in ['PROVA', 'MATERIAL', 'OUTRO']:
                return classification
            else:
                logger.warning(f"LLM retornou classificação inválida: {classification}")
                return 'OUTRO'
        
        except Exception as e:
            logger.error(f"Erro ao analisar com LLM: {e}")
            return 'OUTRO'
    
    def analyze_screen(self, image: Image.Image, url: str = None) -> Dict:
        """
        Análise completa da tela.
        
        Args:
            image: Imagem da tela
            url: URL atual (opcional)
            
        Returns:
            Dicionário com resultados da análise:
            {
                'classification': 'prova' | 'material' | 'outro',
                'confidence': float (0-1),
                'is_allowed': bool,
                'text_extracted': str,
                'keyword_score': float,
                'keyword_details': dict,
                'llm_classification': str (se usar LLM),
                'reason': str
            }
        """
        result = {
            'classification': 'outro',
            'confidence': 0.0,
            'is_allowed': False,
            'text_extracted': '',
            'keyword_score': 0.0,
            'keyword_details': {},
            'llm_classification': None,
            'reason': ''
        }
        
        # 1. Extrair texto da imagem
        text = self.extract_text_from_image(image)
        result['text_extracted'] = text[:500]  # Primeiros 500 chars
        
        if not text:
            result['reason'] = "Não foi possível extrair texto da tela"
            result['confidence'] = 0.0
            return result
        
        # 2. Calcular score de palavras-chave
        keyword_score, keyword_details = self.calculate_keyword_score(text)
        result['keyword_score'] = keyword_score
        result['keyword_details'] = keyword_details
        
        # 3. Classificação baseada em keywords
        if keyword_score > 5:
            # Score alto positivo = PROVA
            result['classification'] = 'prova'
            result['is_allowed'] = True
            result['confidence'] = min(0.95, 0.5 + (keyword_score * 0.05))
            result['reason'] = f"Detectadas {len(keyword_details['prova_matches'])} palavras-chave de prova"
        
        elif keyword_score < -5:
            # Score alto negativo = MATERIAL (slides)
            result['classification'] = 'material'
            result['is_allowed'] = False
            result['confidence'] = min(0.95, 0.5 + (abs(keyword_score) * 0.05))
            result['reason'] = f"Detectadas {len(keyword_details['material_matches'])} palavras-chave de material/slides"
        
        else:
            # Score próximo de zero = Ambíguo
            result['classification'] = 'outro'
            result['confidence'] = 0.3
            result['reason'] = "Conteúdo ambíguo - não foi possível classificar com certeza"
        
        return result
    
    async def analyze_screen_async(self, image: Image.Image, url: str = None) -> Dict:
        """Versão assíncrona com suporte a LLM."""
        # Análise inicial
        result = self.analyze_screen(image, url)
        
        # Se resultado ambíguo e LLM disponível, usar LLM
        if self.use_llm and result['confidence'] < 0.7 and result['text_extracted']:
            logger.info("Resultado ambíguo, consultando LLM...")
            llm_class = await self.analyze_with_llm(result['text_extracted'])
            result['llm_classification'] = llm_class
            
            if llm_class == 'PROVA':
                result['classification'] = 'prova'
                result['is_allowed'] = True
                result['confidence'] = 0.85
                result['reason'] = "LLM classificou como PROVA"
            
            elif llm_class == 'MATERIAL':
                result['classification'] = 'material'
                result['is_allowed'] = False
                result['confidence'] = 0.85
                result['reason'] = "LLM classificou como MATERIAL/SLIDES"
        
        return result


def test_analyzer():
    """Testa o analisador com exemplos."""
    analyzer = ScreenAnalyzer(use_llm=False)
    
    # Teste 1: Texto de prova
    prova_text = """
    Questão 1 de 10
    Tempo restante: 45 minutos
    
    Assinale a alternativa correta:
    
    a) Python é uma linguagem de programação
    b) Java é um tipo de café
    c) HTML é uma linguagem de marcação
    d) Todas as anteriores
    
    Marcar resposta e ir para próxima questão
    """
    
    score, details = analyzer.calculate_keyword_score(prova_text)
    print(f"Texto de PROVA: score = {score}")
    print(f"  Palavras de prova encontradas: {len(details['prova_matches'])}")
    print(f"  Palavras de material encontradas: {len(details['material_matches'])}")
    print()
    
    # Teste 2: Texto de slides
    slides_text = """
    Slide 3 de 25
    Capítulo 2: Introdução à Programação
    
    Conteúdo da Aula:
    - Conceitos fundamentais
    - Definição de variáveis
    - Exemplos práticos
    
    Bibliografia:
    - Python para Iniciantes
    
    Próximo slide
    """
    
    score, details = analyzer.calculate_keyword_score(slides_text)
    print(f"Texto de SLIDES: score = {score}")
    print(f"  Palavras de prova encontradas: {len(details['prova_matches'])}")
    print(f"  Palavras de material encontradas: {len(details['material_matches'])}")


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    test_analyzer()

