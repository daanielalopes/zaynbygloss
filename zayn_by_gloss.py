#!/usr/bin/env python3
"""
🎤 ROBÔ "ZAYN BY GLOSS" — caça-hashtags do concurso cultural do Hugo Gloss
===========================================================================

O que o concurso pede (quinta-feira, 08/10):
  - 6 matérias serão publicadas ao longo do dia.
  - Em cada uma há um TÍTULO de música do Zayn escondido, marcado com # (hashtag).
  - Objetivo: achar as 6 músicas NA ORDEM EXATA em que foram publicadas.

Este robô encontra as hashtags, identifica a música do catálogo do Zayn e
registra a ORDEM. Ele tem dois modos:

  MODO AUTOMÁTICO (vigia)  → fica monitorando o site de X em X minutos.
      python3 zayn_by_gloss.py vigiar
      python3 zayn_by_gloss.py vigiar --intervalo 300   # a cada 5 min

  MODO MANUAL (plano B, à prova de bloqueio) → você cola link ou texto.
      python3 zayn_by_gloss.py url  "https://hugogloss.uol.com.br/materia-x/"
      python3 zayn_by_gloss.py texto "...conteúdo da matéria com #PILLOWTALK..."

  Ver o resultado parcial a qualquer momento:
      python3 zayn_by_gloss.py status

  Zerar o progresso (começar do dia do zero):
      python3 zayn_by_gloss.py reset

Progresso é salvo em  progresso.json  (sobrevive a reinícios do robô).

Observação importante: use este robô NO SEU COMPUTADOR, onde o site abre normal.
Se o site bloquear o acesso automático, o robô avisa e você usa o modo manual.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import unicodedata
from datetime import datetime
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from musicas_zayn import MUSICAS

# ---------------------------------------------------------------------------
# Configurações
# ---------------------------------------------------------------------------
SITE_BASE = "https://hugogloss.uol.com.br/"
ARQ_PROGRESSO = os.path.join(os.path.dirname(os.path.abspath(__file__)), "progresso.json")
TOTAL_MUSICAS_CONCURSO = 6
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0 Safari/537.36"
)


# ---------------------------------------------------------------------------
# Normalização e índice de músicas (para reconhecer variações de escrita)
# ---------------------------------------------------------------------------
def normalizar(texto: str) -> str:
    """minúsculas, sem acento, só letras+números -> chave para comparação."""
    texto = unicodedata.normalize("NFKD", texto.lower())
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]", "", texto)


def construir_indice() -> dict[str, str]:
    """mapeia chave normalizada -> nome oficial da música."""
    indice: dict[str, str] = {}
    for m in MUSICAS:
        indice[normalizar(m["oficial"])] = m["oficial"]
        for alias in m.get("aliases", []):
            indice[normalizar(alias)] = m["oficial"]
    return indice


INDICE_MUSICAS = construir_indice()


# ---------------------------------------------------------------------------
# Detecção de hashtags -> música
# ---------------------------------------------------------------------------
# Hashtags genéricas de site que NÃO são músicas (reduz ruído no modo rede-de-segurança)
HASHTAGS_IGNORAR = {
    "zayn", "zaynmalik", "hugogloss", "gloss", "concursocultural", "zaynbygloss",
    "konnakol", "saopaulo", "sp", "brasil", "show", "meetandgreet", "mg",
    "nubankparque", "turne", "fas", "fa",
}


def achar_musicas_em_texto(texto: str) -> tuple[list[str], list[str]]:
    """
    Procura hashtags no texto. Retorna duas listas (na ordem de aparição, sem repetir):
      - reconhecidas: nomes OFICIAIS das músicas do Zayn que bateram com o catálogo.
      - suspeitas:    hashtags que NÃO bateram com o catálogo nem são genéricas
                      (rede de segurança: pode ser uma música que não cadastrei).
    """
    reconhecidas: list[str] = []
    suspeitas: list[str] = []
    # Hashtag: # seguido de letras/números/_/- (ex.: #PILLOWTALK, #Dusk_Till_Dawn)
    for match in re.finditer(r"#([\w\-]{2,})", texto):
        bruto = match.group(1)
        chave = normalizar(bruto)
        if chave in INDICE_MUSICAS:
            oficial = INDICE_MUSICAS[chave]
            if oficial not in reconhecidas:
                reconhecidas.append(oficial)
        elif chave and chave not in HASHTAGS_IGNORAR:
            etiqueta = "#" + bruto
            if etiqueta not in suspeitas:
                suspeitas.append(etiqueta)
    return reconhecidas, suspeitas


# ---------------------------------------------------------------------------
# Leitura de páginas (HTML -> texto)
# ---------------------------------------------------------------------------
class _ExtratorTexto(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._ignorar = False
        self.partes: list[str] = []
        self.links: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self._ignorar = True
        if tag == "a":
            for nome, valor in attrs:
                if nome == "href" and valor:
                    self.links.append(valor)

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript"):
            self._ignorar = False

    def handle_data(self, data):
        if not self._ignorar and data.strip():
            self.partes.append(data.strip())

    @property
    def texto(self) -> str:
        return " ".join(self.partes)


def baixar(url: str) -> str:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=25) as resp:  # noqa: S310
        charset = resp.headers.get_content_charset() or "utf-8"
        return resp.read().decode(charset, errors="replace")


def extrair_texto_e_links(html: str) -> tuple[str, list[str]]:
    parser = _ExtratorTexto()
    parser.feed(html)
    return parser.texto, parser.links


# ---------------------------------------------------------------------------
# Persistência do progresso
# ---------------------------------------------------------------------------
def carregar_progresso() -> dict:
    if os.path.exists(ARQ_PROGRESSO):
        with open(ARQ_PROGRESSO, encoding="utf-8") as f:
            return json.load(f)
    return {"sequencia": [], "materias_vistas": {}}


def salvar_progresso(prog: dict) -> None:
    with open(ARQ_PROGRESSO, "w", encoding="utf-8") as f:
        json.dump(prog, f, ensure_ascii=False, indent=2)


def registrar_descoberta(prog: dict, musica: str, origem: str) -> bool:
    """Adiciona uma música à sequência se ainda não estiver lá. Retorna True se nova."""
    nomes_ja = [item["musica"] for item in prog["sequencia"]]
    if musica in nomes_ja:
        return False
    prog["sequencia"].append({
        "ordem": len(prog["sequencia"]) + 1,
        "musica": musica,
        "origem": origem,
        "horario": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    return True


# ---------------------------------------------------------------------------
# Impressão de status
# ---------------------------------------------------------------------------
def imprimir_status(prog: dict) -> None:
    seq = prog["sequencia"]
    print("\n" + "=" * 60)
    print(f"🎤 ZAYN BY GLOSS — {len(seq)}/{TOTAL_MUSICAS_CONCURSO} músicas encontradas")
    print("=" * 60)
    if not seq:
        print("Ainda nenhuma música encontrada.")
    else:
        for item in seq:
            print(f"  {item['ordem']}. {item['musica']}")
            print(f"       (encontrada {item['horario']} — {item['origem']})")
    if len(seq) >= TOTAL_MUSICAS_CONCURSO:
        print("\n✅ AS 6 MÚSICAS FORAM ENCONTRADAS! Ordem para o formulário:")
        print("   " + "  →  ".join(i["musica"] for i in seq[:TOTAL_MUSICAS_CONCURSO]))
        print("\n   ➜ Agora corra pro Canal do WhatsApp e preencha o formulário!")
        print("   (Só envie DEPOIS que a 6ª música tiver sido publicada.)")
    else:
        faltam = TOTAL_MUSICAS_CONCURSO - len(seq)
        print(f"\n⏳ Faltam {faltam} música(s). Continue vigiando.")
    suspeitas = prog.get("suspeitas", [])
    if suspeitas:
        print("\n🔎 Hashtags vistas que NÃO estão no catálogo (revise manualmente):")
        for s in suspeitas:
            print(f"     {s}")
    print()


# ---------------------------------------------------------------------------
# Processar uma matéria (texto já extraído)
# ---------------------------------------------------------------------------
def processar_texto(prog: dict, texto: str, origem: str, verbose: bool = True) -> int:
    reconhecidas, suspeitas = achar_musicas_em_texto(texto)
    novas = 0
    for musica in reconhecidas:
        if registrar_descoberta(prog, musica, origem):
            novas += 1
            if verbose:
                print(f"  🎵 NOVA música encontrada: #{musica}  (ordem {len(prog['sequencia'])})")
    if suspeitas and verbose:
        print("  🔎 Rede de segurança — hashtags que NÃO estão no meu catálogo:")
        for s in suspeitas:
            print(f"       {s}  ← confira se é uma música do Zayn que eu não tinha cadastrado")
        # guarda para revisão no status
        prog.setdefault("suspeitas", [])
        for s in suspeitas:
            if s not in prog["suspeitas"]:
                prog["suspeitas"].append(s)
    return novas


# ---------------------------------------------------------------------------
# Descobrir links de matérias na home
# ---------------------------------------------------------------------------
def links_de_materias(home_html: str) -> list[str]:
    _, links = extrair_texto_e_links(home_html)
    materias = []
    for href in links:
        if href.startswith("/"):
            href = SITE_BASE.rstrip("/") + href
        if href.startswith(SITE_BASE) and href.rstrip("/") != SITE_BASE.rstrip("/"):
            # heurística: matérias costumam ter um "slug" após o domínio
            if re.search(r"/[a-z0-9\-]{6,}/?$", href):
                materias.append(href.split("?")[0])
    # remove duplicados preservando ordem
    vistos = set()
    unicos = []
    for u in materias:
        if u not in vistos:
            vistos.add(u)
            unicos.append(u)
    return unicos


# ---------------------------------------------------------------------------
# Comandos
# ---------------------------------------------------------------------------
def cmd_texto(args: list[str]) -> int:
    if not args:
        print("Uso: python3 zayn_by_gloss.py texto \"...conteúdo da matéria...\"")
        return 1
    prog = carregar_progresso()
    texto = " ".join(args)
    processar_texto(prog, texto, origem="colado manualmente")
    salvar_progresso(prog)
    imprimir_status(prog)
    return 0


def cmd_url(args: list[str]) -> int:
    if not args:
        print("Uso: python3 zayn_by_gloss.py url \"https://hugogloss.uol.com.br/materia/\"")
        return 1
    url = args[0]
    prog = carregar_progresso()
    try:
        html = baixar(url)
    except (HTTPError, URLError, TimeoutError) as exc:
        print(f"⚠️  Não consegui acessar a URL automaticamente ({exc}).")
        print("    Plano B: abra a matéria no navegador, copie o texto e use:")
        print("    python3 zayn_by_gloss.py texto \"...texto...\"")
        return 2
    texto, _ = extrair_texto_e_links(html)
    if url in prog["materias_vistas"]:
        print("(Esta matéria já havia sido processada antes — checando mesmo assim.)")
    prog["materias_vistas"][url] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    processar_texto(prog, texto, origem=url)
    salvar_progresso(prog)
    imprimir_status(prog)
    return 0


def cmd_status(_args: list[str]) -> int:
    imprimir_status(carregar_progresso())
    return 0


def cmd_reset(_args: list[str]) -> int:
    if os.path.exists(ARQ_PROGRESSO):
        os.remove(ARQ_PROGRESSO)
    print("Progresso zerado. 🧹")
    return 0


def cmd_vigiar(args: list[str]) -> int:
    intervalo = 600  # 10 min por padrão
    if "--intervalo" in args:
        i = args.index("--intervalo")
        try:
            intervalo = int(args[i + 1])
        except (IndexError, ValueError):
            print("--intervalo precisa de um número em segundos. Ex: --intervalo 300")
            return 1

    print("🔭 MODO VIGIA ativado.")
    print(f"   Checando {SITE_BASE} a cada {intervalo}s. Ctrl+C para parar.")
    print("   (Se o site bloquear o acesso, use o modo manual: 'url' ou 'texto'.)\n")

    prog = carregar_progresso()
    imprimir_status(prog)

    while len(prog["sequencia"]) < TOTAL_MUSICAS_CONCURSO:
        agora = datetime.now().strftime("%H:%M:%S")
        try:
            home = baixar(SITE_BASE)
            materias = links_de_materias(home)
            print(f"[{agora}] {len(materias)} matérias na home. Verificando novas...")
            novas_total = 0
            for url in materias:
                if url in prog["materias_vistas"]:
                    continue
                try:
                    html = baixar(url)
                except (HTTPError, URLError, TimeoutError):
                    continue
                texto, _ = extrair_texto_e_links(html)
                prog["materias_vistas"][url] = agora
                novas_total += processar_texto(prog, texto, origem=url)
            if novas_total:
                salvar_progresso(prog)
                imprimir_status(prog)
            else:
                salvar_progresso(prog)
        except (HTTPError, URLError, TimeoutError) as exc:
            print(f"[{agora}] ⚠️  Site inacessível automaticamente ({exc}).")
            print("        Use o modo manual em outra janela: 'url' ou 'texto'.")

        if len(prog["sequencia"]) >= TOTAL_MUSICAS_CONCURSO:
            break
        try:
            time.sleep(intervalo)
        except KeyboardInterrupt:
            print("\nVigia interrompido pelo usuário.")
            return 0
        prog = carregar_progresso()  # recarrega (caso modo manual tenha rodado em paralelo)

    print("\n🎉 Concurso completo!")
    imprimir_status(prog)
    return 0


COMANDOS = {
    "vigiar": cmd_vigiar,
    "url": cmd_url,
    "texto": cmd_texto,
    "status": cmd_status,
    "reset": cmd_reset,
}


def main(argv: list[str]) -> int:
    if not argv or argv[0] not in COMANDOS:
        print(__doc__)
        return 1
    return COMANDOS[argv[0]](argv[1:])


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        print("\nEncerrado.")
