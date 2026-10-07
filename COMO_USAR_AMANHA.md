# 🎤 Como usar o robô "Zayn By Gloss" na quinta-feira (08/10)

Este robô acha os títulos de músicas do Zayn **escondidos com hashtag (#)** nas
matérias do Hugo Gloss e monta a **ordem exata de publicação** das 6 músicas.

> ⚠️ Rode o robô **no seu computador** (onde o site abre normal no navegador).
> Precisa só do **Python 3** instalado — sem instalar mais nada.

---

## Passo a passo

### 1. Antes de começar o dia, zere o progresso
```bash
python3 zayn_by_gloss.py reset
```

### 2. Escolha um modo

#### 🅰️ Modo automático (robô vigia o site sozinho) — tente este primeiro
```bash
python3 zayn_by_gloss.py vigiar
```
- Ele checa a home do Hugo Gloss a cada 10 minutos, abre as matérias novas e
  procura as hashtags das músicas.
- Para checar com mais frequência (ex.: a cada 5 min):
  ```bash
  python3 zayn_by_gloss.py vigiar --intervalo 300
  ```
- Deixe a janela aberta o dia todo. Quando achar as 6, ele avisa com a ordem.
- Pare com **Ctrl + C**.

#### 🅱️ Modo manual (plano B — à prova de bloqueio) — use se o site bloquear o robô
Toda vez que sair uma matéria nova, faça **UMA** destas:

- Passando o **link** da matéria:
  ```bash
  python3 zayn_by_gloss.py url "https://hugogloss.uol.com.br/a-materia-nova/"
  ```
- Ou **copiando o texto** da matéria (mais garantido):
  ```bash
  python3 zayn_by_gloss.py texto "cole aqui o texto da matéria, incluindo a #Hashtag"
  ```

> No modo manual, a **ordem** é a ordem em que você processar as matérias.
> Processe-as **na mesma ordem em que forem publicadas** no site.

### 3. Ver o resultado parcial a qualquer momento
```bash
python3 zayn_by_gloss.py status
```

### 4. Quando as 6 aparecerem
O robô mostra a mensagem ✅ com a **sequência final**. Aí:
1. Espere a **6ª música** ser publicada (regra do concurso).
2. Entre no **Canal do WhatsApp do Gloss** (o 1º link do dia): https://gloss.bz/WhatsappDoGloss
3. Preencha o formulário com os nomes das músicas **na ordem**.
4. As **2 primeiras pessoas** que enviarem certo levam o M&G. ⚡ Seja rápido!

---

## Dicas importantes

- **O robô ajuda a ACHAR e ORDENAR**, mas quem envia o formulário é você — e a
  velocidade do envio decide o prêmio. Deixe seus dados pessoais já prontos.
- O robô reconhece **variações de escrita** da hashtag
  (`#DuskTillDawn`, `#dusk_till_dawn`, `#DUSK-TILL-DAWN` → "Dusk Till Dawn").
- O progresso fica salvo em `progresso.json`. Se o robô fechar, é só reabrir que
  ele continua de onde parou.
- Se uma matéria repetir uma música já encontrada, o robô **não duplica**.

## Lembrete sobre o ambiente onde o robô foi feito

No ambiente onde construí e testei o robô **não há acesso de rede ao Hugo Gloss**
(o site bloqueia e a rede não alcança). Por isso **testei a lógica com simulações**
e ela funciona 100%. No **seu** computador, onde o site abre, o modo automático tem
boa chance de funcionar; se não funcionar, o **modo manual** garante o resultado.

## Arquivos do projeto
- `zayn_by_gloss.py` — o robô (vigia / url / texto / status / reset).
- `musicas_zayn.py` — catálogo de títulos do Zayn (com variações de escrita).
- `progresso.json` — criado automaticamente; guarda o progresso do dia.
