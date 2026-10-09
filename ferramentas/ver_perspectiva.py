"""
Desenha a grade de 50 x 50 cm (e a máscara do chão, em vermelho) por cima da foto de cada ambiente,
para conferir a perspectiva antes de gerar tudo.  As linhas da grade devem "correr" junto com os
rodapés e a base dos móveis.

Paredes (ambientes/paredes.json): grade de 10 cm e a silhueta de uma peça 60 x 30 apoiada no chão.

Rodar:  python ferramentas/ver_perspectiva.py [ambiente ou parede ...]   ->  ferramentas/build/grade-<nome>.jpg
"""
import json, sys
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


def grade_parede(par, passo=10, peca=(60, 30)):
    """Parede: grade de 10 cm (mais forte a cada 50) e a silhueta de uma peça (60 x 30 deitada) apoiada no chão,
    centralizada, que é como a primeira fiada vai ser assentada."""
    foto = R.ler_foto(AMB, par["ambiente"])
    out = foto.copy()
    mask = cv2.imread(str(AMB / f"{par['id']}-mask.png"), cv2.IMREAD_GRAYSCALE)
    if mask is not None:
        a = (mask.astype(np.float32) / 255 * 0.35)[..., None]
        out = (out * (1 - a) + np.array([0, 0, 255]) * a).astype(np.uint8)
    H = R.homografia(par)
    L, A = par["largura_cm"], par["altura_cm"]

    def px(pts_cm):
        p = cv2.perspectiveTransform(np.float32(pts_cm).reshape(-1, 1, 2), H)
        return p.reshape(-1, 2).round().astype(np.int32)

    for x in np.arange(0, L + 0.1, passo):
        forte = x % 50 == 0
        cv2.polylines(out, [px([(x, 0), (x, A)])], False, (0, 200, 0), 2 if forte else 1, cv2.LINE_AA)
    for y in np.arange(0, A + 0.1, passo):
        forte = y % 50 == 0
        cv2.polylines(out, [px([(0, y), (L, y)])], False, (0, 200, 0), 2 if forte else 1, cv2.LINE_AA)
        if forte:
            cv2.putText(out, f"{int(y)}", tuple(px([(0, y)])[0] + (4, -4)), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                        (0, 120, 0), 1, cv2.LINE_AA)
    pw, ph = peca
    x0 = (L - pw) / 2
    cv2.polylines(out, [px([(x0, 0), (x0 + pw, 0), (x0 + pw, ph), (x0, ph)])], True, (0, 220, 255), 3, cv2.LINE_AA)
    return out


def main():
    ambientes = R.carregar_ambientes(AMB)
    paredes = json.loads((AMB / "paredes.json").read_text(encoding="utf-8")) if (AMB / "paredes.json").exists() else {}
    nomes = sys.argv[1:] or list(ambientes) + list(paredes)
    (AQUI / "build").mkdir(exist_ok=True)
    for n in nomes:
        img = grade_parede(paredes[n]) if n in paredes else grade(ambientes[n])
        cv2.imwrite(str(AQUI / "build" / f"grade-{n}.jpg"), img, [cv2.IMWRITE_JPEG_QUALITY, 85])
        print("ok", n)


if __name__ == "__main__":
    main()
