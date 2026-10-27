"""
Monta dados/pisos.json — o catálogo que o site lê.

Lê da pasta de cima (a pasta de trabalho, fora do git):
  pisos.xlsx                      Código | Produto | Observação (caixa)
  pisos.pdf                       tabela de preço do sistema com todos os fabricantes (também vale dentro de site-pisos/)
  <fabricante>/<fabricante>.pdf   formato antigo, um PDF por fabricante (alfagres/alfagres.pdf, cedasa/cedasa.pdf, ...)
  fotos/<código>.jpg              foto da peça
e daqui:
  ferramentas/fichas.csv          local de uso, acabamento, estilo e retificado de cada piso (preenchido a partir dos folders/sites)

Os preços lidos do pisos.pdf ficam guardados em ferramentas/precos.json, então o PDF pode ser apagado depois.
Vale a fonte com a data mais recente (pisos.pdf > precos.json > PDFs por fabricante).

Só entra no site o que tem estoque e foto. Lote de ponta ('(P)' no fim do nome) fica de fora.
Lote em queima (preço à vista ou oferta igual a um dos PRECOS_QUEIMA, hoje R$ 9,90) também fica de fora;
se todos os lotes de um piso estão em queima, o piso some do site.
Novidades: ferramentas/estreias.json guarda o dia em que cada piso entrou no site pela primeira vez
(piso novo ganha a data do dia em que o script roda). O site mostra o selo "Novidade" por 30 dias.
Rodar:  python3 ferramentas/montar_dados.py
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
# Preços de queima: lote com preço à vista ou oferta igual a um destes não vai para o site.
# (A foto do lote, como a das pontas, ainda pode ser usada pelos outros lotes do mesmo piso.)  Para desligar: PRECOS_QUEIMA = []
PRECOS_QUEIMA = [9.90]


def em_queima(pr):
    return any(v is not None and abs(v - q) < 0.005 for q in PRECOS_QUEIMA for v in (pr.get("vista"), pr.get("oferta")))

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
# Paredes com simulação de revestimento (ambientes/paredes.json). Recebem todo produto que vai na parede
# (revestimento LA ou piso com parede = 1); as marcadas "so_externo" (fachada), só os liberados para área externa.
PAREDES = json.loads((SITE / "ambientes" / "paredes.json").read_text(encoding="utf-8"))


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


def data_iso(d):
    return d[6:] + d[3:5] + d[:2] if d else ""


def carregar_precos():
    """Preços da fonte mais recente.  O pisos.pdf (todos os fabricantes) é guardado em ferramentas/precos.json."""
    cache = AQUI / "precos.json"
    for pdf in (SITE / "pisos.pdf", TRABALHO / "pisos.pdf"):
        if pdf.exists():
            d = dict(data=C.data_pdf(pdf), precos=C.ler_pdf_geral(pdf))
            cache.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"Preços lidos de {pdf} ({d['data']}) e guardados em {cache.name}")
            break
    else:
        d = json.loads(cache.read_text(encoding="utf-8")) if cache.exists() else dict(data=None, precos={})
    # formato antigo, um PDF por fabricante: só vale se for mais novo que o pisos.pdf
    pdfs = [TRABALHO / p / f"{p}.pdf" for p in ("alfagres", "cedasa", "rochaforte")]
    pdfs = [p for p in pdfs if p.exists()]
    datas = [x for x in (C.data_pdf(p) for p in pdfs) if x]
    if datas and data_iso(min(datas, key=data_iso)) > data_iso(d["data"]):
        precos = {}
        for p in pdfs:
            precos.update(C.ler_pdf_precos(p, p.stem.upper()))
        return precos, min(datas, key=data_iso)
    return d["precos"], d["data"]


def main():
    fichas = {r["chave"]: r for r in csv.DictReader(open(AQUI / "fichas.csv", encoding="utf-8"), delimiter=";")}
    precos, data_precos = carregar_precos()
    planilha = {str(l["Código"]).strip(): l for l in C.ler_planilha(TRABALHO / "pisos.xlsx")}
    fotos = TRABALHO / "fotos"

    grupos, queima = {}, set()
    # lote novo que ainda não está na planilha entra com o nome do PDF (a caixa vem dos outros lotes do grupo)
    for cod in list(planilha) + [c for c in precos if c not in planilha]:
        pr = precos.get(cod)
        if not pr or pr["fabricante"] not in FABRICANTES:
            continue
        l = planilha.get(cod) or {"Produto": pr["produto"]}
        k = C.chave(l["Produto"], pr["fabricante"])
        g = grupos.setdefault(k, {"lotes": [], "fotos_extra": [], "produto": l["Produto"], "obs": None, "todos": []})
        g["todos"].append(cod)   # todo código do piso (inclusive ponta, queima e lote zerado): QR da etiqueta
        g["obs"] = g["obs"] or l.get("Observação")
        ponta = pr.get("ponta") or C.RE_PONTA.search(str(pr.get("produto") or l["Produto"]))
        if ponta or em_queima(pr):
            # ponta de estoque ou queima (R$ 9,90): não vai para o site, mas empresta a foto
            # para os outros lotes do mesmo piso (lote novo costuma chegar sem foto)
            if not ponta:
                queima.add(k)
            if (fotos / f"{cod}.jpg").exists():
                g["fotos_extra"].append((pr["estoque"] or 0, cod))
            continue
        g["lotes"].append(dict(codigo=cod, estoque=pr["estoque"], vista=pr["vista"], prazo=pr["prazo"],
                               oferta=pr["oferta"], foto=(fotos / f"{cod}.jpg").exists()))

    itens, sem_ficha, sem_foto, supostos, revest_no_chao = [], [], [], [], []
    so_queima = []
    for k, g in grupos.items():
        lotes = g["lotes"]
        est = sum(max(x["estoque"] or 0, 0) for x in lotes)
        if est <= 0:
            if k in queima:
                so_queima.append(k)
            continue
        fab, base, _ = k.split("|")
        f = fichas.get(k)
        com_foto = [x["codigo"] for x in sorted(lotes, key=lambda x: -(x["estoque"] or 0)) if x["foto"]] \
            + [c for _, c in sorted(g["fotos_extra"], key=lambda t: -t[0])]
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
        # a coluna "retificado" da ficha manda quando preenchida (1 = sim, 0 = não): nem todo retificado tem RET no nome
        if (f.get("retificado") or "").strip() in ("0", "1"):
            retificado = f["retificado"].strip() == "1"
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
            foto=com_foto[0], codigos=[x["codigo"] for x in sorted(lotes, key=lambda x: -(x["estoque"] or 0))
                                                   if (x["estoque"] or 0) > 0],
            outros_codigos=[],
            ambientes=ambientes,
            paredes=[par["ambiente"] for par in PAREDES.values()
                     if parede and (externo or not par.get("so_externo"))],
        ))

    # outros_codigos: lotes que não aparecem no site (ponta, queima, zerado). O QR da etiqueta (#código) acha o piso por eles.
    for it in itens:
        it["outros_codigos"] = sorted(c for c in grupos[it["chave"]]["todos"] if c not in it["codigos"])
        if not it["outros_codigos"]:
            del it["outros_codigos"]
    itens.sort(key=lambda x: (x["fabricante"], x["nome"]))
    ids = {}
    for it in itens:                               # ids únicos
        n = ids.get(it["id"], 0); ids[it["id"]] = n + 1
        if n: it["id"] += f"-{n + 1}"
    # Novidades: dia em que cada piso apareceu no site pela 1ª vez (o site mostra o selo por 30 dias).
    # Piso que sai do site (sem estoque) e volta depois mantém a data antiga: não vira novidade de novo.
    arq_estreias = AQUI / "estreias.json"
    estreias = json.loads(arq_estreias.read_text(encoding="utf-8")) if arq_estreias.exists() else {}
    hoje = datetime.date.today().isoformat()
    estrearam = []
    for it in itens:
        if it["chave"] not in estreias:
            estreias[it["chave"]] = hoje
            estrearam.append(it["chave"])
        it["novo_desde"] = estreias[it["chave"]]
    arq_estreias.write_text(json.dumps(dict(sorted(estreias.items())), ensure_ascii=False, indent=1) + "\n",
                            encoding="utf-8")
    saida = dict(atualizado=data_precos or datetime.date.today().strftime("%d/%m/%Y"),
                 locais=[dict(id=c, nome=n) for c, n, _ in LOCAIS],
                 ambientes=[dict(id=a, nome=v["nome"]) for a, v in AMBIENTES.items()],
                 paredes=[dict(id=par["ambiente"], nome=par["nome"]) for par in PAREDES.values()], pisos=itens)
    (SITE / "dados").mkdir(exist_ok=True)
    txt = json.dumps(saida, ensure_ascii=False, separators=(",", ":"))
    (SITE / "dados" / "pisos.json").write_text(txt, encoding="utf-8")
    # cópia em .js: deixa abrir o index.html direto do computador (dois cliques), sem servidor
    (SITE / "dados" / "pisos.js").write_text("window.PISOS=" + txt + ";\n", encoding="utf-8")
    rel = [f"{len(itens)} produtos no site ({sum(1 for i in itens if i['tipo']=='Piso')} pisos, "
           f"{sum(1 for i in itens if i['tipo']!='Piso')} revestimentos de parede)",
           f"Entraram no site agora, com selo Novidade por 30 dias ({len(estrearam)}): " + ", ".join(estrearam),
           f"Fora do site por falta de foto ({len(sem_foto)}): " + ", ".join(sem_foto),
           f"Fora do site por falta de ficha técnica em fichas.csv ({len(sem_ficha)}): " + ", ".join(sem_ficha),
           f"Local de uso SUPOSTO, conferir ({len(supostos)}): " + ", ".join(supostos),
           f"Fora do site por estar só com lote em queima (R$ {', '.join(f'{q:.2f}'.replace('.', ',') for q in PRECOS_QUEIMA)}) "
           f"({len(so_queima)}): " + ", ".join(sorted(so_queima)),
           f"Cadastrado como REVEST. na loja, mas a ficha não é LA, conferir ({len(revest_no_chao)}): "
           + ", ".join(revest_no_chao)]
    (SITE / "ferramentas" / "relatorio.txt").write_text("\n\n".join(rel), encoding="utf-8")
    print("\n\n".join(rel))


if __name__ == "__main__":
    main()
