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

  MODO MANUAL (plano B) → passe só o LINK (não precisa copiar o texto da página).
      python3 zayn_by_gloss.py url  "https://hugogloss.uol.com.br/materia-x/"

  MODO À PROVA DE TUDO → o site bloqueia cópia (Ctrl+C/V) e acesso automático?
      Basta LER a hashtag na tela e digitar o nome da música:
      python3 zayn_by_gloss.py musica "Pillowtalk"

  Ver o resultado parcial a qualquer momento:
      python3 zayn_by_gloss.py status

  Zerar o progresso (começar do dia do zero):
      python3 zayn_by_gloss.py reset

  SOM: toca um bipe a cada música nova e um alerta ao completar as 6.
      python3 zayn_by_gloss.py --testar-som        # testa os sons agora
      python3 zayn_by_gloss.py vigiar --mudo        # desliga o som

Progresso é salvo em  progresso.json  (sobrevive a reinícios do robô).

Observação importante: use este robô NO SEU COMPUTADOR, onde o site abre normal.
Se o site bloquear o acesso automático, o robô avisa e você usa o modo manual.
"""

from __future__ import annotations

import json
import os
import platform
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
# Alerta sonoro (multiplataforma, sem dependências externas)
# ---------------------------------------------------------------------------
SOM_LIGADO = True  # vira False com a flag --mudo


def _beep_terminal(vezes: int = 1) -> None:
    """Toca o bipe do terminal (fallback universal)."""
    for _ in range(vezes):
        sys.stdout.write("\a")
        sys.stdout.flush()
        time.sleep(0.15)


def tocar_som(tipo: str = "nova") -> None:
    """
    Toca um som. tipo:
      - "nova"     → bipe curto quando acha uma música nova.
      - "completo" → melodia/alerta mais longo quando acha as 6.
    Tenta usar o som do SO; se não der, cai no bipe do terminal.
    """
    if not SOM_LIGADO:
        return
    sistema = platform.system()
    try:
        if sistema == "Windows":
            import winsound  # type: ignore
            if tipo == "completo":
                for freq in (660, 880, 990, 1320):
                    winsound.Beep(freq, 180)
            else:
                winsound.Beep(880, 150)
            return
        if sistema == "Darwin":  # macOS
            som = ("/System/Library/Sounds/Hero.aiff" if tipo == "completo"
                   else "/System/Library/Sounds/Ping.aiff")
            if os.path.exists(som):
                os.system(f"afplay {som} >/dev/null 2>&1 &")
                return
        else:  # Linux: tenta players comuns, senão bipe do terminal
            for player, arg in (("paplay", "/usr/share/sounds/freedesktop/stereo/complete.oga"),
                                ("aplay", None)):
                if _tem_comando(player) and (arg is None or os.path.exists(arg)):
                    if arg:
                        os.system(f"{player} {arg} >/dev/null 2>&1 &")
                        return
    except Exception:
        pass
    # Fallback universal: bipe do terminal
    _beep_terminal(4 if tipo == "completo" else 1)


def _tem_comando(nome: str) -> bool:
    from shutil import which
    return which(nome) is not None


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
        print("   🔊 (tocando alerta sonoro)")
        tocar_som("completo")
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
                icone = " 🔊" if SOM_LIGADO else ""
                print(f"  🎵 NOVA música encontrada: #{musica}  (ordem {len(prog['sequencia'])}){icone}")
                tocar_som("nova")
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


def _sugerir_parecidas(chave: str, limite: int = 3) -> list[str]:
    """Sugere músicas do catálogo com nome parecido (para erros de digitação)."""
    import difflib
    nomes = sorted({m["oficial"] for m in MUSICAS})
    chaves = {normalizar(n): n for n in nomes}
    aprox = difflib.get_close_matches(chave, list(chaves.keys()), n=limite, cutoff=0.6)
    return [chaves[a] for a in aprox]


def cmd_musica(args: list[str]) -> int:
    """Registra uma música que VOCÊ leu/digitou (à prova de bloqueio de cópia)."""
    if not args:
        print("Uso: python3 zayn_by_gloss.py musica \"Pillowtalk\"")
        print("     (digite o título que você LEU na matéria — não precisa copiar nada)")
        return 1
    entrada = " ".join(args).lstrip("#")
    chave = normalizar(entrada)
    prog = carregar_progresso()

    if chave in INDICE_MUSICAS:
        oficial = INDICE_MUSICAS[chave]
        if registrar_descoberta(prog, oficial, origem="digitada manualmente"):
            print(f"  🎵 NOVA música registrada: {oficial}  (ordem {len(prog['sequencia'])})")
        else:
            print(f"  (A música '{oficial}' já estava na sequência — não duplicado.)")
        salvar_progresso(prog)
        imprimir_status(prog)
        return 0

    # Não bateu: ajuda com sugestões
    print(f"⚠️  '{entrada}' não bateu com nenhuma música do catálogo.")
    sugestoes = _sugerir_parecidas(chave)
    if sugestoes:
        print("    Você quis dizer uma destas?")
        for s in sugestoes:
            print(f"      • {s}   →   python3 zayn_by_gloss.py musica \"{s}\"")
    else:
        print("    Confira a grafia. Se for mesmo uma música do Zayn que não está")
        print("    no catálogo, me avise para eu adicioná-la.")
    return 2


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
    "musica": cmd_musica,
    "status": cmd_status,
    "reset": cmd_reset,
}


def main(argv: list[str]) -> int:
    global SOM_LIGADO
    # Flags globais
    if "--mudo" in argv:
        SOM_LIGADO = False
        argv = [a for a in argv if a != "--mudo"]
    if "--testar-som" in argv:
        print("🔊 Testando som de 'música nova'..."); tocar_som("nova")
        time.sleep(0.6)
        print("🔊 Testando som de 'concurso completo'..."); tocar_som("completo")
        return 0
    if not argv or argv[0] not in COMANDOS:
        print(__doc__)
        return 1
    return COMANDOS[argv[0]](argv[1:])


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        print("\nEncerrado.")
