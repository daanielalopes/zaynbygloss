@echo off
chcp 65001 >nul
title Zayn By Gloss - Teste de E-mail
cd /d "%~dp0.."
echo ============================================================
echo   TESTE DE E-MAIL
echo ------------------------------------------------------------
echo   Envia um e-mail de teste para confirmar que a configuracao
echo   (email_config.json) esta correta.
echo.
echo   Antes de rodar: copie email_config.exemplo.json para
echo   email_config.json e preencha com seus dados (veja o LEIA-ME).
echo ============================================================
echo.
python notificador_email.py
echo.
pause
