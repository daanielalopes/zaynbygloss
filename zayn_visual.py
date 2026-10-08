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
    # TESTE DE HOJE: uma varredura única da home (sem loop), para conferir
    # se o robô consegue ler as matérias do site no seu PC.
    # É RÁPIDO por padrão (abas em paralelo, sem baixar imagens):
    python3 zayn_visual.py testar               # home + abre as matérias (recomendado)
    python3 zayn_visual.py testar --mostrar     # idem, navegador visível
    python3 zayn_visual.py testar --limite 25   # abrir mais matérias
    python3 zayn_visual.py testar --so-home     # ler APENAS a home (não abre posts)
    python3 zayn_visual.py testar --devagar     # modo antigo (1 por vez)

    # Obs.: as regras do concurso dizem que as hashtags ficam "no meio das
    # MATÉRIAS", por isso o padrão é abrir os posts. --so-home é mais rápido,
    # mas pode não encontrar hashtags que só aparecem dentro da matéria.

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

# Garante que emojis/acentos sejam impressos sem erro no terminal do Windows (cp1252).
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except Exception:
        pass

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


def ler_varias_rapido(urls, mostrar: bool = False, espera_ms: int = 800,
                      paralelo: int = 4):
    """
    Lê VÁRIAS páginas rápido: abre UM navegador só e processa em lotes de
    `paralelo` abas simultâneas. Devolve dict {url: texto}.

    Muito mais rápido que abrir/fechar um navegador por página, porque:
      - o Chromium é iniciado uma única vez;
      - várias abas carregam ao mesmo tempo;
      - a espera por página é menor (padrão 800ms).
    Para desligar imagens/fontes e acelerar ainda mais, bloqueia esses recursos.
    """
    from playwright.sync_api import sync_playwright

    resultados: dict[str, str] = {}
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
        # Bloqueia imagens/mídia/fontes: não precisamos delas para ler o texto.
        def _rota(route):
            if route.request.resource_type in ("image", "media", "font"):
                route.abort()
            else:
                route.continue_()
        contexto.route("**/*", _rota)

        def ler_uma(url: str) -> str:
            page = contexto.new_page()
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(espera_ms)
                return page.evaluate("() => document.body.innerText") or ""
            except Exception:
                return ""
            finally:
                page.close()

        # processa em lotes (paralelo abas por vez)
        for i in range(0, len(urls), paralelo):
            lote = urls[i:i + paralelo]
            paginas = []
            for url in lote:
                page = contexto.new_page()
                paginas.append((url, page))
            # dispara navegação de todas as abas do lote
            for url, page in paginas:
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=30000)
                except Exception:
                    pass
            # espera uma vez para o lote inteiro, depois coleta
            if paginas:
                paginas[0][1].wait_for_timeout(espera_ms)
            for url, page in paginas:
                try:
                    resultados[url] = page.evaluate("() => document.body.innerText") or ""
                except Exception:
                    resultados[url] = ""
                finally:
                    page.close()
        navegador.close()
    return resultados


def cmd_url(args: list[str]) -> int:
    mostrar = "--mostrar" in args
    sem_hashtag = "--sem-hashtag" in args
    args = [a for a in args if a not in ("--mostrar", "--sem-hashtag")]
    if not args:
        print('Uso: python3 zayn_visual.py url "https://hugogloss.uol.com.br/materia/" [--mostrar] [--sem-hashtag]')
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
    novas = processar_texto(prog, texto, origem=f"visual: {url}", link=url,
                            sem_hashtag=sem_hashtag)
    if not novas:
        print("  (Nenhuma música reconhecida nesta matéria.)")
    salvar_progresso(prog)
    imprimir_status(prog)
    return 0


def cmd_testar(args: list[str]) -> int:
    """UMA varredura da home AGORA (sem loop). Ideal para testar hoje.

    Rápido por padrão (abas em paralelo, sem imagens). Use --devagar para o
    modo antigo (uma página por vez) e --limite N para ler mais/menos matérias.
    """
    mostrar = "--mostrar" in args
    limite = 15  # quantas matérias abrir no teste (para não demorar demais)
    if "--limite" in args:
        i = args.index("--limite")
        try:
            limite = int(args[i + 1])
        except (IndexError, ValueError):
            pass

    # As regras dizem que as hashtags ficam "no meio das MATÉRIAS", então o
    # padrão é abrir as matérias. Use --so-home para ler apenas a home.
    so_home = "--so-home" in args

    print("🧪 MODO TESTE — varredura única a partir da home do Hugo Gloss.")
    prog = carregar_progresso()
    agora = datetime.now().strftime("%H:%M:%S")
    try:
        texto_home, links = ler_pagina_visual(SITE_BASE, mostrar=mostrar)
    except Exception as exc:  # noqa: BLE001
        print(f"❌ Não consegui abrir a home ({exc}).")
        print("   Verifique sua internet e se o Playwright foi instalado:")
        print("     pip install -r requirements.txt && playwright install chromium")
        return 2

    # Também procura hashtags no próprio texto da home (caso apareçam lá)
    processar_texto(prog, texto_home, origem=f"home: {SITE_BASE}",
                    verbose=True, link=SITE_BASE)

    if so_home:
        salvar_progresso(prog)
        print("   (Modo --so-home: li apenas a home, não abri as matérias.)")
        print("   ⚠️  Atenção: as regras dizem que as hashtags ficam no MEIO das")
        print("       matérias, então o normal é precisar ABRIR os posts.")
        imprimir_status(prog)
        return 0

    materias = links_de_materias("".join(f'<a href="{l}"></a>' for l in links))
    print(f"[{agora}] Encontrei {len(materias)} links de matérias na home.")
    if not materias:
        print("   (Nenhum link de matéria reconhecido — o site pode ter mudado o layout.)")
        imprimir_status(prog)
        return 0

    lidas_ok = 0
    com_musica = 0
    prog.setdefault("materias_vistas", {})
    alvos = materias[:limite]

    devagar = "--devagar" in args
    if devagar:
        # modo antigo: uma página por vez (navegador abre/fecha a cada uma)
        for idx, url in enumerate(alvos, 1):
            try:
                texto, _ = ler_pagina_visual(url, mostrar=mostrar)
                lidas_ok += 1
            except Exception as exc:  # noqa: BLE001
                print(f"   {idx}. ⚠️  falhou ao ler: {url}  ({exc})")
                continue
            prog["materias_vistas"][url] = agora
            antes = len(prog.get("sequencia", []))
            processar_texto(prog, texto, origem=f"teste: {url}", verbose=True, link=url)
            marca = "🎵 TEM MÚSICA!" if len(prog["sequencia"]) > antes else "— sem música"
            if len(prog["sequencia"]) > antes:
                com_musica += 1
            print(f"   {idx}. {marca}  {url}")
    else:
        # ⚡ MODO RÁPIDO (padrão): um navegador só, abas em paralelo, sem imagens
        print("   ⚡ Lendo em modo rápido (paralelo, sem imagens)...")
        textos = ler_varias_rapido(alvos, mostrar=mostrar)
        for idx, url in enumerate(alvos, 1):
            texto = textos.get(url, "")
            if not texto:
                print(f"   {idx}. ⚠️  falhou ao ler: {url}")
                continue
            lidas_ok += 1
            prog["materias_vistas"][url] = agora
            antes = len(prog.get("sequencia", []))
            processar_texto(prog, texto, origem=f"teste: {url}", verbose=True, link=url)
            marca = "🎵 TEM MÚSICA!" if len(prog["sequencia"]) > antes else "— sem música"
            if len(prog["sequencia"]) > antes:
                com_musica += 1
            print(f"   {idx}. {marca}  {url}")

    salvar_progresso(prog)
    print(f"\n✅ Teste concluído: {lidas_ok}/{min(limite, len(materias))} matérias lidas com sucesso.")
    print(f"   Matérias com música detectada: {com_musica}")
    print("   → Se as matérias foram LIDAS sem erro, o robô está pronto para o dia 8. 🎯")
    imprimir_status(prog)
    return 0


def cmd_vigiar(args: list[str]) -> int:
    mostrar = "--mostrar" in args
    args = [a for a in args if a != "--mostrar"]
    intervalo = 30  # 30 segundos por padrão
    if "--intervalo" in args:
        i = args.index("--intervalo")
        try:
            intervalo = int(args[i + 1])
        except (IndexError, ValueError):
            print("--intervalo precisa de um número em segundos.")
            return 1
    # Mínimo de segurança: ciclos muito curtos não dão tempo de abrir o
    # navegador e ler as matérias, e podem fazer o site te bloquear por
    # excesso de acessos. 15s é o piso recomendado.
    if intervalo < 15:
        print(f"⚠️  Intervalo {intervalo}s é muito baixo; usando o mínimo seguro de 15s.")
        intervalo = 15

    # DATA-ALVO: por padrão, só processa matérias publicadas em 08/10/2026
    # (o dia do concurso). Use --data DD/MM/AAAA para mudar, ou --todas-datas
    # para desligar o filtro.
    data_alvo: str | None = "08/10/2026"
    if "--todas-datas" in args:
        data_alvo = None
        args = [a for a in args if a != "--todas-datas"]
    if "--data" in args:
        i = args.index("--data")
        try:
            data_alvo = args[i + 1]
        except IndexError:
            print("--data precisa de uma data no formato DD/MM/AAAA. Ex: --data 08/10/2026")
            return 1

    print("👁️  MODO VIGIA VISUAL ativado (navegador real).")
    print(f"   A cada {intervalo}s: lê a HOME, abre as matérias NOVAS (em paralelo)")
    print("   e procura as hashtags dentro de cada post. Ctrl+C para parar.")
    if data_alvo:
        print(f"   📅 Só conta matérias publicadas em {data_alvo} (ignora as antigas).")
    else:
        print("   📅 Filtro de data DESLIGADO (lê matérias de qualquer dia).")
    if mostrar:
        print("   Navegador VISÍVEL: você vai ver o robô percorrendo as matérias.\n")
    else:
        print("   (Use --mostrar para abrir o navegador na sua frente.)\n")

    prog = carregar_progresso()
    imprimir_status(prog)

    while len(prog.get("sequencia", [])) < TOTAL_MUSICAS_CONCURSO:
        agora = datetime.now().strftime("%H:%M:%S")
        try:
            # 1) lê a HOME e extrai os links das matérias
            texto_home, links = ler_pagina_visual(SITE_BASE, mostrar=mostrar)
            materias = links_de_materias(
                "".join(f'<a href="{l}"></a>' for l in links)
            )
            print(f"[{agora}] {len(materias)} matérias na home. Verificando novas...")
            prog.setdefault("materias_vistas", {})

            # A home não tem UMA data de publicação; o filtro de data é aplicado
            # só nas matérias (abaixo). Aqui procuramos hashtags que, por acaso,
            # já apareçam no texto da home.
            novas_total = processar_texto(prog, texto_home, origem=f"home: {SITE_BASE}",
                                          link=SITE_BASE, verbose=True)

            # 2) abre apenas as matérias AINDA NÃO VISTAS, em paralelo (rápido)
            novas_urls = [u for u in materias if u not in prog["materias_vistas"]]
            if novas_urls:
                print(f"           → {len(novas_urls)} matéria(s) nova(s) para ler.")
                textos = ler_varias_rapido(novas_urls, mostrar=mostrar)
                lidas = 0
                achadas_no_ciclo = 0
                for url in novas_urls:
                    texto = textos.get(url, "")
                    if not texto:
                        # Falhou ao ler (ex.: internet oscilou): NÃO marca como vista,
                        # para tentar de novo no próximo ciclo e não perder a matéria.
                        continue
                    prog["materias_vistas"][url] = agora
                    lidas += 1
                    achou = processar_texto(prog, texto, origem=f"visual: {url}",
                                            link=url, verbose=True, data_alvo=data_alvo)
                    novas_total += achou
                    achadas_no_ciclo += achou
                falhas = len(novas_urls) - lidas
                if falhas:
                    print(f"           ⚠️  {falhas} matéria(s) falharam ao carregar; "
                          f"vou tentar de novo no próximo ciclo.")
                # Feedback: avisa que leu as novas e se achou (ou não) música do Zayn.
                if lidas and achadas_no_ciclo == 0:
                    print(f"           ✔️  Li {lidas} matéria(s) nova(s): nenhuma música do Zayn nelas.")
                elif achadas_no_ciclo:
                    print(f"           🎵 Achei {achadas_no_ciclo} música(s) nas matérias novas!")
            else:
                print("           (sem matérias novas desde o último ciclo — seguindo de olho.)")
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


COMANDOS = {"testar": cmd_testar, "url": cmd_url, "vigiar": cmd_vigiar}


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
