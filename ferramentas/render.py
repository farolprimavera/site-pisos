"""
Renderiza um piso num ambiente (sem navegador, só Python + OpenCV).

Cada ambiente tem: foto (ambientes/<id>.jpg ou .png), máscara do chão (ambientes/<id>-mask.png)
e uma "planta" do chão: 4 pontos na foto que correspondem a um retângulo real de L x P cm.
"""
import json, math
from pathlib import Path
import cv2
import numpy as np

AQUI = Path(__file__).resolve().parent


def ler_foto(pasta, id_):
    """Foto do ambiente: <id>.jpg ou <id>.png."""
    for ext in (".jpg", ".png"):
        f = Path(pasta) / f"{id_}{ext}"
        if f.exists():
            return cv2.imread(str(f))
    raise FileNotFoundError(f"foto do ambiente '{id_}' não encontrada em {pasta}")


def arquivo_foto(pasta, id_):
    return next(Path(pasta) / f"{id_}{e}" for e in (".jpg", ".png") if (Path(pasta) / f"{id_}{e}").exists())


def carregar_ambientes(pasta):
    return json.loads((Path(pasta) / "ambientes.json").read_text(encoding="utf-8"))


def homografia(amb):
    L, P = amb["largura_cm"], amb.get("profundidade_cm", amb.get("altura_cm"))
    # chão:   fundo-esq, fundo-dir, frente-dir, frente-esq      <->  (0,P) (L,P) (L,0) (0,0)
    # parede: sup-esq, sup-dir, inf-dir, inf-esq (P = altura)   <->  o mesmo; y em cm sobe a partir do chão
    src = np.float32([[0, P], [L, P], [L, 0], [0, 0]])
    dst = np.float32(amb["pontos"])
    return cv2.getPerspectiveTransform(src, dst)       # cm -> px


def aparar_bordas(img, limite=40, maximo=0.03):
    """Tira faixas de borda (preta ou de fundo) que destoam do meio da peça; elas viravam um 'rejunte' falso."""
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    h, w = g.shape
    med = float(np.median(g[h // 4: 3 * h // 4, w // 4: 3 * w // 4]))
    t, b, l, r = 0, h, 0, w
    borda = lambda v: abs(v - med) > limite and (v < 40 or v > 245)     # só faixa quase preta ou quase branca
    while t < h * maximo and borda(g[t, l:r].mean()): t += 1
    while h - b < h * maximo and borda(g[b - 1, l:r].mean()): b -= 1
    while l < w * maximo and borda(g[t:b, l].mean()): l += 1
    while w - r < w * maximo and borda(g[t:b, r - 1].mean()): r -= 1
    return img[t:b, l:r]


def preparar_peca(img_bgr, medida_cm):
    """Recorta a foto da peça na proporção da medida (lado comprido da foto = lado comprido da peça)."""
    img_bgr = aparar_bordas(img_bgr)
    ih, iw = img_bgr.shape[:2]
    a, b = medida_cm
    maior, menor = max(a, b), min(a, b)
    cw, ch = (maior, menor) if iw >= ih else (menor, maior)
    alvo, atual = cw / ch, iw / ih
    x0, y0, w, h = 0, 0, iw, ih
    if abs(atual / alvo - 1) > 0.04:
        if atual > alvo:
            w = int(round(ih * alvo)); x0 = (iw - w) // 2
        else:
            h = int(round(iw / alvo)); y0 = (ih - h) // 2
    return img_bgr[y0:y0 + h, x0:x0 + w], (cw, ch)


def textura_plana(peca, peca_cm, area_cm, ppc, rejunte_mm, cor_rejunte, layout, seed=7):
    """Monta o chão 'visto de cima' (em pixels = cm*ppc) com rejunte e paginação."""
    (x0, y0, x1, y1) = area_cm
    W, H = int((x1 - x0) * ppc), int((y1 - y0) * ppc)
    out = np.empty((H, W, 3), np.float32)
    out[:] = cor_rejunte
    pw, ph = peca_cm
    g = rejunte_mm / 10.0
    tw, th = max(1, int(round(pw * ppc))), max(1, int(round(ph * ppc)))
    base = cv2.resize(peca, (tw, th), interpolation=cv2.INTER_AREA if peca.shape[1] > tw else cv2.INTER_CUBIC).astype(np.float32)
    rot = base[::-1, ::-1]
    rng = np.random.default_rng(seed)
    passo_x, passo_y = pw + g, ph + g
    j0 = math.floor(y0 / passo_y) - 1
    j1 = math.ceil(y1 / passo_y) + 1
    for j in range(j0, j1):
        desl = {"reto": 0.0, "amarracao": 0.5 * (j % 2), "amarracao3": (j % 3) / 3.0}[layout]
        i0 = math.floor(x0 / passo_x - desl) - 1
        i1 = math.ceil(x1 / passo_x - desl) + 1
        for i in range(i0, i1):
            cx = (i + desl) * passo_x + g / 2
            cy = j * passo_y + g / 2
            px, py = int(round((cx - x0) * ppc)), int(round((cy - y0) * ppc))
            t = rot if rng.random() < 0.5 else base
            t = t * (0.975 + 0.05 * rng.random())
            # recorte na área
            ax0, ay0 = max(px, 0), max(py, 0)
            ax1, ay1 = min(px + tw, W), min(py + th, H)
            if ax1 <= ax0 or ay1 <= ay0:
                continue
            out[ay0:ay1, ax0:ax1] = t[ay0 - py:ay1 - py, ax0 - px:ax1 - px]
    return out


def parametros_parede(p):
    """Paginação e rejunte de um produto na parede (README-REVESTIMENTOS §5)."""
    a, b = p["medida_cm"]
    nome = p["nome"].upper()
    if any(k in nome for k in ("FILETADO", "MATTONE", "CANJIQUINHA", "TIJOLINHO")):
        layout = "amarracao"                    # meia peça
    elif max(a, b) / min(a, b) >= 3:
        layout = "amarracao3"                   # réguas de madeira: junta a prumo fica artificial
    else:
        layout = "reto"
    return dict(layout=layout,
                rejunte_mm=2.0 if p["retificado"] else 3.0,
                girar=p["estilo"] in ("Liso", "Mármore"),      # nunca em desenho com direção
                brilho=p["acabamento"] in ("Brilhante", "Polido"))


def textura_parede(peca, peca_cm, area_cm, ppc, rejunte_mm, cor_rejunte, layout, girar, seed=7):
    """Parede vista de frente (y em cm sobe a partir do chão; a linha 0 da imagem é o topo).
    A 1ª fiada começa inteira no chão e as colunas são centralizadas na largura da parede."""
    xmin, xmax, L, ytop = area_cm
    W, H = int((xmax - xmin) * ppc), int(ytop * ppc)
    out = np.empty((H, W, 3), np.float32)
    out[:] = cor_rejunte
    pw, ph = peca_cm
    g = rejunte_mm / 10.0
    tw, th = max(1, int(round(pw * ppc))), max(1, int(round(ph * ppc)))
    base = cv2.resize(peca, (tw, th), interpolation=cv2.INTER_AREA if peca.shape[1] > tw else cv2.INTER_CUBIC).astype(np.float32)
    rot = base[::-1, ::-1]
    rng = np.random.default_rng(seed)
    px_, py_ = pw + g, ph + g
    for j in range(int(ytop / py_) + 2):
        desl = {"reto": 0.0, "amarracao": 0.5 * (j % 2), "amarracao3": (j % 3) / 3.0}[layout]
        y_bot = j * py_
        for i in range(math.floor((xmin - L / 2) / px_ - desl) - 1, math.ceil((xmax - L / 2) / px_ - desl) + 1):
            x_esq = L / 2 + (i + desl) * px_ - pw / 2          # i = 0 é a peça do meio da parede
            c0, r0 = int(round((x_esq - xmin) * ppc)), int(round((ytop - y_bot - ph) * ppc))
            t = rot if girar and rng.random() < 0.5 else base
            t = t * (0.975 + 0.05 * rng.random())
            ax0, ay0, ax1, ay1 = max(c0, 0), max(r0, 0), min(c0 + tw, W), min(r0 + th, H)
            if ax1 > ax0 and ay1 > ay0:
                out[ay0:ay1, ax0:ax1] = t[ay0 - r0:ay1 - r0, ax0 - c0:ax1 - c0]
    return out


def renderizar_parede(par, pasta_amb, peca_bgr, medida_cm, rejunte_mm=2.0, layout="reto", girar=False,
                      brilho=False, sombra=0.5, ss=2):
    """Aplica um revestimento na parede descrita em ambientes/paredes.json."""
    foto = ler_foto(pasta_amb, par["ambiente"])
    mask = cv2.imread(str(Path(pasta_amb) / f"{par['id']}-mask.png"), cv2.IMREAD_GRAYSCALE)
    Hh, Ww = foto.shape[:2]
    peca, cm = preparar_peca(peca_bgr, medida_cm)
    if cm[0] < cm[1]:                                     # retangulares vão deitadas
        peca = cv2.rotate(peca, cv2.ROTATE_90_CLOCKWISE); cm = (cm[1], cm[0])
    cor_rejunte = peca.reshape(-1, 3).mean(0) * 0.85      # tom da peça, um pouco mais escuro
    L, A = par["largura_cm"], par["altura_cm"]
    ppc = par.get("ppc", 6)
    xmin, xmax, ytop = -30, L + 30, A + 30
    plano = textura_parede(peca, cm, (xmin, xmax, L, ytop), ppc, rejunte_mm, cor_rejunte.astype(np.float32),
                           layout, girar)
    plano = cv2.GaussianBlur(plano, (0, 0), 0.6)
    # plano(px) -> cm (y sobe) -> foto(px), com supersampling
    T = np.array([[1 / ppc, 0, xmin], [0, -1 / ppc, ytop], [0, 0, 1]])
    M = np.diag([ss, ss, 1.0]) @ homografia(par) @ T
    big = cv2.warpPerspective(plano, M, (Ww * ss, Hh * ss), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    rev = cv2.resize(big, (Ww, Hh), interpolation=cv2.INTER_AREA)
    # luz e sombra: luminância da própria parede (média só dos pixels de parede, para a planta e outros
    # objetos não "mancharem" o revestimento em volta deles); desfoque maior e efeito menor que no chão
    a = mask.astype(np.float32) / 255
    g = cv2.cvtColor(foto, cv2.COLOR_BGR2GRAY).astype(np.float32)
    sig = par.get("desfoque", 14)
    gb = cv2.GaussianBlur(g * a, (0, 0), sig) / np.maximum(cv2.GaussianBlur(a, (0, 0), sig), 1e-3)
    ref = np.percentile(gb[a > 0.5], 60)
    s = np.clip(1 + (gb / ref - 1) * sombra, 0.5, 1.2)[..., None]
    expo = float(np.clip(ref / 225, 0.6, 1.0))           # peça branca fica do branco da parede da foto
    rev = rev * expo * s
    if brilho:
        # reflexo suave e difuso da janela: faixa vertical clara, mais forte no meio da altura
        cx, larg = par.get("reflexo", [Ww * 0.45, Ww * 0.08])
        xs = np.arange(Ww, dtype=np.float32)
        ys = np.arange(Hh, dtype=np.float32)
        y0, y1 = par["pontos"][0][1], par["pontos"][2][1]
        faixa = np.exp(-((xs - cx) / larg) ** 2 / 2)[None, :] * np.clip(1 - np.abs((ys - (y0 + y1) / 2) / max(y1 - y0, 1)), 0, 1)[:, None]
        rev = rev + 255 * par.get("reflexo_forca", 0.06) * faixa[..., None]
    a = a[..., None]
    out = foto.astype(np.float32) * (1 - a) + rev * a
    return np.clip(out, 0, 255).astype(np.uint8)


def renderizar(amb, pasta_amb, peca_bgr, medida_cm, rejunte_mm=2.0, cor_rejunte=None,
               layout="reto", girar=False, sombra=0.8, largura_saida=None, ss=2, exposicao=0.9):
    foto = ler_foto(pasta_amb, amb["id"])
    mask = cv2.imread(str(Path(pasta_amb) / f"{amb['id']}-mask.png"), cv2.IMREAD_GRAYSCALE)
    Hh, Ww = foto.shape[:2]
    peca, cm = preparar_peca(peca_bgr, medida_cm)
    if girar:
        peca = cv2.rotate(peca, cv2.ROTATE_90_CLOCKWISE); cm = (cm[1], cm[0])
    if cor_rejunte is None:
        m = peca.reshape(-1, 3).mean(0)
        cor_rejunte = np.clip(m * 0.55 + 255 * 0.45, 0, 255) * 0.92        # rejunte claro, no tom da peça
    H = homografia(amb)                       # cm -> px
    Hi = np.linalg.inv(H)
    # área do chão em cm (pontos da máscara levados ao plano)
    ys, xs = np.nonzero(mask > 10)
    pts = np.stack([xs, ys, np.ones_like(xs)], 0).astype(np.float64)[:, ::50]
    q = Hi @ pts
    ok = q[2] > 0
    u, v = q[0][ok] / q[2][ok], q[1][ok] / q[2][ok]
    x0, x1 = np.percentile(u, 0.2) - 80, np.percentile(u, 99.8) + 80
    y0, y1 = np.percentile(v, 0.2) - 80, np.percentile(v, 99.8) + 80
    x0, x1 = max(x0, -1500), min(x1, amb["largura_cm"] + 1500)
    y0, y1 = max(y0, -800), min(y1, amb["profundidade_cm"] + 2500)
    # resolução do plano: o pixel mais "esticado" da foto pede ~ ppc px/cm
    ppc = amb.get("ppc", 6)
    plano = textura_plana(peca, cm, (x0, y0, x1, y1), ppc, rejunte_mm, np.array(cor_rejunte, np.float32), layout)
    # leve desfoque contra cintilação ao longe
    plano = cv2.GaussianBlur(plano, (0, 0), 0.6)
    # plano(px) -> cm -> foto(px), com supersampling
    S = np.diag([ss, ss, 1.0])
    T = np.array([[1 / ppc, 0, x0], [0, 1 / ppc, y0], [0, 0, 1]])
    M = S @ H @ T
    big = cv2.warpPerspective(plano, M, (Ww * ss, Hh * ss), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    piso = cv2.resize(big, (Ww, Hh), interpolation=cv2.INTER_AREA)
    # luz e sombra da foto original (desfocada para não "vazar" o piso antigo)
    g = cv2.cvtColor(foto, cv2.COLOR_BGR2GRAY).astype(np.float32)
    gb = cv2.GaussianBlur(g, (0, 0), 9)
    sel = mask > 128
    ref = np.percentile(gb[sel], 60)
    s = np.clip(1 + (gb / ref - 1) * sombra, 0.3, 1.3)[..., None]
    piso = piso * exposicao * np.minimum(s, 1.08) + np.maximum(s - 1.08, 0) * 60
    a = cv2.GaussianBlur(mask.astype(np.float32) / 255, (0, 0), 0.8)[..., None]
    out = foto.astype(np.float32) * (1 - a) + piso * a
    out = np.clip(out, 0, 255).astype(np.uint8)
    if largura_saida and largura_saida != Ww:
        out = cv2.resize(out, (largura_saida, int(Hh * largura_saida / Ww)), interpolation=cv2.INTER_AREA)
    return out
