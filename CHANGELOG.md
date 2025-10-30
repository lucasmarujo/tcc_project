# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [1.0.0] - 2024-10-26

### ✨ Adicionado

#### Backend Django
- Sistema completo de autenticação e autorização
- Dashboard administrativa com visualização em tempo real
- Modelos de dados: Student, ExamSession, MonitoringEvent, Alert
- API REST completa com endpoints para:
  - Recebimento de eventos do cliente
  - Sistema de heartbeat
  - Consulta de eventos e alertas
- Sistema automático de geração de alertas baseado em:
  - URLs não permitidas
  - Aplicativos suspeitos
  - Palavras-chave suspeitas
- Interface web moderna com Bootstrap 5
- WebSocket para atualizações em tempo real (Django Channels)
- Admin Django customizado com filtros e buscas avançadas
- Suporte a SQLite (dev) e PostgreSQL (prod)
- Sistema de logs completo

#### Script Cliente
- Monitoramento de navegadores (Chrome, Edge, Firefox)
- Detecção de URLs acessadas
- Monitoramento de processos/aplicativos
- Sistema de comunicação com servidor via API REST
- Sistema de heartbeat para confirmar atividade
- Suporte para compilação em executável (.exe)
- Configuração via variáveis de ambiente ou arquivo
- Sistema de logs local
- Tratamento robusto de erros

#### Documentação
- README completo com visão geral do projeto
- Guia de instalação detalhado (INSTALL.md)
- Guia rápido de início (QUICKSTART.md)
- Documentação separada para backend e cliente
- Guia do aluno em português
- Script de testes da API
- Exemplos de configuração

#### Segurança
- Chaves API únicas por aluno
- Validação de dados em todas as requisições
- Suporte para HTTPS
- Conformidade com LGPD
- Logs de auditoria

### 🎨 Interface

- Dashboard principal com estatísticas
- Página de alertas com filtros
- Página de eventos com histórico completo
- Detalhes individuais por aluno
- Monitoramento ao vivo via WebSocket
- Design responsivo e moderno
- Indicadores visuais de severidade

### 🔧 Configurações

- Whitelist de URLs configurável
- Lista de palavras-chave suspeitas personalizável
- Intervalos de monitoramento ajustáveis
- Suporte para múltiplos ambientes (dev/prod)
- Configuração via variáveis de ambiente

### 📊 Recursos de Monitoramento

- Eventos suportados:
  - Acesso a URL
  - Abertura de aplicativo
  - Mudança de janela
  - Tentativa de screenshot
  - Eventos do sistema
- Níveis de severidade: Baixa, Média, Alta, Crítica
- Estados de alerta: Novo, Em Revisão, Resolvido, Falso Positivo
- Metadados capturados: máquina, IP, timestamp, navegador

### 🚀 Deploy

- Scripts de setup automatizados
- Suporte para Gunicorn + Nginx
- Configuração de SSL/HTTPS
- Arquivos de exemplo para systemd
- Instruções para compilação do executável

## [Não Lançado]

### 🔮 Planejado para Futuras Versões

- Captura periódica de screenshots (opcional)
- Reconhecimento facial via webcam
- Detecção de múltiplos monitores
- Suporte para Linux e macOS no cliente
- App mobile para iOS/Android
- Geração de relatórios em PDF
- Machine Learning para detecção de padrões
- Integração com LMS/AVA existentes
- Notificações push em tempo real
- Histórico de versões de código (se usar IDE)
- Análise de comportamento suspeito
- Dashboard para alunos (visualização própria)
- API pública documentada (OpenAPI/Swagger)
- Suporte para múltiplos idiomas
- Modo offline com sincronização posterior
- Estatísticas e análises avançadas

### 🐛 Correções Planejadas

- Melhorar detecção de URLs em navegadores
- Otimizar uso de memória do script cliente
- Adicionar retry automático em falhas de conexão
- Melhorar performance com grande volume de dados

---

## Tipos de Mudanças

- `Adicionado` para novas funcionalidades
- `Modificado` para mudanças em funcionalidades existentes
- `Descontinuado` para funcionalidades que serão removidas
- `Removido` para funcionalidades removidas
- `Corrigido` para correção de bugs
- `Segurança` para vulnerabilidades corrigidas

---

Para sugestões de novas funcionalidades, entre em contato através do suporte.

