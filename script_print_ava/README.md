# Script de Screenshots Automático - AVA UniAnchieta

Este script automatiza o processo de navegação e captura de screenshots do sistema AVA UniAnchieta.

## Funcionalidades

- ✅ Login automático no sistema
- ✅ Navegação automática por todas as páginas acessíveis
- ✅ Captura de dois tipos de screenshots:
  - **FULL**: Print da **tela toda do PC** (incluindo barra de navegação do Chrome e sistema operacional)
  - **CONTENT**: Print apenas da **página web** (viewport do navegador, sem barra)
- ✅ Exploração recursiva de links e cards clicáveis
- ✅ Sistema de logging completo
- ✅ Organização automática dos prints em uma pasta unificada

## Instalação

### 1. Instalar Python
Certifique-se de ter Python 3.8+ instalado.

### 2. Instalar dependências
```bash
pip install -r requirements.txt
```

### 3. Instalar ChromeDriver
O script usa o Chrome. Você precisa ter o Google Chrome instalado.

**Opção 1 - Automática (Recomendado):**
Adicione ao código:
```python
from webdriver_manager.chrome import ChromeDriverManager
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
```

**Opção 2 - Manual:**
1. Baixe o ChromeDriver compatível com sua versão do Chrome: https://chromedriver.chromium.org/
2. Adicione o ChromeDriver ao PATH do sistema

## Uso

### Executar o script
```bash
python main.py
```

### Credenciais
As credenciais estão configuradas diretamente no código:
- **Usuário**: 2108723
- **Senha**: 42071471873!

Para alterar, edite as variáveis `USERNAME` e `PASSWORD` na função `main()`.

## Estrutura de Saídas

```
script_print_ava/
├── screenshots_YYYYMMDD_HHMMSS/
│   ├── 001_timestamp_pagename_FULL.png    ← Tela toda do PC
│   ├── 001_timestamp_pagename_CONTENT.png ← Só a página web
│   ├── 002_timestamp_pagename_FULL.png
│   ├── 002_timestamp_pagename_CONTENT.png
│   └── ...
├── ava_screenshots.log
└── main.py
```

## Configurações

### Profundidade de Exploração
Altere o parâmetro `max_depth` na função `run()`:
```python
self.explore_page(depth=0, max_depth=5)  # Padrão: 5 níveis
```

### Modo Headless (Sem Interface)
Para executar sem abrir o navegador, descomente a linha:
```python
chrome_options.add_argument('--headless')
```

### Tempo de Espera
Ajuste os valores de `time.sleep()` conforme necessário:
- Após login: `time.sleep(5)` (linha ~194)
- Entre páginas: `time.sleep(3)` (linha ~316)
- Após cliques: `time.sleep(3)` (linha ~372)

## Logs

O script gera um arquivo `ava_screenshots.log` com informações detalhadas:
- Páginas visitadas
- Elementos clicados
- Erros encontrados
- Screenshots capturados

## Segurança

⚠️ **ATENÇÃO**: Este script contém credenciais de acesso. 
- Não compartilhe o código com as credenciais
- Não faça commit do arquivo com senhas para repositórios públicos
- Considere usar variáveis de ambiente para credenciais

## Solução de Problemas

### Erro: ChromeDriver incompatível
- Atualize o Chrome para a versão mais recente
- Reinstale o ChromeDriver compatível

### Erro: Elemento não encontrado
- Aumente os tempos de espera (`time.sleep()`)
- Verifique se o site mudou sua estrutura

### Screenshots vazios
- Desative o modo headless
- Aumente o tempo de espera após carregamento

### Muitos screenshots duplicados
- Reduza o `max_depth`
- Ajuste a lógica de detecção de URLs visitadas

## Limitações

- O script não preenche formulários complexos automaticamente
- Pode não detectar todos os tipos de elementos interativos
- Sites com muito JavaScript podem precisar de tempos de espera maiores
- Modais e popups podem interferir na navegação

## Melhorias Futuras

- [ ] Suporte a múltiplas credenciais
- [ ] Exportação de relatório HTML com thumbnails
- [ ] Detecção de mudanças entre execuções
- [ ] Suporte a outros navegadores (Firefox, Edge)
- [ ] Interface gráfica para configuração

