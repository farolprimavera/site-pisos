"""
Perspectiva dos ambientes a partir de uma câmera simples (sem inclinação: verticais da foto ficam verticais).

Em ambientes/ambientes.json cada ambiente tem
  "camera": {"pf": [x, y], "altura_cm": 120, "f": 1150}
    pf         ponto de fuga das linhas que "entram" na foto (rodapés das paredes laterais).
               O y dele é a linha do horizonte.
    altura_cm  altura da câmera em relação ao chão (define a escala das peças).
    f          distância focal em pixels (define o quanto o piso "encurta" ao fundo). ~1150 para 1536 px.
    giro       (opcional) ângulo em graus da parede do fundo, se ela não estiver de frente.

Este script calcula os 4 "pontos" + largura/profundidade em cm (o formato que o render.py usa) e grava no json.
Rodar:  python ferramentas/perspectiva.py          (depois confira com ver_perspectiva.py)
"""
import json, math
from pathlib import Path

AQUI = Path(__file__).resolve().parent
AMB = AQUI.parent / "ambientes"


def pontos_camera(cam, altura_img):
    vx, vy = cam["pf"]
    h, f = cam["altura_cm"], cam.get("f", 1150)
    g = math.radians(cam.get("giro", 0))
    z1 = f * h / max(altura_img - vy, 1)          # profundidade da linha de baixo da foto
    z2 = z1 * 3
    L = 2 * z1
    P = z2 - z1

    def proj(X, Z):                               # chão (X lateral, Z profundidade) -> foto
        Xr, Zr = X * math.cos(g) + Z * math.sin(g), -X * math.sin(g) + Z * math.cos(g)
        return [round(vx + f * Xr / Zr, 1), round(vy + f * h / Zr, 1)]

    # longe-esq, longe-dir, perto-dir, perto-esq
    pts = [proj(-L / 2, z2), proj(L / 2, z2), proj(L / 2, z1), proj(-L / 2, z1)]
    return pts, round(L, 1), round(P, 1)


def main():
    arq = AMB / "ambientes.json"
    dados = json.loads(arq.read_text(encoding="utf-8"))
    import cv2
    for k, a in dados.items():
        if "camera" not in a:
            continue
        foto = next((AMB / f"{k}{e}" for e in (".jpg", ".png") if (AMB / f"{k}{e}").exists()))
        hh = cv2.imread(str(foto)).shape[0]
        a["pontos"], a["largura_cm"], a["profundidade_cm"] = pontos_camera(a["camera"], hh)
        print(k, a["pontos"], a["largura_cm"], a["profundidade_cm"])
    arq.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
