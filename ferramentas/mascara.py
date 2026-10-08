"""
Gera a máscara do chão (ambientes/<id>-mask.png: branco = chão) a partir da seção "mascara" do ambientes.json:
  "mascara": {
    "poligono": [[x,y],...]      região onde pode haver chão (o resto fica preto)
    "excluir":  [[[x,y],...]]    polígonos que nunca são chão (pés de móveis, tapete, degrau...)
    "incluir":  [[[x,y],...]]    polígonos que são chão com certeza (corrige buracos)
    "sementes": [[x,y],...]      pontos de chão de onde a região cresce (padrão: fileira no pé da foto)
    "dif": 2.5                    diferença de cor aceita entre vizinhos (maior = vaza mais)
    "canny": 40                   sensibilidade das bordas que bloqueiam o crescimento (menor = mais bordas)
  }
Rodar:  python ferramentas/mascara.py [ambiente ...]
Depois confira com ver_perspectiva.py (a máscara aparece em vermelho) e retoque à mão se precisar.
"""
import json, sys
from pathlib import Path
import cv2
import numpy as np

AQUI = Path(__file__).resolve().parent
AMB = AQUI.parent / "ambientes"
sys.path.insert(0, str(AQUI))
import render as R


def poli(p):
    return np.array(p, np.int32)


def gerar(amb):
    cfg = amb["mascara"]
    im = R.ler_foto(AMB, amb["id"])
    h, w = im.shape[:2]
    P = np.zeros((h, w), np.uint8)
    cv2.fillPoly(P, [poli(cfg["poligono"])], 1)
    for e in cfg.get("excluir", []):
        cv2.fillPoly(P, [poli(e)], 0)
    # cresce a região a partir de sementes na parte de baixo da foto: o chão muda de tom aos poucos
    # (passa), a borda de um móvel muda de uma vez (para).
    b = cv2.bilateralFilter(im, 9, 20, 5)
    b = cv2.GaussianBlur(b, (0, 0), cfg.get("suave", 1.5))
    dif = cfg.get("dif", 2.5)
    barreira = np.ones((h + 2, w + 2), np.uint8)
    barreira[1:-1, 1:-1] = 1 - P
    # bordas fortes também são barreira (pés finos de móveis, rodapés)
    bordas = cv2.Canny(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY), cfg.get("canny", 40), cfg.get("canny", 40) * 2.5)
    bordas = cv2.dilate(bordas, np.ones((2, 2), np.uint8)) > 0
    barreira[1:-1, 1:-1][bordas] = 1
    sementes = cfg.get("sementes") or [[x, h - 8] for x in range(40, w, 120)]
    for x, y in sementes:
        if barreira[y + 1, x + 1] == 0:
            cv2.floodFill(b, barreira, (x, y), 0, (dif,) * 3, (dif,) * 3,
                          4 | cv2.FLOODFILL_MASK_ONLY | (2 << 8))
    c = (barreira[1:-1, 1:-1] == 2).astype(np.uint8)
    c = cv2.dilate(c, np.ones((3, 3), np.uint8)) & P   # devolve a linha de borda do Canny
    # nunca é chão: cor fora do cinza do piso (madeira, tecido colorido) ou quase preto (pés de metal)
    lab = cv2.cvtColor(im, cv2.COLOR_BGR2LAB).astype(np.float32)
    ref = np.median(lab[c > 0], axis=0)
    fora = np.sqrt(((lab[..., 1:] - ref[1:]) ** 2).sum(-1)) > cfg.get("tol_cor", 20)
    fora |= lab[..., 0] < cfg.get("preto", 70)
    fora = cv2.dilate(fora.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    c[fora] = 0
    c = cv2.morphologyEx(c, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    # fica só com as partes ligadas ao chão principal (as grandes)
    k, lb, st, _ = cv2.connectedComponentsWithStats(c, connectivity=4)
    keep = [i for i in range(1, k) if st[i, 4] > cfg.get("min_area", 1500)]
    c = np.isin(lb, keep).astype(np.uint8)
    # tapa buracos pequenos (manchas, reflexos)
    inv = (1 - c).astype(np.uint8)
    k2, lb2, st2, _ = cv2.connectedComponentsWithStats(inv, connectivity=4)
    for i in range(1, k2):
        if st2[i, 4] < cfg.get("buraco", 600):
            c[lb2 == i] = 1
    c = cv2.morphologyEx(c, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    for e in cfg.get("incluir", []):
        cv2.fillPoly(c, [poli(e)], 1)
    c &= P
    # encolhe 1 px para não pintar a borda dos móveis
    c = cv2.erode(c, np.ones((3, 3), np.uint8))
    cv2.imwrite(str(AMB / f"{amb['id']}-mask.png"), c * 255)
    return c


def main():
    ambientes = R.carregar_ambientes(AMB)
    for n in sys.argv[1:] or list(ambientes):
        if "mascara" in ambientes[n]:
            c = gerar(ambientes[n])
            print(n, f"{c.mean() * 100:.0f}% da foto é chão")


if __name__ == "__main__":
    main()
