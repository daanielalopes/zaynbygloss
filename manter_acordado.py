#!/usr/bin/env python3
"""
☕ MANTER ACORDADO — impede o Windows de suspender/dormir ENQUANTO este
   programa estiver aberto. Não altera NENHUMA configuração do sistema:
   assim que você fechar esta janela (ou apertar Ctrl+C), tudo volta ao normal.

USO:
    python manter_acordado.py

Deixe esta janela ABERTA numa aba separada do cmd enquanto o robô vigia o site.
Para parar, feche a janela ou aperte Ctrl+C.
"""

import ctypes
import sys
import time
from datetime import datetime

# Reconfigura a saída para UTF-8 (evita erro com emojis no cmd do Windows).
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Flags da API SetThreadExecutionState (Windows):
ES_CONTINUOUS = 0x80000000        # mantém o estado até ser alterado de novo
ES_SYSTEM_REQUIRED = 0x00000001   # impede o PC de dormir
ES_DISPLAY_REQUIRED = 0x00000002  # mantém a TELA ligada também


def manter_acordado(manter_tela: bool = True) -> None:
    flags = ES_CONTINUOUS | ES_SYSTEM_REQUIRED
    if manter_tela:
        flags |= ES_DISPLAY_REQUIRED
    ctypes.windll.kernel32.SetThreadExecutionState(flags)


def liberar() -> None:
    # Volta ao comportamento normal de energia do Windows.
    ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS)


def main() -> int:
    manter_tela = "--sem-tela" not in sys.argv  # por padrão, mantém a tela ligada
    manter_acordado(manter_tela=manter_tela)
    print("☕ PC mantido ACORDADO. Esta janela precisa ficar ABERTA.")
    print(f"   Tela ligada: {'sim' if manter_tela else 'não (só não dorme o PC)'}")
    print("   Para liberar: feche esta janela ou aperte Ctrl+C.\n")
    try:
        while True:
            # Reforça o estado periodicamente (bom para sessões longas).
            manter_acordado(manter_tela=manter_tela)
            agora = datetime.now().strftime("%H:%M:%S")
            print(f"[{agora}] mantendo acordado...", end="\r", flush=True)
            time.sleep(60)
    except KeyboardInterrupt:
        pass
    finally:
        liberar()
        print("\n✅ Liberado. O PC volta ao comportamento normal de energia.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
