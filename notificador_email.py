"""
📧 Notificador por e-mail do robô "Zayn By Gloss".

Envia um e-mail assim que o robô encontra uma música, dizendo:
  - o NOME da música
  - o LINK do post onde ela foi achada

Usa apenas a biblioteca padrão do Python (smtplib) — não precisa instalar nada.

------------------------------------------------------------------------------
COMO CONFIGURAR (uma vez só):
  Crie um arquivo chamado  email_config.json  na mesma pasta, assim:

    {
      "ativo": true,
      "smtp_host": "smtp.gmail.com",
      "smtp_port": 587,
      "remetente": "SEU_EMAIL@gmail.com",
      "senha_app": "xxxx xxxx xxxx xxxx",
      "destinatario": "PARA_ONDE_ENVIAR@gmail.com"
    }

  IMPORTANTE (Gmail): "senha_app" NÃO é a sua senha normal. É uma "Senha de app"
  de 16 letras, gerada em:  https://myaccount.google.com/apppasswords
  (Precisa ter a verificação em duas etapas ativada na conta Google.)

  Alternativa: definir as mesmas chaves como variáveis de ambiente:
    ZBG_SMTP_HOST, ZBG_SMTP_PORT, ZBG_EMAIL, ZBG_SENHA_APP, ZBG_DEST

  Se não houver configuração, o robô simplesmente NÃO envia e-mail (segue normal).
------------------------------------------------------------------------------
"""

from __future__ import annotations

import json
import os
import smtplib
import ssl
import sys
from email.message import EmailMessage

# Garante que emojis/acentos sejam impressos sem erro no terminal do Windows (cp1252).
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except Exception:
        pass

_CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "email_config.json")


def _carregar_config() -> dict | None:
    # 1) arquivo email_config.json
    cfg: dict = {}
    if os.path.exists(_CONFIG_PATH):
        try:
            with open(_CONFIG_PATH, encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception:
            cfg = {}
    # 2) variáveis de ambiente sobrescrevem/complementam
    env = os.environ
    cfg.setdefault("smtp_host", env.get("ZBG_SMTP_HOST", "smtp.gmail.com"))
    cfg.setdefault("smtp_port", int(env.get("ZBG_SMTP_PORT", "587")))
    if env.get("ZBG_EMAIL"):
        cfg["remetente"] = env["ZBG_EMAIL"]
    if env.get("ZBG_SENHA_APP"):
        cfg["senha_app"] = env["ZBG_SENHA_APP"]
    if env.get("ZBG_DEST"):
        cfg["destinatario"] = env["ZBG_DEST"]

    # precisa do mínimo para enviar
    if not cfg.get("remetente") or not cfg.get("senha_app") or not cfg.get("destinatario"):
        return None
    if cfg.get("ativo") is False:
        return None
    return cfg


def email_configurado() -> bool:
    return _carregar_config() is not None


def enviar_email_musica(musica: str, link: str, ordem: int, total: int) -> bool:
    """
    Envia um e-mail avisando sobre uma música encontrada.
    Retorna True se enviou, False se não há config ou se falhou.
    """
    cfg = _carregar_config()
    if not cfg:
        return False

    assunto = f"🎵 Zayn By Gloss: música {ordem}/{total} encontrada — {musica}"
    corpo = (
        f"O robô encontrou uma música do concurso!\n\n"
        f"Música: {musica}\n"
        f"Ordem:  {ordem} de {total}\n"
        f"Post:   {link}\n\n"
        f"— Robô Zayn By Gloss"
    )

    msg = EmailMessage()
    msg["Subject"] = assunto
    msg["From"] = cfg["remetente"]
    msg["To"] = cfg["destinatario"]
    msg.set_content(corpo)

    try:
        contexto = ssl.create_default_context()
        with smtplib.SMTP(cfg["smtp_host"], int(cfg["smtp_port"]), timeout=20) as s:
            s.starttls(context=contexto)
            s.login(cfg["remetente"], cfg["senha_app"])
            s.send_message(msg)
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"  ⚠️  Não consegui enviar o e-mail ({exc}).")
        return False


def enviar_email_completo(sequencia: list[dict]) -> bool:
    """E-mail final com as músicas na ordem, quando o concurso completa."""
    cfg = _carregar_config()
    if not cfg:
        return False
    linhas = [f"{i+1}. {item['musica']}  —  {item.get('origem', '')}"
              for i, item in enumerate(sequencia)]
    # Ordem limpa para copiar no formulário: UMA música por linha.
    ordem_para_copiar = "\n".join(item["musica"] for item in sequencia)
    corpo = (
        "🎉 TODAS AS MÚSICAS FORAM ENCONTRADAS!\n\n"
        + "\n".join(linhas)
        + "\n\n==============================\n"
        + "ORDEM PARA O FORMULÁRIO (copie):\n"
        + "==============================\n"
        + ordem_para_copiar
        + "\n\nCorra para o Canal do WhatsApp do Gloss e preencha o formulário!\n"
        "— Robô Zayn By Gloss"
    )
    msg = EmailMessage()
    msg["Subject"] = "✅ Zayn By Gloss: as músicas na ORDEM (corra pro formulário!)"
    msg["From"] = cfg["remetente"]
    msg["To"] = cfg["destinatario"]
    msg.set_content(corpo)
    try:
        contexto = ssl.create_default_context()
        with smtplib.SMTP(cfg["smtp_host"], int(cfg["smtp_port"]), timeout=20) as s:
            s.starttls(context=contexto)
            s.login(cfg["remetente"], cfg["senha_app"])
            s.send_message(msg)
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"  ⚠️  Não consegui enviar o e-mail final ({exc}).")
        return False


# Teste rápido: python3 notificador_email.py
if __name__ == "__main__":
    if not email_configurado():
        print("E-mail NÃO configurado. Crie email_config.json (veja instruções no topo).")
        raise SystemExit(1)
    ok = enviar_email_musica("Pillowtalk (TESTE)",
                             "https://hugogloss.uol.com.br/materia-de-teste/", 1, 6)
    print("E-mail de teste enviado!" if ok else "Falha ao enviar e-mail de teste.")
