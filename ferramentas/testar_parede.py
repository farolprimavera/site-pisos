"""
Renderiza alguns produtos numa parede, para conferir antes de gerar tudo.

Rodar:  python ferramentas/testar_parede.py <parede> <id do produto> [...]
        ->  ferramentas/build/parede-<parede>-<id>.jpg
"""
import json, sys
from pathlib import Path
import cv2

AQUI = Path(__file__).resolve().parent
SITE = AQUI.parent
AMB = SITE / "ambientes"
FOTOS = SITE.parent / "fotos"
sys.path.insert(0, str(AQUI))
import render as R


def main():
    parede, ids = sys.argv[1], sys.argv[2:]
    par = json.loads((AMB / "paredes.json").read_text(encoding="utf-8"))[parede]
    pisos = {p["id"]: p for p in json.loads((SITE / "dados" / "pisos.json").read_text(encoding="utf-8"))["pisos"]}
    (AQUI / "build").mkdir(exist_ok=True)
    for i in ids:
        p = pisos[i]
        kw = R.parametros_parede(p)
        out = R.renderizar_parede(par, AMB, cv2.imread(str(FOTOS / f"{p['foto']}.jpg")), p["medida_cm"], **kw)
        arq = AQUI / "build" / f"parede-{parede}-{i}.jpg"
        cv2.imwrite(str(arq), out, [cv2.IMWRITE_JPEG_QUALITY, 90])
        print("ok", arq.name, kw)


if __name__ == "__main__":
    main()
