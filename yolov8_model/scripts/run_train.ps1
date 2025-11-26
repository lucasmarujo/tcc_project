# Script PowerShell para executar treinamento

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Ativando ambiente virtual..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Navegar para raiz do projeto
Set-Location -Path "$PSScriptRoot\..\.."

# Ativar ambiente virtual
& ".\.venv\Scripts\Activate.ps1"

# Voltar para scripts
Set-Location -Path "yolov8_model\scripts"

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Executando treinamento..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green

# Executar treinamento
python train.py

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Pressione qualquer tecla para sair..." -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")


