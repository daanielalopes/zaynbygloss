@echo off
chcp 65001 >nul
title Zayn By Gloss - Instalacao (rodar uma vez)
echo ============================================================
echo   ZAYN BY GLOSS - INSTALACAO (so precisa rodar UMA vez)
echo ============================================================
echo.
echo Verificando se o Python esta instalado...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERRO] Python nao encontrado.
    echo Instale em https://www.python.org/downloads/
    echo IMPORTANTE: marque a opcao "Add Python to PATH" na instalacao.
    echo.
    pause
    exit /b 1
)
python --version
echo.
echo Instalando o navegador do robo (Playwright)...
python -m pip install -r "%~dp0..\requirements.txt"
python -m playwright install chromium
echo.
echo ============================================================
echo   PRONTO! Agora voce pode usar:
echo     2-TESTAR-HOJE.bat   (teste de hoje)
echo     3-VIGIAR-DIA-8.bat  (ligar no dia do concurso)
echo ============================================================
echo.
pause
