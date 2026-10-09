# Revestimentos de parede — simulação nos ambientes

> **Para o assistente do VS Code:** complemento do `README-PROJETO.md` (leia ele antes).
> Aqui está como simular **revestimentos de parede**, e não só piso, nas fotos que já estão em `ambientes/`.
> Responda em português. Na dúvida sobre uma medida ou um ponto, **pergunte ao David** e não invente.

## Situação (feito em 09/10/2026)

Passos 1 a 5 feitos, e a fachada da entrada (opcional). O como-usar está no `README.md` §6.1.
- **Nomes dos ambientes:** ficaram os já usados no site (`varanda` = área gourmet, `calcada` = entrada,
  `quintal-piscina` = piscina). Ids das paredes: `banheiro-parede`, `lavanderia-parede`, `varanda-parede`, `calcada-parede`.
- **Paredes ficam em `ambientes/paredes.json`**, não no `ambientes.json` (os scripts de chão percorrem esse arquivo todo).
- **Medidas:** banheiro 346 × 275 cm; lavanderia 209 × 129 cm (só abaixo da prateleira); varanda, backsplash A,
  363 × 86 cm; fachada 240 × 151 cm (dos dois lados da porta, só produtos externos).
- **Réguas de madeira (≥ 3:1)** vão em 1/3 de peça, não a prumo (a prumo ficava artificial).
- **Cozinha não foi feita:** parede em ângulo forte, faixa estreita e cheia de objetos; a faixa de frente, sob a janela,
  tem ~20 cm (só peças cortadas). Não compensava.
- **Pendências:** as fotos de 4 peças têm só 100×100 px (Alfagrês Angelin Noce, Marfil, Native e Pinus Beige), o que
  deixa a simulação borrada no chão e na parede. Uma foto maior resolve nos dois.

---

## 1. Objetivo

Hoje o site só simula **piso**. Os revestimentos (tipo `Revestimento`, local de uso **LA**) e os pisos com
`parede = 1` não aparecem em ambiente nenhum, só a foto da peça. Queremos que eles apareçam **aplicados numa parede**,
com a mesma qualidade da simulação de piso.

---

## 2. Ambientes disponíveis (pasta `ambientes/`)

São 11 imagens geradas por IA, todas com **1536 × 1024 px**, chão de cimento liso cinza e paredes brancas/claras.

1. Primeiro **liste a pasta**.
2. Identifique cada imagem pelo conteúdo e **renomeie** seguindo a tabela abaixo (confirme com o David antes de renomear).

| Arquivo sugerido | Conteúdo | Piso | Parede |
|---|---|---|---|
| `sala` | sofá, rack com TV, janela grande | ✅ | — |
| `quarto` | cama de casal, guarda-roupa | ✅ | — |
| `escritorio` | mesa, cadeira preta, estante | ✅ | — |
| `loja` | estantes com produtos, balcão | ✅ | — |
| `garagem` | carro preto, portão aberto | ✅ | — |
| `piscina` | piscina, espreguiçadeiras | ✅ | — |
| `entrada` | porta de madeira, degrau | ✅ | ⚪ opcional (fachada) |
| `banheiro` | bancada, box de vidro, vaso | ✅ | ✅ **prioridade 1** |
| `lavanderia` | máquina de lavar, tanque, cesto | ✅ | ✅ **prioridade 2** |
| `area-gourmet` | churrasqueira, bancada de madeira, mesa | ✅ | ✅ **prioridade 3** |
| `cozinha` | armários em L, geladeira, mesinha | ✅ | ⚪ opcional (parede em ângulo) |

---

## 3. As paredes de cada ambiente

Coordenadas **aproximadas**, em pixels da imagem de 1536 × 1024 (origem no canto superior esquerdo). São só ponto de
partida: **confira e ajuste** sobre a imagem real.

### 3.1 Banheiro (prioridade 1, a melhor)
- **Superfície:** a parede branca grande **de frente**, à direita do box de vidro.
- **Região:** x ≈ 600 → 1235, y ≈ 0 (topo da imagem) → 497 (linha do rodapé).
- **Fica fora da máscara (objetos na frente):** o vaso de planta (x ≈ 1150–1290, y ≈ 260–555) e a quina da parede lateral direita.
- **Rodapé:** o revestimento vai **até o chão**. Pinte o rodapé branco por cima, pois em banheiro não se usa rodapé.
- **Opcional:** a parede dentro do box, atrás do vidro. Fica para depois: aplicar atrás do vidro exige simular reflexo e transparência.

### 3.2 Lavanderia (prioridade 2)
- **Superfície:** a parede do fundo, de frente, entre as duas colunas.
- **Região:** x ≈ 440 → 1045, y ≈ 122 (logo abaixo da prateleira de madeira) → 490 (rodapé).
- **Fica fora da máscara:** a máquina de lavar (x ≈ 500–715, y ≈ 245–505), o tanque/gabinete (x ≈ 737–970, y ≈ 258–505), o cesto
  (x ≈ 1008–1135, y ≈ 345–512), a torneira e o frasco.
- **Também pode receber revestimento:** o trecho de parede acima da prateleira, até o topo. Faça a primeira versão só do trecho abaixo.

### 3.3 Área gourmet (prioridade 3)
Duas opções. Comece pela **A**.
- **A. Backsplash da bancada:**
  - **Região:** a faixa branca entre a bancada preta e a prateleira de madeira, x ≈ 510 → 1090, y ≈ 186 → 318.
  - **Fica fora:** tábuas, garrafas, vasos, torneira, potes e a luz de LED embaixo da prateleira. A luz quente deve
    **continuar aparecendo** por cima do revestimento (use a luminância original, ver §5).
- **B. Coluna da churrasqueira:**
  - **Região:** a face de frente, x ≈ 310 → 520, y ≈ 45 → 500.
  - **Fica fora:** a boca da churrasqueira (x ≈ 335–482, y ≈ 222–338) e a gaveta de cinzas.
  - Essa coluna já tem pedra cinza com rejunte desenhado. A textura nova precisa **cobrir 100%** (opacidade total), sem deixar o rejunte antigo aparecer.

### 3.4 Cozinha (opcional)
- **Superfície:** a parede **lateral esquerda** entre a bancada e os armários de cima. Está em **ângulo forte**, mas a homografia resolve.
- A faixa é estreita, com cooktop, tábuas e utensílios na frente. Faça só depois das três primeiras.

### 3.5 Entrada (opcional, fachada)
- **Superfícies:** os trechos de parede branca ao lado da porta. São bons para **revestimento de fachada/externo**.
- O banco e os vasos ficam fora da máscara.

---

## 4. Arquivos de cada parede

Para cada parede crie, em `ambientes/`:
- `<id>-parede-mask.png`: máscara do mesmo tamanho da foto. **Branco** onde vai revestimento e **preto** no resto.
  Objetos na frente da parede ficam **pretos**. Bordas com 1–2 px de suavização (feather) para não serrilhar.
- Uma entrada nova em `ambientes.json`, **separada** da entrada de piso:
  ```json
  "banheiro-parede": {
    "id": "banheiro-parede",
    "ambiente": "banheiro",
    "superficie": "parede",
    "nome": "Banheiro",
    "pontos": [[600, 0], [1235, 0], [1235, 497], [600, 497]],
    "largura_cm": 260,
    "altura_cm": 220,
    "ppc": 6,
    "inicio": "baixo"
  }
  ```
  - `pontos`: 4 cantos de um **retângulo real** da parede, na ordem **superior-esq → superior-dir → inferior-dir → inferior-esq**.
    Para parede de frente, quase um retângulo na imagem; para parede em ângulo (cozinha), um trapézio.
  - `largura_cm` / `altura_cm`: medidas reais desse retângulo. **Estime com referências da própria foto**:

    | Referência | Medida real aproximada |
    |---|---|
    | máquina de lavar | ~60 cm de largura × 85 cm de altura |
    | bancada de cozinha/gourmet | ~90 cm de altura |
    | vaso sanitário | ~40 cm de altura do assento |
    | porta | ~210 cm de altura |
    | pé-direito | ~260 cm |

    Os valores do exemplo são chute. **Calcule e mostre ao David** antes de gerar tudo.
  - `inicio`: de onde a paginação começa. `"baixo"` quer dizer peça inteira apoiada no chão ou na bancada. É assim que o
    azulejista assenta, e as peças cortadas ficam lá em cima.
- Crie ou adapte `ferramentas/ver_perspectiva.py` para desenhar a **grade de 10 cm** e a **silhueta de uma peça 30×60**
  por cima da parede. Conferir isso antes de renderizar evita retrabalho.

---

## 5. Render de parede (`render.py`)

Reaproveite a mesma função do piso, mudando só o necessário.

1. **Homografia:** igual à do piso, mas o retângulo é `largura_cm × altura_cm`, na vertical.
2. **Paginação:**
   - **Retangulares (ex.: 30×60, 33×60):** **na horizontal** (lado maior deitado). Assentamento **reto**, alinhado com
     junta a prumo. Linhas horizontais **niveladas** com a bancada ou o chão.
   - **Quadradas e decorativas:** reto.
   - **Filetado, tijolinho (Mattone, Canjiquinha…):** amarração meia peça.
   - A primeira fiada começa **inteira** na base (`inicio: "baixo"`) e é centralizada na horizontal.
3. **Rejunte:**
   - 2 mm se retificado, 3 mm se não.
   - Cor do rejunte: um tom próximo da média da peça, levemente mais escuro. Rejunte branco em peça escura fica feio.
4. **Rotação aleatória de 180°:** só em peças lisas, mármore e cimentício. **Nunca** em peças com desenho direcional
   (madeira, filetado, decor).
5. **Luz e sombra:** igual ao piso, usando a luminância desfocada da foto original. Na parede use desfoque **maior** e
   intensidade **menor** (`sombra ≈ 0.5`). O que importa é manter os gradientes de luz (LED da área gourmet, luz da
   janela) e a sombra de contato dos objetos.
6. **Brilho:**
   - **Brilhante/polido:** some um reflexo suave, uma faixa clara difusa vinda da janela, com 5–8% de intensidade.
   - **Matte/acetinado:** sem reflexo.
7. **Composição:** alfa da máscara de parede **por cima** da foto original. O piso continua o cimento original.
8. **Saída:** `imagens/<ambiente>/parede/<id>.webp` (1280 px) e `imagens/<ambiente>/parede/mini/<id>.webp` (520 px).
   Use a mesma lógica incremental do `controle.json`, com a chave `<ambiente>-parede/<id>`.

---

## 6. Quais produtos vão para a parede

| Produto | Onde renderizar |
|---|---|
| Revestimentos (`local_uso = LA`) | só nas paredes: banheiro, lavanderia, área gourmet (e cozinha, se feita) |
| Pisos com `parede = 1` (ex.: Alfagrês "1 e 3") | no chão **e** na parede |
| Externos (`externo = 1`) com `parede = 1` | também na fachada da entrada, se ela for feita |
| Pisos sem `parede = 1` | não vão para a parede |

No `pisos.json`, acrescente para cada produto um campo `"paredes": ["banheiro", "lavanderia", ...]` ao lado do
`"ambientes"` (que continua sendo só piso).

---

## 7. Mudanças no site

- Aba no topo: **Pisos | Revestimentos**, em vez da seção escondida no fim da página.
- **Vitrine:**
  - para revestimento, as abas de ambiente mostram só os que têm parede (Banheiro, Lavanderia, Área gourmet);
  - para piso que também é parede, aparecem os dois grupos: "No chão" e "Na parede".
- **Cards de revestimento:** miniatura da parede (`object-position` centrado na parede) com a foto da peça no canto, igual aos pisos.
- **Calculadora do modal:** para revestimento, peça **largura × altura da parede** em vez de m² de chão (mantendo +10%).

---

## 8. Ordem de trabalho

1. Listar e renomear as imagens (confirmar com o David).
2. **Banheiro:** máscara → pontos → `ver_perspectiva.py` → mostrar ao David.
3. Render de parede com **3 produtos de teste**: um revestimento liso branco, um decorado/filetado e um piso 31×60 com `parede = 1`.
   Mostrar ao David.
4. Ajustes aprovados → lavanderia e área gourmet.
5. Gerar tudo, atualizar o `pisos.json` (`paredes`) e o site (§7).
6. Opcionais: cozinha e entrada.

## 9. Cuidados

- Não deixe o revestimento **invadir objetos**: confira a máscara com zoom nas bordas (vaso, máquina, garrafas).
- As linhas de rejunte têm que ficar **retas e niveladas**. Se entortarem, os pontos da homografia estão errados.
- A escala tem que convencer: num banheiro de 2,6 m de altura cabem ~4 fiadas de 60 cm. Se couberem 10, a medida está errada.
- Não regenere as imagens de piso ao mexer na parede: as assinaturas no `controle.json` são independentes.
