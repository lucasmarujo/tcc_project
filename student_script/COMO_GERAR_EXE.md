# Como Gerar o Executável (.exe)

Este guia explica como compilar o monitor.py em um executável (.exe) para distribuição.

## Método 1: Usando build_exe.py (Recomendado)

```bash
cd student_script
python build_exe.py
```

O executável será criado em: `dist/MonitorAluno.exe`

## Método 2: PyInstaller Diretamente

Se o método 1 não funcionar, use o PyInstaller diretamente:

### Passo 1: Instalar PyInstaller

```bash
pip install pyinstaller
```

### Passo 2: Executar PyInstaller

```bash
cd student_script
pyinstaller --onefile --console --name=MonitorAluno ^
  --add-data="config.py;." ^
  --add-data="url_bloqueadas.txt;." ^
  --add-data="face_detection_model;face_detection_model" ^
  --hidden-import=win32gui ^
  --hidden-import=win32process ^
  --hidden-import=win32api ^
  --hidden-import=win32con ^
  --hidden-import=cv2 ^
  --hidden-import=PIL ^
  --hidden-import=numpy ^
  --hidden-import=ultralytics ^
  --hidden-import=torch ^
  --hidden-import=websocket ^
  --hidden-import=requests ^
  --hidden-import=psutil ^
  --hidden-import=pynput ^
  --hidden-import=mss ^
  --collect-all=ultralytics ^
  --collect-all=torch ^
  --collect-all=cv2 ^
  monitor.py
```

**NOTA para Linux/Mac**: Use `:` em vez de `;` no `--add-data`

## Método 3: Comando Simplificado (Básico)

Se os métodos acima falharem, tente uma versão mais simples:

```bash
cd student_script
pyinstaller monitor.py --onefile --console
```

Depois, copie manualmente:
- `config.py` → pasta `dist/`
- `url_bloqueadas.txt` → pasta `dist/`
- `face_detection_model/` → pasta `dist/face_detection_model/`

## Testando o Executável

```bash
cd dist
MonitorAluno.exe
```

## Problemas Comuns

### Erro: "ModuleNotFoundError"
- Certifique-se de que todas as dependências estão instaladas
- Tente adicionar `--hidden-import=nome_do_modulo` ao comando

### Erro: "Failed to execute script"
- Use `--console` em vez de `--noconsole` para ver os erros
- Verifique se os arquivos de dados foram incluídos corretamente

### Executável muito grande
- Normal! O executável pode ter 500MB+ devido aos modelos YOLO e PyTorch
- Para reduzir: remova o modelo YOLO do executável e carregue-o externamente

### Antivírus bloqueia o executável
- Executáveis criados com PyInstaller podem ser marcados como suspeitos
- Adicione exceção no antivírus ou assine o executável digitalmente

## Estrutura Final

```
dist/
├── MonitorAluno.exe          # Executável principal
├── config.py                 # (se não incluído no exe)
├── url_bloqueadas.txt        # (se não incluído no exe)
└── face_detection_model/     # (se não incluído no exe)
    └── yolov8m_200e.pt
```

## Distribuição

Para distribuir para os alunos:

1. Teste o executável completamente
2. Crie um arquivo ZIP com:
   - `MonitorAluno.exe`
   - `README_ALUNO.txt` (instruções para o aluno)
3. Distribua o ZIP
4. Instrua os alunos a:
   - Extrair o ZIP
   - Executar `MonitorAluno.exe`
   - Informar matrícula, nome e email na primeira execução

## Notas Importantes

- O executável NÃO funciona em modo portátil (requer instalação local)
- É necessário conexão com o servidor Django
- O modelo YOLO requer recursos computacionais (CPU/GPU)
- Recomenda-se testar em várias máquinas antes da distribuição final

