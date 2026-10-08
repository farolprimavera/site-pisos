"""
Desenha a grade de 50 x 50 cm (e a máscara do chão, em vermelho) por cima da foto de cada ambiente,
para conferir a perspectiva antes de gerar tudo.  As linhas da grade devem "correr" junto com os
rodapés e a base dos móveis.

Rodar:  python ferramentas/ver_perspectiva.py [ambiente ...]      ->  ferramentas/build/grade-<ambiente>.jpg
"""
import sys
from pathlib import Path
import cv2
import numpy as np

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import render as R

AMB = AQUI.parent / "ambientes"


def grade(amb, passo=50, alcance=1200):
    foto = R.ler_foto(AMB, amb["id"])
    hh, ww = foto.shape[:2]
    out = foto.copy()
    mask = cv2.imread(str(AMB / f"{amb['id']}-mask.png"), cv2.IMREAD_GRAYSCALE)
    if mask is not None:
        sel = mask > 128
        out[sel] = (out[sel] * 0.6 + np.array([0, 0, 255]) * 0.4).astype(np.uint8)
    H = R.homografia(amb)
    L, P = amb["largura_cm"], amb["profundidade_cm"]

    def linha(p, q, cor, esp):
        pts = np.float32([p, q]).reshape(-1, 1, 2)
        # amostra a linha e só desenha os trechos à frente da câmera
        t = np.linspace(0, 1, 200)[:, None]
        seg = (1 - t) * np.float32(p) + t * np.float32(q)
        hom = np.c_[seg, np.ones(len(seg))] @ H.T
        ok = hom[:, 2] > 1e-6
        xy = hom[:, :2] / np.where(ok, hom[:, 2], 1)[:, None]
        xy = xy[ok]
        xy = xy[(np.abs(xy) < 5000).all(1)]
        if len(xy) > 1:
            cv2.polylines(out, [xy.astype(np.int32)], False, cor, esp, cv2.LINE_AA)

    for x in np.arange(-alcance, L + alcance + 1, passo):
        linha((x, -alcance), (x, P + alcance * 3), (0, 220, 0), 1)
    for y in np.arange(-alcance, P + alcance * 3 + 1, passo):
        linha((-alcance, y), (L + alcance, y), (0, 220, 0), 1)
    vx, vy = amb.get("camera", {}).get("pf", (None, None))
    if vx is not None:
        cv2.line(out, (0, int(vy)), (ww, int(vy)), (255, 0, 255), 1)
        cv2.circle(out, (int(vx), int(vy)), 6, (255, 0, 255), 2)
    return out


def main():
    ambientes = R.carregar_ambientes(AMB)
    nomes = sys.argv[1:] or list(ambientes)
    (AQUI / "build").mkdir(exist_ok=True)
    for n in nomes:
        img = grade(ambientes[n])
        cv2.imwrite(str(AQUI / "build" / f"grade-{n}.jpg"), img, [cv2.IMWRITE_JPEG_QUALITY, 85])
        print("ok", n)


if __name__ == "__main__":
    main()
