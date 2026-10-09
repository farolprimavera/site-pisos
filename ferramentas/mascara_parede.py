"""
Gera a máscara de parede (ambientes/<id>-mask.png: branco = recebe revestimento) a partir de ambientes/paredes.json:
  "mascara": {
    "poligono": [[x,y],...]          a parede (o resto fica preto)
    "objetos":  [[x0,y0,x1,y1],...]  caixas com coisas na frente da parede (planta, frascos...): dentro delas, o que
                                      tiver cor diferente da parede na mesma altura fica de fora
    "limiar": 6                       diferença de cor (a*b* do Lab) para contar como objeto
    "limiar_luz": 25                  quanto mais escuro que a parede (L do Lab) conta como objeto (sombra suave não conta)
    "excluir":  [[[x,y],...]]         polígonos que nunca são parede (objetos da cor da parede, como um vaso claro)
  }
Rodar:  python ferramentas/mascara_parede.py [parede ...]
Depois confira com:  python ferramentas/ver_perspectiva.py <parede>
"""
import json, sys
from pathlib import Path
import cv2
import numpy as np

AQUI = Path(__file__).resolve().parent
AMB = AQUI.parent / "ambientes"
sys.path.insert(0, str(AQUI))
import render as R


def carregar_paredes():
    return json.loads((AMB / "paredes.json").read_text(encoding="utf-8"))


def poli(p):
    return np.array(p, np.int32)


def gerar(par):
    cfg = par["mascara"]
    im = R.ler_foto(AMB, par["ambiente"])
    h, w = im.shape[:2]
    m = np.zeros((h, w), np.uint8)
    cv2.fillPoly(m, [poli(cfg["poligono"])], 1)
    lab = cv2.cvtColor(im, cv2.COLOR_BGR2LAB).astype(np.float32)
    for x0, y0, x1, y1 in cfg.get("objetos", []):
        # cor da parede em cada linha: mediana da parede fora da caixa
        fora = m.copy()
        fora[y0:y1, x0:x1] = 0
        ref = np.zeros((y1 - y0, 3), np.float32)
        for i, y in enumerate(range(y0, y1)):
            xs = np.nonzero(fora[y])[0]
            ref[i] = np.median(lab[y, xs], axis=0) if len(xs) else lab[y, x0]
        dif = lab[y0:y1, x0:x1] - ref[:, None]
        # objeto = cor diferente da parede, ou bem mais escuro/claro; sombra suave na parede (só um pouco mais
        # escura, mesma cor) continua sendo parede e recebe o revestimento
        cor = np.sqrt((dif[..., 1:] ** 2).sum(-1))
        # só o que é mais escuro conta: o contorno claro que a IA desenha em volta das folhas fica na parede,
        # assim o revestimento cobre esse halo em vez de deixá-lo aparecendo
        o = ((cor > cfg.get("limiar", 6)) | (dif[..., 0] < -cfg.get("limiar_luz", 25))).astype(np.uint8)
        o = cv2.morphologyEx(o, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
        o = cv2.morphologyEx(o, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
        o = cv2.erode(o, np.ones((3, 3), np.uint8))       # encolhe 1 px: o revestimento cobre a borda acinzentada
        m[y0:y1, x0:x1][o > 0] = 0
    for e in cfg.get("excluir", []):
        cv2.fillPoly(m, [poli(e)], 0)
    # borda suave de ~1 px para não serrilhar
    a = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 0.7)
    out = np.clip(a * 255, 0, 255).astype(np.uint8)
    cv2.imwrite(str(AMB / f"{par['id']}-mask.png"), out)
    return out


def main():
    paredes = carregar_paredes()
    for n in sys.argv[1:] or list(paredes):
        c = gerar(paredes[n])
        print(n, f"{(c > 128).mean() * 100:.0f}% da foto é parede")


if __name__ == "__main__":
    main()
