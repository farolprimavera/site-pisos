"""
Gera as imagens do site a partir de dados/pisos.json:
  imagens/<ambiente>/<id>.webp        simulação grande (1280 px)
  imagens/<ambiente>/mini/<id>.webp   miniatura da grade (520 px)
  imagens/pecas/<id>.webp             foto da peça
  imagens/<ambiente>/parede/<id>.webp        revestimento na parede (1280 px)
  imagens/<ambiente>/parede/mini/<id>.webp   miniatura recortada em volta da parede (520 px)

Só gera o que falta ou mudou (guarda uma "impressão digital" em imagens/controle.json).
Rodar depois do montar_dados.py:   python3 ferramentas/gerar_imagens.py
Para refazer tudo:                  python3 ferramentas/gerar_imagens.py --tudo
"""
import hashlib, json, sys
from pathlib import Path
import cv2

AQUI = Path(__file__).resolve().parent
SITE = AQUI.parent
sys.path.insert(0, str(AQUI))
import comum as C
FOTOS = C.pasta_trabalho(SITE) / "fotos"   # David/projeto-pisos/fotos
FACES = C.pasta_trabalho(SITE) / "faces"   # David/projeto-pisos/faces/<código>-1.jpg, -2.jpg... (da fabricante)
AMB = SITE / "ambientes"
OUT = SITE / "imagens"
VERSAO = "8"          # mude para forçar regerar tudo (ex.: depois de mexer no render.py)
VERSAO_PAREDE = "2"   # o mesmo, só para as paredes (não regera os chãos)
# Linha do rejunte desenhada com pelo menos 2,5 mm e um pouco mais escura que a peça: o rejunte real (1,5 mm)
# some na foto, e é ele que mostra o tamanho da peça. Era 4 mm até 26/11/2026 (ficava marcado demais).
# Para voltar ao jeito antigo: 0.
REJUNTE_VISIVEL_MM = 2.5
# Quadradas desses estilos também giram 90°/270° no chão; madeira e decorado têm direção, só giram 180°.
GIRA_90 = {"Mármore", "Pedra", "Cimento", "Liso"}
# Brilho/reflexo do chão por acabamento (janela, móveis e paredes refletidos, mais forte ao fundo).
REFLEXO = {"Polido": 0.55, "Brilhante": 0.4, "Acetinado": 0.15}
sys.path.insert(0, str(AQUI))
import render as R


def salvar_webp(img, caminho, largura, q=80):
    caminho.parent.mkdir(parents=True, exist_ok=True)
    h, w = img.shape[:2]
    if w != largura:
        img = cv2.resize(img, (largura, int(round(h * largura / w))), interpolation=cv2.INTER_AREA)
    cv2.imwrite(str(caminho), img, [cv2.IMWRITE_WEBP_QUALITY, q])


def parametros(p):
    a, b = p["medida_cm"]
    prancha = max(a, b) / min(a, b) >= 3
    return dict(layout="amarracao3" if prancha else "reto",
                rejunte_mm=1.5 if p["retificado"] else 3.0,
                rejunte_visivel_mm=REJUNTE_VISIVEL_MM,
                reflexo=REFLEXO.get(p.get("acabamento"), 0.0),
                girar90=abs(a - b) < 1 and p.get("estilo") in GIRA_90)


def numero_da_face(arq):
    try:
        return int(arq.stem.rsplit("-", 1)[1])
    except (IndexError, ValueError):
        return 999


def faces_do_piso(codigo):
    """Faces da fabricante (projeto-pisos/faces/<código>-N.jpg). Só valem com 2 ou mais."""
    arqs = sorted(FACES.glob(f"{codigo}-*.jpg"), key=numero_da_face)
    imgs = [(a, cv2.imread(str(a))) for a in arqs]
    imgs = [(a, i) for a, i in imgs if i is not None]
    return imgs if len(imgs) >= 2 else []


def main():
    tudo = "--tudo" in sys.argv
    dados = json.loads((SITE / "dados" / "pisos.json").read_text(encoding="utf-8"))
    ambientes = R.carregar_ambientes(AMB)
    # muda a assinatura se a foto, a máscara ou a perspectiva do ambiente mudar
    assin_amb = {a: hashlib.md5(R.arquivo_foto(AMB, a).read_bytes() + (AMB / f"{a}-mask.png").read_bytes()
                                + json.dumps(v, sort_keys=True).encode()).hexdigest() for a, v in ambientes.items()}
    paredes = {par["ambiente"]: par for par in json.loads((AMB / "paredes.json").read_text(encoding="utf-8")).values()}
    assin_par = {a: hashlib.md5(R.arquivo_foto(AMB, a).read_bytes() + (AMB / f"{par['id']}-mask.png").read_bytes()
                                + json.dumps(par, sort_keys=True).encode()).hexdigest() for a, par in paredes.items()}
    ctrl_arq = OUT / "controle.json"
    ctrl = {} if tudo or not ctrl_arq.exists() else json.loads(ctrl_arq.read_text())
    feitos = 0
    validos = set()
    for i, p in enumerate(dados["pisos"]):
        foto = FOTOS / f"{p['foto']}.jpg"
        img = cv2.imread(str(foto))
        if img is None:
            print("  sem foto:", p["id"]); continue
        faces = faces_do_piso(p["foto"])
        # a assinatura muda se a foto ou qualquer face mudar (face nova regera os ambientes do piso)
        h_foto = hashlib.md5(foto.read_bytes() + b"".join(a.read_bytes() for a, _ in faces)).hexdigest()
        faces = [i for _, i in faces] or None
        # peça
        chave = f"pecas/{p['id']}"; validos.add(chave)
        assin = f"{VERSAO}|{h_foto}|{p['medida_cm']}"
        if ctrl.get(chave) != assin or not (OUT / f"{chave}.webp").exists():
            peca, _ = R.preparar_peca(img, p["medida_cm"])
            salvar_webp(peca, OUT / f"{chave}.webp", min(600, peca.shape[1]), 82)
            ctrl[chave] = assin
        # ambientes
        par = parametros(p)
        for a in p["ambientes"]:
            chave = f"{a}/{p['id']}"; validos.add(chave)
            assin = f"{VERSAO}|{h_foto}|{p['medida_cm']}|{par}|{assin_amb[a]}"
            if ctrl.get(chave) == assin and (OUT / f"{chave}.webp").exists():
                continue
            out = R.renderizar(ambientes[a], AMB, img, p["medida_cm"], faces=faces, **par)
            salvar_webp(out, OUT / f"{chave}.webp", 1280, 80)
            salvar_webp(out, OUT / a / "mini" / f"{p['id']}.webp", 520, 76)
            ctrl[chave] = assin
            feitos += 1
        # paredes (revestimentos e pisos que também vão na parede)
        par_p = R.parametros_parede(p)
        for a in p.get("paredes", []):
            par = paredes[a]
            chave = f"{a}/parede/{p['id']}"; validos.add(chave)
            assin = f"{VERSAO_PAREDE}|{h_foto}|{p['medida_cm']}|{par_p}|{assin_par[a]}"
            if ctrl.get(chave) == assin and (OUT / f"{chave}.webp").exists():
                continue
            out = R.renderizar_parede(par, AMB, img, p["medida_cm"], faces=faces, **par_p)
            salvar_webp(out, OUT / f"{chave}.webp", 1280, 80)
            x0, y0, x1, y1 = par["recorte"]                # miniatura: só em volta da parede
            salvar_webp(out[y0:y1, x0:x1], OUT / a / "parede" / "mini" / f"{p['id']}.webp", 520, 76)
            ctrl[chave] = assin
            feitos += 1
        print(f"\r  {i + 1}/{len(dados['pisos'])}  ({feitos} imagens novas)", end="", flush=True)
    # apaga imagens de pisos que saíram do site (ou de um ambiente/parede)
    for k in list(ctrl):
        if k not in validos:
            grande = OUT / f"{k}.webp"
            for f in (grande, grande.parent / "mini" / grande.name):
                f.unlink(missing_ok=True)
            del ctrl[k]
    OUT.mkdir(exist_ok=True)
    ctrl_arq.write_text(json.dumps(ctrl, indent=0))
    print(f"\nPronto: {feitos} simulações geradas.")


if __name__ == "__main__":
    main()
