# 🎓 Sistema de Monitoramento de Alunos

Sistema completo de monitoramento para garantir a integridade de exames online. Composto por uma **dashboard administrativa em Django** e um **script de monitoramento** que roda no computador do aluno.

## 📋 Visão Geral

Este sistema permite que instituições educacionais monitorem a atividade dos alunos durante exames online, detectando automaticamente:

- ✅ Acesso a sites não autorizados
- ✅ Abertura de aplicativos suspeitos
- ✅ Tentativas de trapaça em tempo real
- ✅ Comportamentos anormais

### URL Permitida

Por padrão, apenas **ava.anchieta.br** é permitida durante os exames. Qualquer outro acesso gera um alerta automático.

## 🏗️ Arquitetura

```
┌─────────────────────┐
│  PC do Aluno        │
│  ┌───────────────┐  │
│  │ Script Python │  │──┐
│  │ (.exe)        │  │  │
│  └───────────────┘  │  │
└─────────────────────┘  │
                         │ API REST
                         │ (HTTPS)
                         ▼
┌─────────────────────────────────────┐
│  Servidor Django                    │
│  ┌─────────────┐  ┌──────────────┐ │
│  │ API REST    │  │ Dashboard    │ │
│  │             │  │ Administrativa│ │
│  └─────────────┘  └──────────────┘ │
│  ┌──────────────────────────────┐  │
│  │ Banco de Dados               │  │
│  └──────────────────────────────┘  │
└─────────────────────────────────────┘
```

## 📦 Componentes

### 1. 🖥️ Admin Django (`admin_django/`)

Dashboard administrativa completa para gestão e visualização dos dados.

**Funcionalidades:**
- Dashboard com estatísticas em tempo real
- Gestão de alunos e sessões de exame
- Visualização de eventos e alertas
- Sistema de notificações automáticas
- API REST para receber dados dos clientes
- Interface web moderna e responsiva

**Tecnologias:**
- Django 4.2
- Django REST Framework
- Django Channels (WebSocket)
- Bootstrap 5
- Chart.js

[📖 Ver documentação completa](admin_django/README.md)

### 2. 💻 Script de Monitoramento (`student_script/`)

Aplicação Python que roda no PC do aluno para capturar atividades.

**Funcionalidades:**
- Monitora Chrome, Edge e Firefox
- Detecta URLs acessadas
- Monitora processos/aplicativos abertos
- Envia dados em tempo real para o servidor
- Sistema de heartbeat
- Pode ser compilado para .exe

**Tecnologias:**
- Python 3.8+
- psutil
- pywin32
- requests

[📖 Ver documentação completa](student_script/README.md)

## 🚀 Início Rápido

### 1. Configure o Servidor Django

```bash
cd admin_django

# Criar ambiente virtual
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Instalar dependências
pip install -r requirements.txt

# Configurar banco de dados
python manage.py migrate

# Criar superusuário
python manage.py createsuperuser

# Executar servidor
python manage.py runserver
```

Acesse: `http://localhost:8000`

### 2. Configure o Script do Aluno

```bash
cd student_script

# Instalar dependências
pip install -r requirements.txt

# Configurar (editar config.py com a API key do aluno)
# Ou definir variáveis de ambiente:
set MONITOR_SERVER_URL=http://localhost:8000
set MONITOR_API_KEY=api-key-do-aluno

# Executar
python monitor.py
```

### 3. Cadastrar Aluno

1. Acesse o admin: `http://localhost:8000/admin`
2. Crie um novo aluno
3. Copie a **API Key** gerada automaticamente
4. Forneça ao aluno para configurar o script

## 📱 Como Usar

### Para Administradores

1. **Cadastrar alunos** no sistema via Admin Django
2. **Criar sessões de exame** com data/hora e alunos participantes
3. **Distribuir o script** (.exe) para os alunos com suas API Keys
4. **Monitorar em tempo real** via dashboard durante o exame
5. **Revisar alertas** após o exame

### Para Alunos

1. **Receber o executável** e a API Key do administrador
2. **Configurar** a API Key no script
3. **Executar o monitor** antes de iniciar o exame
4. **Realizar o exame** normalmente na URL permitida (ava.anchieta.br)
5. O sistema monitora automaticamente

## 🔒 Segurança e Privacidade

### O que é monitorado:

- URLs acessadas nos navegadores
- Nomes de aplicativos abertos
- Títulos de janelas
- Data/hora dos eventos

### O que NÃO é monitorado:

- ❌ Conteúdo das telas (screenshots)
- ❌ Teclas digitadas (keylogger)
- ❌ Senhas ou dados pessoais
- ❌ Arquivos do sistema
- ❌ Câmera ou microfone

### Segurança:

- Chaves API únicas por aluno
- Comunicação pode ser via HTTPS
- Autenticação em todos os endpoints
- Logs de todas as atividades
- Dados criptografados em trânsito

## 🎨 Screenshots da Dashboard

### Dashboard Principal
- Estatísticas em tempo real
- Alertas recentes
- Alunos com mais alertas
- Sessões de exame ativas

### Página de Alertas
- Lista completa de alertas
- Filtros por status e severidade
- Detalhes de cada evento
- Ações para resolver

### Detalhes do Aluno
- Histórico completo de eventos
- Alertas específicos
- Estatísticas individuais

### Monitoramento Ao Vivo
- WebSocket em tempo real
- Notificações instantâneas
- Status de conexão

## 🛠️ Desenvolvimento

### Estrutura do Projeto

```
tcc_monitor_2/
├── admin_django/           # Backend Django
│   ├── config/            # Configurações do projeto
│   ├── students/          # App de gestão de alunos
│   ├── monitoring/        # App de monitoramento
│   ├── dashboard/         # App da dashboard
│   ├── templates/         # Templates HTML
│   ├── static/            # Arquivos estáticos
│   └── requirements.txt
│
├── student_script/        # Script cliente
│   ├── monitor.py         # Script principal
│   ├── browser_monitor.py # Monitoramento de navegadores
│   ├── api_client.py      # Cliente da API
│   ├── config.py          # Configurações
│   ├── build_exe.py       # Compilador para .exe
│   └── requirements.txt
│
└── README.md             # Este arquivo
```

## 📊 Banco de Dados

### Principais Tabelas

- **students**: Dados dos alunos
- **exam_sessions**: Sessões de exame
- **monitoring_events**: Eventos capturados
- **alerts**: Alertas gerados

## 🚀 Deploy em Produção

### Servidor Django

1. Use PostgreSQL como banco de dados
2. Configure variáveis de ambiente apropriadas
3. Use Gunicorn + Nginx
4. Configure SSL/HTTPS
5. Use Redis para Channels (WebSocket)

### Script Cliente

1. Compile para .exe usando PyInstaller
2. Distribua com configurações pré-definidas
3. Considere assinatura digital do executável
4. Forneça instruções claras aos alunos

## 🧪 Testes

### Backend Django

```bash
cd admin_django
python manage.py test
```

### Script Cliente

```bash
cd student_script
python -m pytest
```

## 📝 Configurações Importantes

### URLs Permitidas

Edite em `admin_django/config/settings.py`:

```python
ALLOWED_URLS = ['ava.anchieta.br', 'outro-dominio.com']
```

### Palavras-chave Suspeitas

```python
SUSPICIOUS_KEYWORDS = [
    'chat', 'gpt', 'gemini', 'claude',
    'stackoverflow', 'github', 'google',
    'whatsapp', 'telegram', 'discord'
]
```

### Intervalo de Monitoramento

Edite em `student_script/config.py`:

```python
MONITORING_INTERVAL = 5  # segundos entre verificações
HEARTBEAT_INTERVAL = 60  # segundos entre heartbeats
```

## ⚠️ Requisitos do Sistema

### Servidor

- Linux/Windows Server
- Python 3.8+
- 2GB RAM (mínimo)
- 10GB disco

### Cliente (PC do Aluno)

- Windows 10/11
- Python 3.8+ (se executar o script)
- Ou apenas o .exe compilado
- Conexão com internet

## 🤝 Contribuindo

Este é um projeto acadêmico. Para contribuir:

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto é desenvolvido para fins acadêmicos e é confidencial.

## 👥 Autores

- **Lucas** - Desenvolvimento completo

## 📞 Suporte

Para dúvidas ou problemas:

- 📧 Email: suporte@instituicao.edu.br
- 📱 WhatsApp: (XX) XXXXX-XXXX
- 🌐 Site: https://www.instituicao.edu.br

## 🎯 Roadmap

### Futuras Melhorias

- [ ] Captura de screenshots periódicos (opcional)
- [ ] Reconhecimento facial via webcam
- [ ] Detecção de múltiplos monitores
- [ ] App mobile para iOS/Android
- [ ] Relatórios em PDF
- [ ] Machine Learning para detectar padrões
- [ ] Integração com sistemas AVA existentes
- [ ] Suporte para Linux e macOS

## ⚖️ Considerações Legais

Este sistema deve ser usado de acordo com as leis de privacidade e proteção de dados (LGPD no Brasil). Certifique-se de:

- Informar os alunos sobre o monitoramento
- Obter consentimento explícito
- Usar os dados apenas para fins educacionais
- Implementar políticas de retenção de dados
- Proteger os dados coletados

---

**Desenvolvido com ❤️ para educação de qualidade**

