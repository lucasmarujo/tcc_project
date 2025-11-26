@echo off
echo ========================================
echo Ativando ambiente virtual...
echo ========================================
cd ..\..
call .venv\Scripts\activate.bat
cd yolov8_model\scripts

echo.
echo ========================================
echo Executando treinamento...
echo ========================================
python train.py

pause


