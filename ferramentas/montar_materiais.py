"""
Monta dados/materiais.json (+ .js) — argamassa, rejunte, espaçador, nivelador (clips) e cunha
da loja, com preço e estoque, para a calculadora do site (js/materiais.js).

Lê da pasta de trabalho (fora do git):
  materiais/*.pdf    tabela de preço do sistema (Pontual), ex.: grupo BASICO / CIMENTÍCIOS
  materiais/*.xls    exportação de produtos do sistema (colunas Código, Produto, Preço, Qtde.)
  materiais/*.xlsx   idem
Pode ter vários arquivos; o mesmo código em dois arquivos fica com o do arquivo mais novo.

Só entra o que o script reconhece pelo nome (regras em CLASSES abaixo). O que não reconhece
é ignorado; o que reconhece mas está sem estoque entra (o site esconde na hora de oferecer).

Rodar:  python3 ferramentas/montar_materiais.py
Dependência extra para .xls:  pip install --break-system-packages xlrd
"""
import collections, json, re, sys, datetime
from pathlib import Path

AQUI = Path(__file__).resolve().parent
SITE = AQUI.parent
TRABALHO = SITE.parent
PASTA = TRABALHO / "materiais"

# Produtos que o script NÃO oferece mesmo reconhecendo (decisão da loja / dúvida em aberto).
IGNORAR = [
    r"BLOCO VIDRO",          # argamassa de bloco de vidro
    r"PISO\s*X\s*PISO",      # piso sobre piso: uso especial
]
# Garramax Super 7x1 (garramax.com.br/produtos-18): uso interno e externo, porcelanato, fachada e piscina,
# mas sem classe AC no nome e com aderência > 0,5 MPa / tempo em aberto 15 min. Entra como "SUPER":
# opção para qualquer classe, nunca a sugestão principal da AC-III.
# Rejuntamento Construcola: embalagem de 1 kg (confirmado pelo David), mesmo sem "1KG" no nome.


def num_br(s):
    if s is None:
        return None
    s = str(s).strip().replace("R$", "").strip()
    if not s or s.lower() == "nan":
        return None
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def titulo(s):
    """'CIMENTCOLA VOTOMASSA ACIII CINZA 20KG' -> 'Cimentcola Votomassa AC-III Cinza 20 kg'"""
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r"\bAC\s*(III|II|I)\b", lambda m: "AC-" + m.group(1), s)
    s = re.sub(r"(\d)\s*KG\b", r"\1 kg", s, flags=re.I)
    s = re.sub(r"(\d)\s*MM\b", r"\1 mm", s, flags=re.I)
    s = re.sub(r"\s*\(?\s*(\d+)\s*(PÇ|PC|PCS|PECAS|PEÇAS)\s*\)?", r" (\1 peças)", s, flags=re.I)
    s = re.sub(r"\(\s*CLARO\s*\)\s*", "", s, flags=re.I)
    s = re.sub(r"\bCINZA PLAT\b", "CINZA PLATINA", s, flags=re.I)
    s = s.replace("ESPACADOR", "ESPAÇADOR")
    pal = []
    for w in s.split(" "):
        if re.match(r"^AC-|^\d|^\(|kg$|mm$", w) or w in ("P/", "BR", "CZ"):
            pal.append(w)
        else:
            pal.append(w.capitalize())
    return " ".join(pal).replace("P/porcelanato", "p/ Porcelanato").replace("P/Porcelanato", "p/ Porcelanato")


# ---------------- leitura dos arquivos ----------------

def ler_pdf(pdf):
    """Tabela de preço do Pontual. As colunas Produto e Fabricante se sobrepõem no PDF;
    o texto do produto vem primeiro no arquivo, então separa onde a posição x volta para trás."""
    import pdfplumber
    out, data = [], None
    with pdfplumber.open(pdf) as p:
        for pg in p.pages:
            txt = pg.extract_text() or ""
            m = re.search(r"Data:\s*(\d{2}/\d{2}/\d{4})", txt)
            data = data or (m and m.group(1))
            # posições das colunas pelo cabeçalho
            pal = {w["text"]: w for w in pg.extract_words()}
            if "Quant." not in pal:
                continue
            xq = pal["Quant."]["x0"] - 15
            xv = pal["VISTA"]["x0"] - 15
            xp = pal["PRAZO"]["x0"] - 15
            xo = pal["SUP.OFERTA"]["x0"] - 15
            linhas = collections.OrderedDict()
            for c in pg.chars:
                linhas.setdefault(round(c["top"]), []).append(c)
            for cs in linhas.values():
                cod = "".join(c["text"] for c in cs if c["x0"] < 58).strip()
                if not cod.isdigit():
                    continue
                meio = [c for c in cs if 58 <= c["x0"] < xq]
                trechos = [[]]
                for c in meio:
                    if trechos[-1] and c["x0"] < trechos[-1][-1]["x0"] - 3:
                        trechos.append([])
                    trechos[-1].append(c)
                produto = "".join(c["text"] for c in trechos[0]).strip()
                # quando o nome é curto, o fabricante vem colado no fim: "ACI 20KGGARRAMAX"
                produto = re.sub(r"\s*(DIVERSOS|VOTOMASSA|GARRAMAX|CONSTRUCOLA|PONTUAL)$", "", produto)
                col = lambda a, b: "".join(c["text"] for c in cs if a <= c["x0"] < b).strip()
                out.append(dict(codigo=cod, produto=produto, estoque=num_br(col(xq, xv)),
                                vista=num_br(col(xv, xp)), prazo=num_br(col(xp, xo)), oferta=num_br(col(xo, 9999))))
    return out, data


def ler_planilha(arq):
    import pandas as pd
    d = pd.read_excel(arq)
    out = []
    for _, l in d.iterrows():
        cod = str(l.get("Código", "")).strip().split(".")[0]
        if not cod.isdigit():
            continue
        preco = num_br(l.get("Preço"))
        out.append(dict(codigo=cod, produto=str(l.get("Produto", "")).strip(), estoque=num_br(l.get("Qtde.")),
                        vista=preco, prazo=preco, oferta=None))
    data = datetime.datetime.fromtimestamp(arq.stat().st_mtime).strftime("%d/%m/%Y")
    return out, data


# ---------------- classificação ----------------

def classificar(produto):
    n = produto.upper()
    if any(re.search(r, n) for r in IGNORAR):
        return None
    m = re.match(r"CIMENTCOLA\b", n)
    if m and re.search(r"20\s*KG", n):
        if "SUPER 7X1" in n:
            classe = "SUPER"
        elif "PORCELANATO" in n:
            classe = "PORC"   # argamassa "porcelanato interno": serve no lugar da AC-III em área interna
        else:
            c = re.search(r"\bAC\s*(III|II|I)\b", n)
            if not c:
                return None
            classe = "AC-" + c.group(1)
        cor = "Branca" if re.search(r"\bBR(ANCA)?\b", n) else "Cinza" if re.search(r"\bCZ\b|CINZA", n) else ""
        return dict(tipo="argamassa", classe=classe, cor=cor, kg=20)
    if n.startswith("REJUNTAMENTO") and (re.search(r"1\s*KG", n) or "CONSTRUCOLA" in n):
        porc = "PORCELANATO" in n
        marca = n.split()[1].title()
        cor = re.sub(r"REJUNTAMENTO\s+\w+\s+(P/PORCELANATO\s+)?", "", n)
        cor = re.sub(r"\s*1\s*KG.*$", "", cor).strip()
        cor = cor.replace("CINZA PLAT", "CINZA PLATINA").replace("PLATINAINA", "PLATINA")
        cor = re.sub(r"\(\s*CLARO\s*\)", "", cor).strip().title()
        cor = cor.replace("Camurca", "Camurça").replace("Marron", "Marrom").replace("Cafe", "Café")
        return dict(tipo="rejunte", porcelanato=porc, cor=cor, marca=marca, kg=1)
    m = re.match(r"ESPACADOR NIVELADOR\b.*?(\d+(?:,\d+)?)\s*MM.*?(\d+)\s*P", n)
    if m:
        return dict(tipo="clip", mm=num_br(m.group(1)), pacote=int(m.group(2)))
    m = re.match(r"ESPACADOR PISO\s+(\d+(?:,\d+)?)\s*MM.*?\((\d+)\s*PE", n)
    if m:
        return dict(tipo="espacador", mm=num_br(m.group(1)), pacote=int(m.group(2)))
    m = re.match(r"CUNHA NIVELADORA\b.*?(\d+)\s*P", n)
    if m:
        return dict(tipo="cunha", pacote=int(m.group(1)))
    return None


def main():
    if not PASTA.exists():
        sys.exit(f"Pasta {PASTA} não existe. Coloque lá os PDFs/planilhas de argamassa, rejunte e espaçador.")
    arquivos = sorted([*PASTA.glob("*.pdf"), *PASTA.glob("*.xls"), *PASTA.glob("*.xlsx")], key=lambda a: a.stat().st_mtime)
    produtos, datas = {}, []
    for arq in arquivos:
        linhas, data = ler_pdf(arq) if arq.suffix.lower() == ".pdf" else ler_planilha(arq)
        datas.append(data)
        for l in linhas:
            produtos[l["codigo"]] = l           # o arquivo mais novo vence
        print(f"  {arq.name}: {len(linhas)} produtos ({data})")

    itens, ignorados = [], []
    for l in produtos.values():
        c = classificar(l["produto"])
        if not c:
            ignorados.append(l["produto"])
            continue
        nome = titulo(l["produto"])
        if c["tipo"] == "rejunte" and "kg" not in nome:
            nome += " 1 kg"
        itens.append(dict(codigo=l["codigo"], nome=nome, estoque=l["estoque"] or 0,
                          vista=l["vista"], prazo=l["prazo"], oferta=l["oferta"], **c))
    itens.sort(key=lambda x: (x["tipo"], x.get("classe", ""), x.get("mm") or 0, x["nome"]))

    hoje = max((d for d in datas if d), key=lambda d: d[6:] + d[3:5] + d[:2], default=None)
    saida = dict(atualizado=hoje, itens=itens)
    txt = json.dumps(saida, ensure_ascii=False, separators=(",", ":"))
    (SITE / "dados" / "materiais.json").write_text(txt, encoding="utf-8")
    (SITE / "dados" / "materiais.js").write_text("window.MATERIAIS=" + txt + ";\n", encoding="utf-8")

    por_tipo = collections.Counter(i["tipo"] for i in itens)
    print(f"\n{len(itens)} materiais: " + ", ".join(f"{k} {v}" for k, v in sorted(por_tipo.items())))
    print(f"Ignorados ({len(ignorados)}): " + "; ".join(sorted(ignorados)))


if __name__ == "__main__":
    main()
