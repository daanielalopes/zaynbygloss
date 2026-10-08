"""
Discografia ampla do Zayn (Zayn Malik), usada para reconhecer os títulos
escondidos nas matérias do concurso "Zayn By Gloss".

O concurso esconde o TÍTULO da música junto de uma hashtag (ex.: #PILLOWTALK).
Cada música tem:
  - "oficial": nome correto (vai assim no formulário).
  - "aliases": formas alternativas de escrita que podem aparecer.

O reconhecimento usa uma "chave normalizada" (minúsculas, sem espaço, sem
pontuação, sem acento), então #DuskTillDawn, #dusk_till_dawn e #DUSK-TILL-DAWN
caem todos em "Dusk Till Dawn".

Fontes das tracklists (resumidas/parafraseadas para compliance):
  - Wikipedia (discografia e páginas dos álbuns)
  - Discogs (tracklists de Icarus Falls)
  - Apple Music / Hoopla (tracklist de Konnakol 2026 + deluxe)
"""

MUSICAS = [
    # ======================= Mind of Mine (2016) =======================
    {"oficial": "Mind of Mindd (Intro)", "aliases": ["mind of mindd", "intro"]},
    {"oficial": "Pillowtalk", "aliases": ["pillow talk"]},
    {"oficial": "It's You", "aliases": ["its you"]},
    {"oficial": "Befour", "aliases": []},
    {"oficial": "She", "aliases": []},
    {"oficial": "Drunk", "aliases": []},
    {"oficial": "Intermission: Flower", "aliases": ["flower", "intermission flower"]},
    {"oficial": "Rear View", "aliases": ["rearview"]},
    {"oficial": "Wrong", "aliases": []},
    {"oficial": "Fool for You", "aliases": ["fool 4 u"]},
    {"oficial": "Borderz", "aliases": ["borders"]},
    {"oficial": "Truth", "aliases": []},
    {"oficial": "Lucozade", "aliases": []},
    {"oficial": "TiO", "aliases": ["tio"]},
    {"oficial": "Blue", "aliases": []},
    {"oficial": "Like I Would", "aliases": []},
    {"oficial": "She Don't Love Me", "aliases": ["she dont love me"]},
    {"oficial": "Fourth of July", "aliases": ["4th of july"]},

    # ======================= Icarus Falls (2018) =======================
    {"oficial": "Let Me", "aliases": []},
    {"oficial": "Stand Still", "aliases": []},
    {"oficial": "If I Got You", "aliases": []},
    {"oficial": "I Don't Mind", "aliases": ["i dont mind"]},
    {"oficial": "You Wish You Knew", "aliases": []},
    {"oficial": "Entertainer", "aliases": []},
    {"oficial": "Good Guy", "aliases": []},
    {"oficial": "Sour Diesel", "aliases": []},
    {"oficial": "Satisfaction", "aliases": []},
    {"oficial": "Scripted", "aliases": []},
    {"oficial": "Natural", "aliases": []},
    {"oficial": "Rainberry", "aliases": []},
    {"oficial": "Fingers", "aliases": []},
    {"oficial": "Good Years", "aliases": []},
    {"oficial": "Insomnia", "aliases": []},
    {"oficial": "Common", "aliases": []},
    {"oficial": "Fresh Air", "aliases": []},
    {"oficial": "There You Are", "aliases": []},
    {"oficial": "No Candle No Light", "aliases": ["no candle no light feat nicki minaj"]},
    {"oficial": "Too Much", "aliases": ["too much feat timbaland"]},
    {"oficial": "Flight of the Stars", "aliases": []},
    {"oficial": "Dusk Till Dawn", "aliases": ["dusk til dawn", "dusk 'til dawn", "from dusk till dawn", "dusk till dawn feat sia"]},
    {"oficial": "All That", "aliases": []},
    {"oficial": "Imprint", "aliases": []},
    {"oficial": "Icarus Interlude", "aliases": []},

    # ======================= Nobody Is Listening (2021) =======================
    {"oficial": "Calamity", "aliases": []},
    {"oficial": "Better", "aliases": []},
    {"oficial": "Outside", "aliases": []},
    {"oficial": "Vibez", "aliases": ["vibes"]},
    {"oficial": "When Love's Around", "aliases": ["when loves around", "when loves around feat syd"]},
    {"oficial": "Connexion", "aliases": []},
    {"oficial": "Sweat", "aliases": []},
    {"oficial": "Windowsill", "aliases": ["window sill", "windowsill feat devlin"]},
    {"oficial": "Tightrope", "aliases": ["tight rope"]},
    {"oficial": "Unfuckwitable", "aliases": []},
    {"oficial": "River Road", "aliases": []},
    {"oficial": "Flames", "aliases": []},

    # ======================= Room Under the Stairs (2024) =======================
    {"oficial": "Dreamin", "aliases": ["dreamin'", "dreaming"]},
    {"oficial": "What I Am", "aliases": []},
    {"oficial": "Stardust", "aliases": []},
    {"oficial": "Alienated", "aliases": []},
    {"oficial": "False Starts", "aliases": []},
    {"oficial": "My Woman", "aliases": []},
    {"oficial": "Birds on a Cloud", "aliases": []},
    {"oficial": "Shoot at Will", "aliases": []},
    {"oficial": "Concrete Kisses", "aliases": []},
    {"oficial": "Fuchsia Sea", "aliases": []},
    {"oficial": "Gates of Hell", "aliases": []},
    {"oficial": "The Time", "aliases": []},
    {"oficial": "How It Feels", "aliases": []},
    {"oficial": "Something in the Water", "aliases": []},
    {"oficial": "Love Like This", "aliases": []},

    # ======================= Konnakol (2026) — nome da turnê no Brasil =======================
    {"oficial": "Nusrat", "aliases": []},
    {"oficial": "Betting Folk", "aliases": []},
    {"oficial": "Used to the Blues", "aliases": []},
    {"oficial": "Sideways", "aliases": []},
    {"oficial": "5th Element", "aliases": ["fifth element"]},
    {"oficial": "Side Effects", "aliases": []},
    {"oficial": "Met Tonight", "aliases": []},
    {"oficial": "Fatal", "aliases": []},
    {"oficial": "Take Turns", "aliases": []},
    {"oficial": "Blooming", "aliases": []},
    {"oficial": "Like I Have You", "aliases": []},
    {"oficial": "Loving the Way I Do", "aliases": ["loving the way i do"]},
    {"oficial": "Breathe", "aliases": []},
    {"oficial": "Die for Me", "aliases": ["die 4 me"]},
    {"oficial": "Bad for You", "aliases": ["bad 4 u"]},
    {"oficial": "Daydreamin'", "aliases": ["daydreaming", "daydreamin"]},
    {"oficial": "Raise the Dead", "aliases": []},

    # ======================= Colaborações / singles / trilhas =======================
    {"oficial": "I Don't Wanna Live Forever", "aliases": ["i dont wanna live forever", "idontwannaliveforever"]},
    {"oficial": "Still Got Time", "aliases": ["still got time feat psb"]},
    {"oficial": "A Whole New World", "aliases": ["a whole new world end title"]},
    {"oficial": "Flowers", "aliases": []},

    # ======================= Feats / colaborações (Zayn como artista convidado) =======================
    # Importante: o concurso pode esconder tambem FEATS do Zayn (ex.: #EyesClosed, #HeavenBaby).
    {"oficial": "Eyes Closed", "aliases": ["eyesclosed", "eyes closed jisoo", "eyes closed jisoo zayn", "eyes closed with zayn", "eyes closed feat zayn"]},
    {"oficial": "Heaven Baby", "aliases": ["heavenbaby", "heaven baby ayra starr", "heaven baby feat zayn"]},
    {"oficial": "Cruel", "aliases": ["cruel feat zayn", "cruel snakehips"]},
    {"oficial": "Dusk Till Dawn (Radio Edit)", "aliases": ["dusk till dawn radio edit"]},
    {"oficial": "Taken", "aliases": []},
    {"oficial": "Entertainer (Remix)", "aliases": ["entertainer remix"]},
    {"oficial": "Back to Sleep (Remix)", "aliases": ["back to sleep remix", "back to sleep"]},
    {"oficial": "Melt", "aliases": []},
    {"oficial": "Taste (Make It Shake)", "aliases": ["taste", "make it shake", "taste make it shake"]},
    {"oficial": "Love Like This", "aliases": ["lovelikethis"]},
    {"oficial": "You Are the Reason", "aliases": ["you are the reason duet", "youarethereason"]},
    {"oficial": "Boundaries", "aliases": []},
    {"oficial": "Who", "aliases": []},
]
