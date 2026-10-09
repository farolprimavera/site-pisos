"""
Monta dados/pisos.json — o catálogo que o site lê.

Lê da pasta de cima (a pasta de trabalho, fora do git):
  pisos.xlsx                      Código | Produto | Observação (caixa)
  <fabricante>/<fabricante>.pdf   tabela de preço do sistema (alfagres/alfagres.pdf, cedasa/cedasa.pdf, rochaforte/rochaforte.pdf)
  fotos/<código>.jpg              foto da peça
e daqui:
  ferramentas/fichas.csv          local de uso, acabamento e estilo de cada piso (preenchido a partir dos folders/sites)

Só entra no site o que tem estoque e foto.  Rodar:  python3 ferramentas/montar_dados.py
"""
import csv, json, re, sys, datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
SITE = AQUI.parent
TRABALHO = SITE.parent
sys.path.insert(0, str(AQUI))
import comum as C

FABRICANTES = {"ALFAGRES": "Alfagrês", "CEDASA": "Cedasa", "ROCHAFORTE": "Rocha"}
ORDEM_LU = ["LA", "LB", "LC", "LD", "LE", "LF"]

# Onde usar (filtro do site).  Cada local pede um local de uso mínimo.
LOCAIS = [
    ("quarto", "Quarto e sala", "LB"),
    ("cozinha", "Cozinha, banheiro e corredor", "LC"),
    ("coberta", "Varanda, área de serviço e garagem coberta", "LD"),
    ("externa", "Área externa e quintal", None),   # só se o fabricante indica uso externo
    ("parede", "Paredes", None),
]
# Ambientes renderizados e quais pisos fazem sentido em cada um: seção "regra" de ambientes/ambientes.json
#   minimo          local de uso mínimo (LB, LC, LD...)
#   so_externo      só pisos que o fabricante libera para área externa
#   sem_acabamento  acabamentos que não combinam (ex.: Polido no banheiro, Rústico na sala)
#   sem_estilo      estilos que não combinam
AMBIENTES = json.loads((SITE / "ambientes" / "ambientes.json").read_text(encoding="utf-8"))


def ambientes_do_piso(lu, externo, acabamento, estilo):
    out = []
    for a, cfg in AMBIENTES.items():
        r = cfg.get("regra", {})
        if not lu_ok(lu, r.get("minimo", "LB")):
            continue
        if r.get("so_externo") and not externo:
            continue
        if acabamento in r.get("sem_acabamento", []) or estilo in r.get("sem_estilo", []):
            continue
        out.append(a)
    return out

NOMES = {"IMENT CARRARA BRANCO": "Carrara Branco", "380 007": "380.007", "HD ARIZONA BROWN": "Arizon Brown",
         "HD ARIZON SAND": "Arizon Sand"}


def nome_exibicao(base):
    if base in NOMES:
        return NOMES[base]
    n = re.sub(r"\bARBE\b", "", base).strip()
    pal = []
    for w in n.split():
        pal.append(w if re.search(r"\d", w) or w in ("HD",) else w.capitalize())
    s = " ".join(pal)
    return s.replace("Sao Tome", "São Tomé").replace("Lactea", "Láctea").replace("Calcario", "Calcário") \
            .replace("Calcis", "Cálcis").replace("Rustico", "Rústico").replace("Rusti", "Rústico").replace("Ipe ", "Ipê ")


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", C.sem_acento(s.lower())).strip("-")


def fmt_medida(m):
    a, b = sorted(m)
    f = lambda v: (f"{v:.2f}".rstrip("0").rstrip(".")).replace(".", ",")
    return f"{f(a)} × {f(b)} cm"


def lu_ok(lu, minimo):
    return lu in ORDEM_LU and ORDEM_LU.index(lu) >= ORDEM_LU.index(minimo) and lu != "LA"


def main():
    fichas = {r["chave"]: r for r in csv.DictReader(open(AQUI / "fichas.csv", encoding="utf-8"), delimiter=";")}
    precos = {}
    for pasta in ("alfagres", "cedasa", "rochaforte"):
        pdf = TRABALHO / pasta / f"{pasta}.pdf"
        if pdf.exists():
            precos.update(C.ler_pdf_precos(pdf, pasta.upper()))
    planilha = C.ler_planilha(TRABALHO / "pisos.xlsx")
    fotos = TRABALHO / "fotos"

    grupos = {}
    for l in planilha:
        cod = str(l["Código"]).strip()
        pr = precos.get(cod)
        if not pr:
            continue
        k = C.chave(l["Produto"], pr["fabricante"])
        g = grupos.setdefault(k, {"lotes": [], "produto": l["Produto"], "obs": l.get("Observação")})
        g["lotes"].append(dict(codigo=cod, **pr, foto=(fotos / f"{cod}.jpg").exists()))

    itens, sem_ficha, sem_foto, supostos, revest_no_chao = [], [], [], [], []
    for k, g in grupos.items():
        lotes = g["lotes"]
        est = sum(max(x["estoque"] or 0, 0) for x in lotes)
        if est <= 0:
            continue
        fab, base, _ = k.split("|")
        f = fichas.get(k)
        com_foto = [x for x in sorted(lotes, key=lambda x: -(x["estoque"] or 0)) if x["foto"]]
        if not com_foto:
            sem_foto.append(k); continue
        if not f:
            sem_ficha.append(k); continue
        if f["fonte"].startswith("SUPOSTO"):
            supostos.append(k)
        com_preco = [x for x in lotes if x["vista"] and (x["estoque"] or 0) > 0] or [x for x in lotes if x["vista"]]
        principal = max(com_preco, key=lambda x: (x["estoque"] or 0)) if com_preco else None
        ofertas = [x["oferta"] for x in lotes if x["oferta"] and (x["estoque"] or 0) > 0]
        m = C.medida(g["produto"])
        m2, pcs = C.caixa(g["obs"])
        lu = f["local_uso"]
        # a loja cadastra revestimento como "REVEST..."; se a ficha disser que vai no chão, algo está errado
        if str(g["produto"]).upper().startswith("REVEST") and lu != "LA":
            revest_no_chao.append(k)
        externo = f["externo"] == "1"
        parede = f["parede"] == "1" or lu == "LA"
        onde = [c for c, _, mn in LOCAIS if mn and lu_ok(lu, mn)]
        if externo: onde.append("externa")
        if parede: onde.append("parede")
        ambientes = ambientes_do_piso(lu, externo, f["acabamento"], f["estilo"])
        nome = nome_exibicao(base)
        retificado = bool(re.search(r"\b(RET|RT)\b|RET\b", str(g["produto"]).upper()))
        itens.append(dict(
            id=slug(f"{fab}-{nome}-{int(round(max(m)))}"),
            chave=k, nome=nome, fabricante=FABRICANTES[fab],
            tipo="Revestimento" if lu == "LA" else "Piso",
            medida=fmt_medida(m), medida_cm=m, formato=f"{round(min(m))}x{round(max(m))}",
            caixa_m2=m2, caixa_pecas=pcs,
            vista=principal["vista"] if principal else None,
            prazo=principal["prazo"] if principal else None,
            oferta=min(ofertas) if ofertas else None,
            local_uso=lu, onde=onde, acabamento=f["acabamento"], estilo=f["estilo"], retificado=retificado,
            foto=com_foto[0]["codigo"], codigos=[x["codigo"] for x in lotes],
            ambientes=ambientes,
        ))

    itens.sort(key=lambda x: (x["fabricante"], x["nome"]))
    ids = {}
    for it in itens:                               # ids únicos
        n = ids.get(it["id"], 0); ids[it["id"]] = n + 1
        if n: it["id"] += f"-{n + 1}"
    datas = [C.data_pdf(TRABALHO / p / f"{p}.pdf") for p in ("alfagres", "cedasa", "rochaforte")
             if (TRABALHO / p / f"{p}.pdf").exists()]
    datas = sorted((d for d in datas if d), key=lambda d: d[6:] + d[3:5] + d[:2])
    saida = dict(atualizado=datas[0] if datas else datetime.date.today().strftime("%d/%m/%Y"),
                 locais=[dict(id=c, nome=n) for c, n, _ in LOCAIS],
                 ambientes=[dict(id=a, nome=v["nome"]) for a, v in AMBIENTES.items()], pisos=itens)
    (SITE / "dados").mkdir(exist_ok=True)
    txt = json.dumps(saida, ensure_ascii=False, separators=(",", ":"))
    (SITE / "dados" / "pisos.json").write_text(txt, encoding="utf-8")
    # cópia em .js: deixa abrir o index.html direto do computador (dois cliques), sem servidor
    (SITE / "dados" / "pisos.js").write_text("window.PISOS=" + txt + ";\n", encoding="utf-8")
    rel = [f"{len(itens)} produtos no site ({sum(1 for i in itens if i['tipo']=='Piso')} pisos, "
           f"{sum(1 for i in itens if i['tipo']!='Piso')} revestimentos de parede)",
           f"Fora do site por falta de foto ({len(sem_foto)}): " + ", ".join(sem_foto),
           f"Fora do site por falta de ficha técnica em fichas.csv ({len(sem_ficha)}): " + ", ".join(sem_ficha),
           f"Local de uso SUPOSTO, conferir ({len(supostos)}): " + ", ".join(supostos),
           f"Cadastrado como REVEST. na loja, mas a ficha não é LA, conferir ({len(revest_no_chao)}): "
           + ", ".join(revest_no_chao)]
    (SITE / "ferramentas" / "relatorio.txt").write_text("\n\n".join(rel), encoding="utf-8")
    print("\n\n".join(rel))


if __name__ == "__main__":
    main()
