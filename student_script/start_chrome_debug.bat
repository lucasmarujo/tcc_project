@echo off
REM Script para iniciar o Chrome com debugging port para detecção de Brightspace
REM Este script fecha todas as instâncias do Chrome e abre uma nova com debugging habilitado

echo ========================================
echo  Iniciando Chrome com Debugging
echo ========================================
echo.
echo Este script vai:
echo 1. Fechar todas as instancias do Chrome abertas
echo 2. Iniciar o Chrome com debugging port 9222
echo.
echo IMPORTANTE: Use ESTE Chrome para acessar o Brightspace!
echo.
pause

echo.
echo Fechando instancias do Chrome...
taskkill /F /IM chrome.exe 2>nul
timeout /t 2 >nul

echo.
echo Iniciando Chrome com debugging...
start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222 --remote-allow-origins=* --user-data-dir="%TEMP%\chrome_debug_profile"

echo.
echo Chrome iniciado com sucesso!
echo.
echo Agora voce pode executar o monitor.py
echo O sistema ira detectar automaticamente paginas de prova do Brightspace.
echo.
pause

