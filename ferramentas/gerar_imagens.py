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
FOTOS = SITE.parent / "fotos"
AMB = SITE / "ambientes"
OUT = SITE / "imagens"
VERSAO = "5"          # mude para forçar regerar tudo (ex.: depois de mexer no render.py)
VERSAO_PAREDE = "1"   # o mesmo, só para as paredes (não regera os chãos)
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
                rejunte_mm=1.5 if p["retificado"] else 3.0)


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
        h_foto = hashlib.md5(foto.read_bytes()).hexdigest()
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
            out = R.renderizar(ambientes[a], AMB, img, p["medida_cm"], **par)
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
            out = R.renderizar_parede(par, AMB, img, p["medida_cm"], **par_p)
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
