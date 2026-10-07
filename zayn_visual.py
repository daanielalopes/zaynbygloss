#!/usr/bin/env python3
"""
👁️ ROBÔ VISUAL "ZAYN BY GLOSS" — lê a tela como um humano (via navegador real)
==============================================================================

Por que este modo existe:
  O site do Hugo Gloss BLOQUEIA copiar texto (Ctrl+C / Ctrl+V) e pode bloquear
  acesso automático simples. Este robô resolve isso abrindo um NAVEGADOR DE
  VERDADE (Chromium, via Playwright), deixando a página carregar como você vê na
  tela, e então LENDO o texto renderizado — sem depender da sua seleção/cópia.

  É a forma mais parecida com "o robô olhando a tela e procurando as palavras".

O que ele faz:
  - Abre a matéria num navegador real e lê o texto visível.
  - Procura as hashtags de músicas do Zayn (mesmo catálogo dos outros modos).
  - Registra na ordem de publicação, no mesmo progresso.json.
  - Pode VIGIAR a home: abre cada matéria nova e repete, de X em X minutos.

------------------------------------------------------------------------------
PRÉ-REQUISITOS (rodar UMA vez no seu computador, que tem internet):
    pip install playwright
    playwright install chromium
------------------------------------------------------------------------------

USO:
    # Ler UMA matéria visualmente (navegador abre, lê, fecha):
    python3 zayn_visual.py url "https://hugogloss.uol.com.br/materia-x/"

    # VIGIAR a home e abrir as matérias novas automaticamente:
    python3 zayn_visual.py vigiar
    python3 zayn_visual.py vigiar --intervalo 300        # a cada 5 min
    python3 zayn_visual.py vigiar --mostrar              # navegador VISÍVEL
                                                         # (ver o robô trabalhando)

    # Ver resultado parcial / zerar (reaproveita os comandos do robô principal):
    python3 zayn_by_gloss.py status
    python3 zayn_by_gloss.py reset

Dica: use --mostrar para abrir o navegador na sua frente e literalmente VER o
robô percorrendo as matérias e achando as hashtags.
"""

from __future__ import annotations

import sys
import time
from datetime import datetime

# Reaproveita toda a lógica já testada do robô principal:
from zayn_by_gloss import (
    SITE_BASE,
    TOTAL_MUSICAS_CONCURSO,
    carregar_progresso,
    imprimir_status,
    links_de_materias,
    processar_texto,
    salvar_progresso,
)


def _checar_playwright():
    try:
        from playwright.sync_api import sync_playwright  # noqa: F401
        return True
    except ImportError:
        print("❌ Playwright não está instalado. No seu computador, rode uma vez:")
        print("     pip install playwright")
        print("     playwright install chromium")
        return False


def ler_pagina_visual(page_url: str, mostrar: bool = False, espera_ms: int = 2500):
    """
    Abre a URL num navegador real e devolve (texto_visivel, lista_de_links).
    Lê o texto RENDERIZADO — contorna bloqueio de cópia (Ctrl+C) do site.
    """
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        navegador = p.chromium.launch(
            headless=not mostrar,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
        )
        contexto = navegador.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/122.0 Safari/537.36"
            ),
            locale="pt-BR",
        )
        page = contexto.new_page()
        page.goto(page_url, wait_until="domcontentloaded", timeout=45000)
        # dá tempo de carregar conteúdo dinâmico (JS) — como um humano esperaria
        page.wait_for_timeout(espera_ms)
        try:
            page.mouse.wheel(0, 4000)  # rola a página para carregar o resto
            page.wait_for_timeout(1000)
        except Exception:
            pass
        # innerText = exatamente o texto que aparece na tela (ignora cópia bloqueada)
        texto = page.evaluate("() => document.body.innerText") or ""
        links = page.evaluate(
            "() => Array.from(document.querySelectorAll('a[href]')).map(a => a.href)"
        ) or []
        navegador.close()
        return texto, links


def cmd_url(args: list[str]) -> int:
    mostrar = "--mostrar" in args
    args = [a for a in args if a != "--mostrar"]
    if not args:
        print('Uso: python3 zayn_visual.py url "https://hugogloss.uol.com.br/materia/" [--mostrar]')
        return 1
    url = args[0]
    prog = carregar_progresso()
    print(f"👁️  Abrindo no navegador real e lendo a tela: {url}")
    try:
        texto, _ = ler_pagina_visual(url, mostrar=mostrar)
    except Exception as exc:  # noqa: BLE001
        print(f"⚠️  Não consegui ler a página ({exc}).")
        print("    Última saída: leia a hashtag na tela e use:")
        print('    python3 zayn_by_gloss.py musica "Nome Da Musica"')
        return 2
    prog.setdefault("materias_vistas", {})[url] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    novas = processar_texto(prog, texto, origem=f"visual: {url}")
    if not novas:
        print("  (Nenhuma hashtag de música reconhecida nesta matéria.)")
    salvar_progresso(prog)
    imprimir_status(prog)
    return 0


def cmd_vigiar(args: list[str]) -> int:
    mostrar = "--mostrar" in args
    args = [a for a in args if a != "--mostrar"]
    intervalo = 600
    if "--intervalo" in args:
        i = args.index("--intervalo")
        try:
            intervalo = int(args[i + 1])
        except (IndexError, ValueError):
            print("--intervalo precisa de um número em segundos.")
            return 1

    print("👁️  MODO VIGIA VISUAL ativado (navegador real).")
    print(f"   Checando {SITE_BASE} a cada {intervalo}s. Ctrl+C para parar.")
    if mostrar:
        print("   Navegador VISÍVEL: você vai ver o robô percorrendo as matérias.\n")
    else:
        print("   (Use --mostrar para abrir o navegador na sua frente.)\n")

    prog = carregar_progresso()
    imprimir_status(prog)

    while len(prog.get("sequencia", [])) < TOTAL_MUSICAS_CONCURSO:
        agora = datetime.now().strftime("%H:%M:%S")
        try:
            _, links = ler_pagina_visual(SITE_BASE, mostrar=mostrar)
            materias = links_de_materias(
                "".join(f'<a href="{l}"></a>' for l in links)
            )
            print(f"[{agora}] {len(materias)} matérias na home. Verificando novas...")
            novas_total = 0
            prog.setdefault("materias_vistas", {})
            for url in materias:
                if url in prog["materias_vistas"]:
                    continue
                try:
                    texto, _ = ler_pagina_visual(url, mostrar=mostrar)
                except Exception:
                    continue
                prog["materias_vistas"][url] = agora
                novas_total += processar_texto(prog, texto, origem=f"visual: {url}")
            salvar_progresso(prog)
            if novas_total:
                imprimir_status(prog)
        except Exception as exc:  # noqa: BLE001
            print(f"[{agora}] ⚠️  Erro ao ler o site ({exc}).")
            print('        Alternativa: leia a hashtag e use  python3 zayn_by_gloss.py musica "Nome"')

        if len(prog.get("sequencia", [])) >= TOTAL_MUSICAS_CONCURSO:
            break
        try:
            time.sleep(intervalo)
        except KeyboardInterrupt:
            print("\nVigia interrompido.")
            return 0
        prog = carregar_progresso()

    print("\n🎉 Concurso completo!")
    imprimir_status(prog)
    return 0


COMANDOS = {"url": cmd_url, "vigiar": cmd_vigiar}


def main(argv: list[str]) -> int:
    if not argv or argv[0] not in COMANDOS:
        print(__doc__)
        return 1
    if not _checar_playwright():
        return 3
    return COMANDOS[argv[0]](argv[1:])


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        print("\nEncerrado.")
