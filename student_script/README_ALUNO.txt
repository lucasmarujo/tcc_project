================================================================================
           SISTEMA DE MONITORAMENTO DE ALUNOS - GUIA DO ALUNO
================================================================================

Olá! Este programa é necessário para realizar seu exame online.

================================================================================
O QUE ESTE PROGRAMA FAZ?
================================================================================

Este programa monitora sua atividade no computador durante o exame para
garantir a integridade acadêmica. Ele detecta:

✓ Sites que você acessa nos navegadores
✓ Programas que você abre
✓ Janelas que você utiliza

IMPORTANTE: O programa NÃO captura:
✗ Conteúdo da sua tela (sem screenshots)
✗ O que você digita (sem keylogger)
✗ Suas senhas
✗ Seus arquivos pessoais

================================================================================
COMO USAR
================================================================================

1. ANTES DO EXAME:
   - Feche todos os programas desnecessários
   - Feche todas as abas do navegador
   - Desative notificações

2. INICIAR O MONITOR:
   - Execute o arquivo: MonitorAluno.exe
   - Você verá uma mensagem confirmando que está ativo
   - NÃO feche esta janela durante o exame

3. DURANTE O EXAME:
   - Acesse APENAS: ava.anchieta.br
   - Não abra outras abas ou sites
   - Não abra programas como WhatsApp, calculadoras, etc.
   - Mantenha o monitor rodando

4. APÓS O EXAME:
   - Pressione Ctrl+C na janela do monitor para parar
   - Ou simplesmente feche a janela

================================================================================
CONFIGURAÇÃO DA API KEY
================================================================================

Você recebeu uma CHAVE API única. Para configurar:

MÉTODO 1 - Variáveis de Ambiente (recomendado):

   Windows:
   1. Pressione Windows + R
   2. Digite: sysdm.cpl
   3. Vá em "Avançado" > "Variáveis de Ambiente"
   4. Clique em "Nova" (variáveis do usuário)
   5. Nome: MONITOR_API_KEY
   6. Valor: [sua-chave-api-aqui]
   7. Clique OK
   8. Reinicie o computador

MÉTODO 2 - Linha de Comando:

   Antes de executar o programa:
   
   set MONITOR_API_KEY=sua-chave-api-aqui
   set MONITOR_SERVER_URL=http://servidor.com
   MonitorAluno.exe

MÉTODO 3 - Editar config.py (se tiver o código fonte):

   Abra config.py e edite:
   API_KEY = 'sua-chave-api-aqui'
   SERVER_URL = 'http://servidor.com'

================================================================================
SITES E APPS PERMITIDOS
================================================================================

PERMITIDO:
✓ ava.anchieta.br (plataforma do exame)

NÃO PERMITIDO (irá gerar alerta):
✗ Google, Bing, outros buscadores
✗ WhatsApp, Telegram, Discord
✗ ChatGPT, Gemini, outros assistentes de IA
✗ Stack Overflow, GitHub
✗ Tradutores online
✗ Calculadoras online
✗ Qualquer outro site

================================================================================
O QUE ACONTECE SE EU ACESSAR SITES NÃO PERMITIDOS?
================================================================================

Se você acessar sites ou abrir programas não permitidos:

1. O sistema registrará o evento
2. Um alerta será gerado para o professor
3. O professor poderá revisar sua prova manualmente
4. Dependendo da gravidade, medidas disciplinares podem ser aplicadas

================================================================================
PROBLEMAS COMUNS
================================================================================

PROBLEMA: "Invalid API key"
SOLUÇÃO: Verifique se configurou a API Key corretamente

PROBLEMA: "Unable to connect to server"
SOLUÇÃO: 
   - Verifique sua conexão com internet
   - Verifique o endereço do servidor
   - Desative temporariamente firewall/antivírus

PROBLEMA: Antivírus bloqueia o programa
SOLUÇÃO: 
   - Adicione exceção no antivírus
   - Este é um programa legítimo da instituição

PROBLEMA: Monitor fecha sozinho
SOLUÇÃO:
   - Execute como Administrador (clique com botão direito)
   - Verifique os logs em monitor.log

================================================================================
REQUISITOS DO SISTEMA
================================================================================

✓ Windows 10 ou 11
✓ 2GB de RAM (mínimo)
✓ Conexão com internet
✓ Navegador: Chrome, Edge ou Firefox

================================================================================
PRIVACIDADE E DADOS
================================================================================

Seus dados são tratados com confidencialidade e usados apenas para:

✓ Verificar integridade do exame
✓ Gerar relatórios para professores
✓ Auditoria acadêmica

Os dados SÃO:
✓ Criptografados em trânsito
✓ Armazenados com segurança
✓ Usados apenas para fins educacionais
✓ Protegidos pela LGPD

Os dados NÃO SÃO:
✗ Compartilhados com terceiros
✗ Vendidos ou comercializados
✗ Usados para outros fins

================================================================================
CONTATO E SUPORTE
================================================================================

Em caso de dúvidas ou problemas:

📧 Email: suporte@instituicao.edu.br
📱 Telefone: (XX) XXXX-XXXX
🌐 Site: www.instituicao.edu.br/suporte

Horário de atendimento: Segunda a Sexta, 8h às 18h

================================================================================
DICAS PARA UM EXAME SEM PROBLEMAS
================================================================================

✓ Teste o monitor ANTES do dia do exame
✓ Certifique-se de ter boa conexão com internet
✓ Use um computador confiável
✓ Feche todos os programas desnecessários
✓ Desative notificações do sistema
✓ Mantenha o computador plugado (não use bateria)
✓ Tenha o contato do suporte técnico à mão

================================================================================

Boa sorte no seu exame! 🎓

================================================================================

