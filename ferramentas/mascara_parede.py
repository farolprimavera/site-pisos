"""
Gera a máscara de parede (ambientes/<id>-mask.png: branco = recebe revestimento) a partir de ambientes/paredes.json:
  "mascara": {
    "poligono": [[x,y],...]          a parede (o resto fica preto)
    "objetos":  [[x0,y0,x1,y1],...]  caixas com coisas na frente da parede (planta, frascos...): dentro delas, o que
                                      tiver cor diferente da parede na mesma altura fica de fora.
                                      Ou {"caixa": [...], "claro": 12, "preencher": true}: "claro" também tira o que
                                      for mais claro que a parede (objeto branco); "preencher" tapa buracos do objeto
                                      (o que não se liga à borda da caixa vira objeto)
    "limiar": 6                       diferença de cor (a*b* do Lab) para contar como objeto
    "limiar_luz": 25                  quanto mais escuro que a parede (L do Lab) conta como objeto (sombra suave não conta)
    "excluir":  [[[x,y],...]]         polígonos que nunca são parede (objetos da cor da parede, como um vaso claro)
    "metodo": "grabcut"               recorta cada caixa de "objetos" com GrabCut em vez da diferença de cor; melhor
                                      quando a luz varia ao longo da parede ou o objeto é branco. A caixa deve
                                      sobrar um pouco em volta do objeto (a borda dela é tomada como parede)
                                      {"caixa": [...], "planta": true}: caixa só com planta/objetos escuros ou
                                      coloridos; ali todo trecho claro e pouco colorido volta a ser parede
    "claro_max": 14                   (grabcut) até quanto mais claro que a parede vizinha um trecho ainda volta a ser
                                      parede; suba onde há luz forte (LED) e nenhum objeto branco perto
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
    if cfg.get("metodo") == "grabcut":
        for obj in cfg.get("objetos", []):
            caixa = obj["caixa"] if isinstance(obj, dict) else obj
            planta = isinstance(obj, dict) and obj.get("planta", False)
            o = objeto_grabcut(im, lab, caixa, cfg.get("claro_max", 14), planta)
            x0, y0, x1, y1 = caixa
            m[y0:y1, x0:x1][o > 0] = 0
        return salvar(par, m, cfg)
    for obj in cfg.get("objetos", []):
        if isinstance(obj, dict):
            (x0, y0, x1, y1), claro, preencher = obj["caixa"], obj.get("claro"), obj.get("preencher", False)
        else:
            (x0, y0, x1, y1), claro, preencher = obj, None, False
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
        o = (cor > cfg.get("limiar", 6)) | (dif[..., 0] < -cfg.get("limiar_luz", 25))
        if claro is not None:                             # objeto branco na frente da parede (máquina, gabinete)
            o |= dif[..., 0] > claro
        o = o.astype(np.uint8)
        o = cv2.morphologyEx(o, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
        o = cv2.morphologyEx(o, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
        if preencher:                                     # tapa os buracos de dentro do objeto
            borda = np.zeros((o.shape[0] + 2, o.shape[1] + 2), np.uint8)
            fora = o.copy()
            hh, ww = o.shape
            for x, y in [(x, y) for x in range(ww) for y in (0, hh - 1)] + [(x, y) for y in range(hh) for x in (0, ww - 1)]:
                if fora[y, x] == 0:
                    cv2.floodFill(fora, borda, (x, y), 2)
            o = (fora != 2).astype(np.uint8)
        o = cv2.erode(o, np.ones((3, 3), np.uint8))       # encolhe 1 px: o revestimento cobre a borda acinzentada
        m[y0:y1, x0:x1][o > 0] = 0
    return salvar(par, m, cfg)


def objeto_grabcut(im, lab, caixa, claro_max=14, planta=False, it=6):
    """Separa o objeto da parede dentro da caixa com GrabCut: a borda da caixa ensina como é a parede (com as
    variações de luz), o miolo é provável objeto. Na borda, o que tiver cor forte ou for escuro (planta, cesto
    cortados pela caixa) continua como provável objeto. Objeto branco (máquina, gabinete) também funciona, pela
    diferença de brilho e pelas bordas nítidas."""
    x0, y0, x1, y1 = caixa
    crop = im[y0:y1, x0:x1].copy()
    l = lab[y0:y1, x0:x1]
    # escuro, ou colorido sem ser claro (a luz quente de um LED é amarelada, mas clara: continua sendo parede)
    croma = np.hypot(l[..., 1] - 128, l[..., 2] - 128)
    forte = ((croma > 18) & (l[..., 0] < 170)) | (l[..., 0] < 90)
    gm = np.full(crop.shape[:2], cv2.GC_PR_FGD, np.uint8)
    b = np.zeros_like(forte)
    b[:2, :] = b[-2:, :] = b[:, :2] = b[:, -2:] = True
    parede_borda = b & ~forte
    gm[parede_borda] = cv2.GC_BGD
    bg, fg = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    cv2.grabCut(crop, gm, None, bg, fg, it, cv2.GC_INIT_WITH_MASK)
    o = (gm == cv2.GC_FGD) | (gm == cv2.GC_PR_FGD)
    # o GrabCut às vezes leva junto bolsões de parede presos entre folhas: devolve à parede o que tiver cor e
    # brilho de parede naquela altura (referência: as laterais da caixa, que são parede)
    lados = np.zeros_like(b)
    lados[:, :2] = lados[:, -2:] = True
    lados &= ~forte
    ref = np.tile(np.median(l[parede_borda], axis=0) if parede_borda.any() else [200, 128, 128], (l.shape[0], 1))
    for y in range(l.shape[0]):
        ys = slice(max(y - 6, 0), y + 7)
        v = l[ys][lados[ys]]
        if len(v):
            ref[y] = np.median(v, axis=0)
    dl = l[..., 0] - ref[:, None, 0]
    dab = np.hypot(l[..., 1] - ref[:, None, 1], l[..., 2] - ref[:, None, 2])
    parecida = o & (dab < 7) & (dl > -25) & (dl < claro_max)      # objeto branco fica uns 20+ acima da parede
    # só os bolsões que encostam na parede (o vidro da porta da máquina, cercado por ela, continua objeto)
    k, lb = cv2.connectedComponents(parecida.astype(np.uint8), connectivity=8)
    parede = cv2.dilate((~o).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    encosta = np.unique(lb[parede & parecida])
    o = o & ~np.isin(lb, encosta[encosta > 0])
    if planta:
        # caixa só com planta (sem objeto branco): todo trecho claro e pouco colorido é parede, mesmo preso
        # entre as folhas ou sob a luz quente de um LED
        o &= ~((l[..., 0] > 150) & (croma < 35))
    o = o.astype(np.uint8)
    o = cv2.morphologyEx(o, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    o = cv2.erode(o, np.ones((3, 3), np.uint8))       # encolhe 1 px: o revestimento cobre a borda acinzentada
    return o


def salvar(par, m, cfg):
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
