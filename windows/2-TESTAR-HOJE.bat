@echo off
chcp 65001 >nul
title Zayn By Gloss - Teste de Hoje
cd /d "%~dp0.."
echo ============================================================
echo   TESTE DE HOJE - uma varredura unica da home do Hugo Gloss
echo ------------------------------------------------------------
echo   O navegador vai abrir e o robo vai LER as materias de hoje.
echo   Hoje pode achar 0 musicas (normal). O importante e confirmar
echo   que ele consegue LER o site no seu PC.
echo ============================================================
echo.
python zayn_by_gloss.py reset
python zayn_visual.py testar --mostrar
echo.
echo ============================================================
echo   Teste finalizado. Veja acima quantas materias foram lidas.
echo ============================================================
pause
