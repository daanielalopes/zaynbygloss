# 🎤 Zayn By Gloss — robô caça-hashtags

Robô que participa do **Concurso Cultural "Zayn By Gloss"** (Hugo Gloss).
Na quinta-feira (08/10), o site esconde **6 títulos de músicas do Zayn** no meio
das matérias, cada um marcado com uma **hashtag** (ex.: `#PILLOWTALK`). A missão é
achar as **6 músicas na ordem exata de publicação**. Este robô faz isso.

## O que ele faz

- **Modo visual** (`zayn_visual.py`): abre um navegador real e **lê a tela como um
  humano**, contornando o bloqueio de cópia (Ctrl+C) do site.
- **Vigia o site** sozinho (ou funciona manualmente, caso o site bloqueie bots).
- Procura hashtags nas matérias e **reconhece a música** comparando com uma
  **discografia ampla do Zayn** (de *Mind of Mine* a *Konnakol*, 2026).
- Registra a **ordem de publicação** e salva o progresso.
- **Rede de segurança:** mostra também qualquer hashtag que *não* esteja no
  catálogo, para você conferir manualmente (caso seja uma faixa não cadastrada).

## Como usar

> Precisa só de **Python 3**. Rode **no seu computador** (onde o site abre normal).
> Guia detalhado em [`COMO_USAR_AMANHA.md`](COMO_USAR_AMANHA.md).

```bash
python3 zayn_by_gloss.py reset          # zera o progresso (começo do dia)
python3 zayn_by_gloss.py vigiar         # modo automático (vigia o site)
python3 zayn_by_gloss.py url  "<link>"  # modo manual: por link
python3 zayn_by_gloss.py texto "<texto com #Hashtag>"   # modo manual: por texto
python3 zayn_by_gloss.py status         # ver o resultado parcial
```

Quando achar as 6, ele mostra a **sequência final** pronta para o formulário.

## Notificação por e-mail (opcional)

O robô pode **enviar um e-mail** assim que encontrar cada música, informando o
**nome da música** e o **link do post**. Para ativar, copie
`email_config.exemplo.json` para `email_config.json` e preencha com seus dados
(use uma *Senha de app* do Gmail — veja o cabeçalho de `notificador_email.py`).
Sem configuração, o robô funciona normal, apenas sem e-mail.

## Arquivos

- `zayn_visual.py` — **robô visual** (navegador real, lê a tela mesmo com cópia bloqueada).
- `zayn_by_gloss.py` — robô base (vigiar / url / texto / musica / status / reset).
- `musicas_zayn.py` — discografia do Zayn com variações de escrita das hashtags.
- `notificador_email.py` — envio de e-mail (nome da música + link do post).
- `email_config.exemplo.json` — modelo de configuração do e-mail.
- `COMO_USAR_AMANHA.md` — passo a passo para o dia do concurso.

## Observação

O robô foi testado com simulações porque o ambiente de desenvolvimento não tem
acesso de rede ao site do Hugo Gloss. No seu computador, o modo automático tende
a funcionar; se o site bloquear o acesso, o **modo manual** garante o resultado.

---

> Projeto feito para fins do concurso cultural. As músicas e a marca pertencem aos
> seus respectivos donos.
