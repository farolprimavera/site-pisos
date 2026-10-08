"""Funções compartilhadas: leitura da planilha, dos PDFs de preço e normalização dos nomes."""
import re, unicodedata
from pathlib import Path
import openpyxl, pdfplumber


def num_br(s):
    s = str(s).strip().replace("R$", "")
    if "," in s:
        s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def ler_planilha(caminho):
    wb = openpyxl.load_workbook(caminho, read_only=True, data_only=True)
    linhas = list(wb.worksheets[0].iter_rows(values_only=True))
    cab = [str(c or "").strip() for c in linhas[0]]
    return [dict(zip(cab, l)) for l in linhas[1:] if l and l[0] is not None]


RE_LINHA = re.compile(r"^\s*(\d{4,7})\s+(.*)$")
RE_PRECOS = re.compile(r"(-?[\d.,]+(?:E-?\d+)?)\s*R\$\s*([\d.,]+)\s+R\$\s*([\d.,]+)(?:\s+R\$\s*([\d.,]+))?")
RE_SEM_PRECO = re.compile(r"(-?[\d.,]+(?:E-?\d+)?)\s*$")


def ler_pdf_precos(pdf, fabricante):
    """Tabela de preço exportada do sistema (Pontual): código, qtde, à vista, a prazo, super oferta."""
    precos = {}
    with pdfplumber.open(pdf) as doc:
        for pag in doc.pages:
            for linha in (pag.extract_text(layout=True) or "").splitlines():
                m = RE_LINHA.match(linha)
                if not m:
                    continue
                cod, resto = m.group(1), m.group(2).rstrip()
                p = RE_PRECOS.search(resto)
                if p:
                    qtd, vista, prazo, oferta = p.groups()
                else:
                    q = RE_SEM_PRECO.search(resto)
                    qtd, vista, prazo, oferta = (q.group(1) if q else "0"), None, None, None
                q = num_br(qtd) or 0.0
                precos[cod] = dict(fabricante=fabricante, estoque=round(q, 2) if abs(q) > 0.005 else 0.0,
                                   vista=num_br(vista) if vista else None, prazo=num_br(prazo) if prazo else None,
                                   oferta=num_br(oferta) if oferta else None)
    return precos


RE_MEDIDA = re.compile(r"(\d+(?:[.,]\d+)?)\s*,?\s*[xX]\s*(\d+(?:[.,]\d+)?)")


def medida(produto):
    m = RE_MEDIDA.search(str(produto))
    if not m:
        return None
    a, b = num_br(m.group(1)), num_br(m.group(2))
    if not a or not b or a < 5 or b < 5:
        return None
    return [a, b]


def sem_acento(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def nome_base(produto):
    """'PISO CALACATA GOLD MAT.RET 75,5X75,5LT:32 (G4/A4)' -> 'CALACATA GOLD MATTE'  (sem medida, lote, RET)."""
    n = sem_acento(str(produto).upper())
    n = re.sub(r"(?<![A-Z])(LT|LOT|L)\s*[:(.].*$", "", n)
    n = re.sub(r"(?<![A-Z])LT\s*\d+.*$", "", n)
    n = re.sub(r"\([^)]*\)?", " ", n)
    n = re.sub(r"\b\d{1,2}[-/]\d{1,2}(?:[-/]\d{2,4})?\b", " ", n)
    n = re.sub(r"/\d+\b", " ", n)
    n = n.replace(")", " ")
    n = re.sub(r"^(PISO|PORCELANATO|REVESTIMENTO|REVEST\.?)\s*", "", n)
    n = RE_MEDIDA.sub(" ", n)
    n = re.sub(r"\bMAT\.", "MATTE ", n)
    n = re.sub(r"\b(RET|RT|L:?)\b\.?", " ", n)
    n = re.sub(r"[.]", " ", n)
    return re.sub(r"\s+", " ", n).strip(" -")


def chave(produto, fabricante):
    m = medida(produto) or [0, 0]
    a, b = sorted(round(x) for x in m)
    return f"{fabricante}|{nome_base(produto)}|{a}x{b}"


def caixa(obs):
    obs = str(obs or "")
    m2 = re.search(r"(\d+[.,]?\d*)\s*m\s*[2²]", obs, re.I)
    pc = re.search(r"(\d+)\s*(?:p[çc]s|pe[çc]as|unid)", obs, re.I) or re.search(r"pe[çc]as\s*(\d+)", obs, re.I)
    return (num_br(m2.group(1)) if m2 else None), (int(pc.group(1)) if pc else None)


def data_pdf(pdf):
    """Data impressa no cabeçalho da tabela de preço ('Data: 06/10/2026')."""
    with pdfplumber.open(pdf) as doc:
        t = doc.pages[0].extract_text() or ""
    m = re.search(r"Data:\s*(\d{2}/\d{2}/\d{4})", t)
    return m.group(1) if m else None
