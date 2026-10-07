@echo off
chcp 65001 >nul
title Zayn By Gloss - VIGIANDO (dia do concurso)
cd /d "%~dp0.."
echo ============================================================
echo   MODO VIGIA - deixe esta janela ABERTA o dia todo (dia 8)
echo ------------------------------------------------------------
echo   O robo vai checar o Hugo Gloss de tempos em tempos, abrir
echo   as materias novas, achar as hashtags das musicas e TOCAR
echo   UM SOM quando encontrar cada uma (e um alerta nas 6).
echo.
echo   Para PARAR: feche esta janela ou aperte Ctrl + C.
echo ============================================================
echo.
echo Zerar o progresso antes de comecar? (recomendado no inicio do dia)
set /p ZERAR="Digite S para zerar, ou ENTER para continuar: "
if /i "%ZERAR%"=="S" python zayn_by_gloss.py reset
echo.
python zayn_visual.py vigiar --mostrar --intervalo 300
echo.
pause
