# Pisos e Revestimentos · Farol da Primavera — README / prompt inicial

> **Para o assistente (Copilot / Claude no VS Code):** este arquivo é o briefing completo do projeto.
> Vamos começar **do zero**. O David vai importando os arquivos (planilhas, PDFs, fotos, imagens de ambiente)
> aos poucos. Leia tudo antes de criar qualquer coisa, siga a estrutura de pastas abaixo e, na dúvida,
> pergunte em vez de inventar dados (preço, local de uso, medida). Responda em português.

---

## 1. O que é

Um **site estático** (GitHub Pages, sem servidor, sem banco) com o catálogo de **pisos e revestimentos que a loja tem em estoque**.

- Cada piso aparece **já aplicado** em fotos de ambientes (sala, quarto, cozinha, escritório…). As simulações são
  **geradas antes**, em Python, e o site só mostra imagens prontas.
- Mostra **preço** (à vista, a prazo e oferta), medida, m² por caixa e local de uso.
- Tem **filtros** por fabricante, onde usar, estilo, acabamento e formato. Também tem busca e ordenação.
- Deve abrir **com dois cliques no `index.html`** (via `file://`), além de funcionar publicado no GitHub Pages.

Fabricantes base: **Cedasa**, **Grupo Rocha (Rochaforte)** e **Alfagrês**.
Inspiração visual: sites e folders dessas três marcas.
- https://www.cedasa.com.br/
- https://www.portalgruporocha.com.br/
- https://www.alfagres.com.br/

---

## 2. Estrutura de pastas

```
site-pisos/                    ← pasta de trabalho (NÃO vai pro GitHub)
├── pisos.xlsx                 lista de pisos exportada do sistema (Código | Produto | Observação)
├── alfagres/*.pdf             tabela de preço/estoque do sistema Pontual, uma por fabricante
├── cedasa/*.pdf
├── rochaforte/*.pdf
├── fotos/<código>.jpg         foto da peça (nome = código do produto no sistema)
└── site-pisos/                ← ESTA pasta = repositório git = raiz do GitHub Pages
    ├── index.html             só a estrutura (HTML). Sem <style> nem <script> inline grandes
    ├── css/
    │   └── styles.css         todo o visual
    ├── js/
    │   ├── app.js             inicialização, estado, leitura de dados
    │   ├── filtros.js         filtros, busca e ordenação
    │   ├── vitrine.js         destaque grande + abas de ambiente
    │   ├── cards.js           grade de produtos
    │   └── detalhe.js         modal de detalhe + calculadora + WhatsApp
    ├── dados/
    │   ├── pisos.json         catálogo gerado
    │   └── pisos.js           o mesmo catálogo como  window.PISOS = {...};  (para abrir via file://)
    ├── imagens/
    │   ├── <ambiente>/<id>.webp        simulação grande (1280 px de largura)
    │   ├── <ambiente>/mini/<id>.webp   miniatura da grade (520 px)
    │   ├── pecas/<id>.webp             foto da peça (até 600 px)
    │   └── controle.json               assinaturas para gerar só o que mudou
    ├── ambientes/             fotos-base dos ambientes + máscaras + perspectiva (ver §6)
    ├── ferramentas/           scripts Python (não pesam no site)
    │   ├── comum.py
    │   ├── montar_dados.py
    │   ├── render.py
    │   ├── gerar_imagens.py
    │   ├── fichas.csv
    │   └── relatorio.txt      gerado: o que ficou fora do site e por quê
    ├── .gitignore             __pycache__/  *.pyc  build/  *.zip
    ├── .nojekyll
    └── README.md
```

Regras:
- Nada de framework nem build (sem React, sem npm). Use HTML, CSS e JS puro, com vários `<script src>` em ordem,
  sem `type="module"`, porque módulos ES não carregam via `file://`.
- O JS **não pode depender de `fetch`** para funcionar localmente. Ele lê `window.PISOS` (de `dados/pisos.js`) e só usa
  `fetch("dados/pisos.json")` como plano B.
- Caminhos sempre relativos (`css/styles.css`, `imagens/...`). Nunca `/` absoluto, para não quebrar no GitHub Pages.

---

## 3. Dados de entrada e regras de negócio

### 3.1 `pisos.xlsx`
Colunas: **Código | Produto | Observação**. O nome do produto traz lote e medida, por exemplo
`PORC. CEDASA HD 1743 58X58 RET LT 123`. A observação costuma trazer m²/caixa e peças/caixa.

### 3.2 PDFs de preço (sistema Pontual)
- Ler com `pdfplumber`, usando `page.extract_text(layout=True)` e regex por linha.
- Cada linha traz código, produto, estoque, preço à vista, a prazo e oferta.
- A data dos preços vem do cabeçalho `Data: dd/mm/aaaa`. Mostrar no site como "Preços atualizados em …".
- Números no formato brasileiro (`1.234,56`).

### 3.3 Agrupamento
- Um mesmo piso tem **vários lotes/códigos**. Agrupe por uma **chave** `FABRICANTE|NOME BASE|MEDIDA`
  (ex.: `ALFAGRES|3001|31x60`).
- O nome base é o nome sem lote (`LT 123…`), sem `RET`/`RT`, sem medidas e datas. `MAT.` vira `MATTE`.
  Regex do lote: `(?<![A-Z])LT\s*\d+.*$`.
- **Só entra no site o que tem estoque > 0, foto e ficha** (linha no `fichas.csv`).
- Preço exibido: o do lote com **maior estoque**. Oferta: a **menor oferta** entre os lotes com estoque.
- "Super oferta": desconto relevante sobre o preço a prazo (vira filtro "Só super ofertas" e selo no card).
- Retificado (RET/RT no nome) influencia o rejunte da simulação: 1,5 mm se retificado, 3 mm se não.

### 3.4 Local de uso (`fichas.csv`)
Colunas: `chave;local_uso;externo;parede;acabamento;estilo;fonte`.

| Código | Uso |
|---|---|
| LA | só parede |
| LB | quarto / sala (tráfego leve) |
| LC | + cozinha |
| LD | + áreas cobertas, comércio leve |
| LE / LF | tráfego intenso |
| LS (Rocha) | uso externo |

Conversões:
- **Alfagrês** usa uma escala de 1 a 5, convertida assim: 1→LA, 2→LB, 3→LC, 4→LD, 5→LD + externo.
  O campo "Interno/Externo" liga o `externo`. "1 e 3" significa LC + parede. **Confirmar com o David.**
- **Rocha**: o código da loja `HD 70082` corresponde ao produto `R7008` no site da marca (o último dígito é sufixo).
  Os itens `40xx2` são revestimentos de parede (LA).
- A coluna `fonte` diz de onde veio a informação. Linhas que começam com `SUPOSTO` são palpites e **precisam de confirmação**.

Categorias "onde usar" (filtro em chips):
- **quarto/sala**: LB ou mais
- **cozinha**: LC ou mais
- **área coberta**: LD ou mais
- **área externa**: `externo = 1`
- **parede**: `parede = 1` ou LA

Ambientes onde o piso é renderizado (regra em `ambientes/ambientes.json` → `"regra"`; o piso só vai para o ambiente se fizer sentido):

| Ambiente | Local de uso mínimo | Fica de fora |
|---|---|---|
| sala, quarto, escritório | LB | Rústico |
| cozinha | LC | Rústico |
| banheiro | LC | Rústico, Polido (escorrega) |
| lavanderia, varanda gourmet | LD | Polido |
| loja | LD | Rústico |
| garagem | LD | Polido, Brilhante |
| calçada/entrada, quintal com piscina | LD **e** liberado para área externa | Polido, Brilhante |

- revestimento de parede (LA): só foto da peça, numa seção própria "Revestimentos"

### 3.5 Formato do `pisos.json`
```json
{
  "atualizado": "08/10/2026",
  "locais": { ... },
  "pisos": [{
    "id": "alfagres-3001-60", "chave": "ALFAGRES|3001|31x60", "nome": "3001",
    "fabricante": "Alfagrês", "tipo": "Piso", "medida": "31 × 60 cm", "medida_cm": [31, 60],
    "formato": "31x60", "caixa_m2": 2.08, "caixa_pecas": 11,
    "vista": 30.9, "prazo": 33.9, "oferta": 21.6,
    "local_uso": "LC", "onde": ["quarto", "cozinha", "parede"],
    "acabamento": "Brilhante", "estilo": "Liso", "retificado": false,
    "foto": "1011200", "codigos": ["1011200", "1007275"],
    "ambientes": ["sala", "quarto", "escritorio", "cozinha"]
  }]
}
```
O `montar_dados.py` grava o `.json`, o `.js` (`"window.PISOS=" + json + ";"`) e o `relatorio.txt`, que lista
o que ficou fora do site: sem foto, sem ficha, sem estoque, itens SUPOSTO.

---

## 4. Site (front-end)

**Identidade:**
- Fonte **Archivo** (Google Fonts).
- Paleta em variáveis CSS no `:root`:

| Variável | Cor |
|---|---|
| `--verde` | `#0e5a3a` |
| `--amarelo` | `#f2c230` |
| `--vermelho` | `#c8302b` (ofertas) |
| `--fundo` | `#f3f5f4` |

Seções:
1. **Vitrine (hero):** a simulação grande do piso selecionado, com **abas de ambiente** (Sala, Quarto, Cozinha,
   Escritório…) e um bloco de preço ao lado. Trocar de piso troca a imagem. Abas de ambientes que não servem
   para aquele piso ficam desabilitadas.
2. **Barra de filtros fixa (sticky):**
   - chips "onde usar" e busca por nome ou código;
   - selects de marca, estilo, acabamento e formato;
   - ordenação: maior desconto (padrão), menor preço, nome;
   - "Só super ofertas".
   - No celular, os selects ficam atrás de um botão **"Mais filtros"**.
3. **Grade de cards:**
   - a miniatura do ambiente atual (proporção 5/4, `object-position: 50% 100%` para mostrar o chão) com a foto da peça
     pequena no canto;
   - nome, marca, medida e preço por m², com selo de oferta.
   - Os revestimentos ficam numa seção separada.
4. **Modal de detalhe (`<dialog>`):**
   - preços e "onde usar";
   - ficha (acabamento, estilo, retificado, m²/caixa);
   - **calculadora**: m² do ambiente → caixas, +10% de perda;
   - botão **copiar link**;
   - botão **WhatsApp** "Pedir orçamento", que só aparece se `const WHATSAPP = "55DDDNUMERO"` estiver preenchido
     (em `js/app.js`).
5. **Deep link:** `index.html#<id>` abre direto o modal daquele piso.

Outros requisitos:
- Imagens com `loading="lazy"`.
- Responsivo de verdade: celular primeiro, sem rolagem horizontal.
- Avisos no rodapé: preços sujeitos a alteração, cores podem variar na tela, data da atualização.

---

## 5. Gerador de simulações (Python + OpenCV)

Dependências:
```bash
pip install --break-system-packages openpyxl pdfplumber opencv-python-headless numpy
```

O `render.py` aplica a textura do piso no chão da foto do ambiente:
1. **Homografia:** usa os 4 cantos de um retângulo do chão na foto (longe-esq, longe-dir, perto-dir, perto-esq) e as
   medidas reais desse retângulo em cm (`largura_cm`, `profundidade_cm`). Normalize o sinal de `w` pelo centroide.
2. **Textura plana:**
   - repete a peça na escala real (`ppc` = pixels por cm, ex.: 6), com linha de rejunte;
   - gira peças aleatoriamente em 180° para não parecer carimbo;
   - Layouts: `reto` (padrão), `amarracao`, e `amarracao3` (réguas/porcelanato madeira, quando o lado maior ≥ 3× o menor).
3. `cv2.warpPerspective` com **supersampling 2×** e redução com `INTER_AREA` para não serrilhar.
4. **Sombra/luz:** usa a luminância desfocada da foto original, assim os móveis continuam projetando sombra:
   ```python
   s = np.clip(1 + (gb / ref - 1) * sombra, 0.3, 1.3)[..., None]
   piso = piso * np.minimum(s, 1.08) + np.maximum(s - 1.08, 0) * 60
   ```
5. **Recorte:** usa a máscara do chão (PNG branco = chão) como alfa. Os móveis ficam por cima.
6. Saída em WebP: grande com 1280 px de largura (qualidade 80), mini com 520 px (qualidade 76), peça até 600 px (qualidade 82).

O `gerar_imagens.py` é **incremental**:
- Cada imagem tem uma assinatura `VERSAO|md5(foto)|medida|parâmetros|md5(ambiente+máscara+json)` guardada em `imagens/controle.json`.
- Só regera o que mudou.
- `--tudo` força refazer tudo. Mudar `VERSAO` também.
- Apaga as imagens de pisos que saíram do site.

---

## 6. Ambientes (as imagens vão mudar)

O David vai trazer **novas fotos de ambiente** e talvez mais ambientes. Para cada um, crie em `ambientes/`:
- `<id>.jpg`: a foto (ex.: 1480 px de largura). Sem texto ou marca d'água em cima do chão.
- `<id>-mask.png`: máscara do chão, do mesmo tamanho, branco onde é chão e preto no resto.
  Pés de móveis e tapetes ficam **fora** (preto).
- Uma entrada em `ambientes.json`:
  ```json
  "sala": { "id": "sala", "nome": "Sala",
            "pontos": [[467,578],[1107,578],[1681.5,1000],[39.7,1000]],
            "largura_cm": 340, "profundidade_cm": 318.8, "ppc": 6 }
  ```
  `pontos` são os 4 cantos do retângulo de chão, nesta ordem: longe-esquerda, longe-direita, perto-direita,
  perto-esquerda. Podem cair fora da imagem. `largura_cm` e `profundidade_cm` são as medidas reais desse retângulo.
  Para estimar, use pontos de fuga e um FOV horizontal de ~75°, ou uma referência conhecida (porta ≈ 80 cm, cama casal ≈ 138 cm).
- **Como está feito hoje:** em vez de medir os 4 pontos à mão, cada ambiente tem `"camera": {"pf": [x, y], "altura_cm", "f"}`
  (ponto de fuga dos rodapés laterais, altura da câmera e focal ~1150 px). `python ferramentas/perspectiva.py` calcula
  `pontos`/`largura_cm`/`profundidade_cm` a partir disso.
- `python ferramentas/mascara.py [ambiente]` gera a máscara crescendo a região do chão a partir do pé da foto
  (parâmetros em `"mascara"`: polígono, excluir, incluir, sementes).
- `python ferramentas/ver_perspectiva.py [ambiente]` desenha a grade de 50 × 50 cm e a máscara (vermelho) em
  `ferramentas/build/grade-<ambiente>.jpg`, para conferir antes de renderizar tudo.
- A máscara pode começar por segmentação de cor/textura dentro de um polígono do chão, com polígonos de exclusão
  (tapete, mesa) e de inclusão, e depois ser **retocada à mão**. É o passo que mais afeta a qualidade.
- Se o David gerar as fotos com IA, peça o chão **liso, claro e sem tapete**, com câmera na altura dos olhos.
  Assim a máscara e a sombra ficam muito melhores.

---

## 7. Fluxo de atualização

```bash
cd site-pisos/site-pisos
python3 ferramentas/montar_dados.py     # lê xlsx + PDFs + fichas → dados/pisos.json/.js + relatório
python3 ferramentas/gerar_imagens.py    # só gera o que é novo
git add -A && git commit -m "Atualiza preços" && git push
```
Piso novo:
1. Coloque a foto em `fotos/<código>.jpg`.
2. Adicione a linha no `fichas.csv`. A chave aparece no `relatorio.txt`.
3. Rode os dois scripts.

GitHub Pages: Settings → Pages → *Deploy from a branch* → `main` / `(root)`.

---

## 8. Lições aprendidas (não repetir)

- `fetch` não funciona abrindo o HTML direto do disco. Por isso existe o `pisos.js`.
- Remover texto ou marca da foto com `cv2.inpaint` borra o chão. Prefira fotos limpas.
- A máscara automática pega tampo de mesa e tapete como se fosse chão. Sempre confira visualmente.
- Cuidado com a especificidade do CSS: uma regra como `.card .foto img` sobrescreveu a miniatura da peça.
  Use classes próprias (`.peca-mini`).
- Não suba zips de imagens para o repositório: `*.zip` fica no `.gitignore`.

## 9. Pendências conhecidas

- Confirmar os itens marcados `SUPOSTO` no `fichas.csv`.
- Confirmar a conversão da escala 1–5 da Alfagrês.
- Faltam fotos de 8 produtos:
  - Cedasa: HD 1743 57x57, Luxor Blanc, Lyon Brilho e RTGC0115.
  - Rocha: HD 70442, 70622, 70861 e 70952.
- Preencher o número do WhatsApp.

---

## 10. Por onde começar (ordem sugerida)

1. Criar a estrutura de pastas, o `.gitignore`, o `.nojekyll` e um `index.html` vazio ligando `css/styles.css` e os `js/*.js`.
2. `ferramentas/comum.py` + `montar_dados.py`, com o `xlsx`, os PDFs e o `fichas.csv` importados → gerar `dados/pisos.json/.js`.
3. Front-end com dados reais, usando por enquanto só as fotos das peças.
4. Trazer os ambientes novos → máscara + perspectiva → `render.py` testado em 2 ou 3 pisos.
5. Gerar tudo, revisar visualmente, publicar.
