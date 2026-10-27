/* Materiais para assentar: argamassa, rejunte, espaçador e nivelador (clips + cunhas),
   já com os produtos da loja (dados/materiais.js, gerado por ferramentas/montar_materiais.py).
   Usado pela calculadora do detalhe (js/detalhe.js).

   As QUANTIDADES são estimativas pelas tabelas dos fabricantes; o site sempre avisa para
   confirmar com o vendedor.

   - Argamassa (boletins técnicos quartzolit Cimentcola, seção "Dados técnicos"):
       peça até 400 cm² ......... camada simples, dente 6 mm ...... ± 4,0 kg/m²
       peça de 400 a 900 cm² .... camada simples, dente 8 mm ...... ± 4,5 kg/m²
       peça acima de 900 cm² .... dupla colagem (base e verso) .... ± 8,0 kg/m²
     Tipo: AC-III para polido, retificado e peça de 60 × 60 cm ou maior (3.600 cm²);
           AC-II para área externa; AC-I para o resto (cerâmica em área interna).
     Pode oferecer argamassa "acima" da pedida (AC-II no lugar da AC-I), nunca abaixo.
   - Rejunte: fórmula usada pelos fabricantes
       kg/m² = (C + L) / (C × L) × E × J × D
       C, L = lados da peça (mm) · E = espessura da peça (mm) · J = junta (mm) · D = 1,6 (densidade)
     Junta: 2 mm em peça retificada, 3 mm nas outras. Espessura: 8 mm (lado < 60 cm) ou 9 mm.
     Peça retificada ou polida: primeiro o rejunte "p/ porcelanato".
   - Nivelador (só no chão, peça com lado de 45 cm ou mais): clips a cada ~35 cm em cada lado;
     cada peça "fica" com 2 lados (os outros 2 são da vizinha). O clip é descartável (a base fica
     embaixo da peça e o topo é quebrado depois), então vai 1 por ponto, na obra toda.
     A cunha é reutilizável: sai depois que a argamassa seca (~24 h) e volta para o próximo trecho.
     Basta cunha para 1 dia de assentamento (MATERIAIS.areaDia m²); obra menor que isso, 1 por clip.
     Mínimo 1 pacote.
   - Espaçador (peça menor e toda parede): 1 cruzeta por peça (cada canto é dividido entre 4 peças).

   Produto oferecido: só o que tem estoque para a quantidade pedida. O padrão é o mais barato
   da classe certa; o cliente troca no seletor (cor do rejunte, marca etc.). */

const MATERIAIS = {
  perda: 0.1,          // +10%, igual às peças
  sacoArgamassa: 20,   // kg (todas as argamassas da loja são de 20 kg)
  densidadeRejunte: 1.6,
  ladoNivelador: 45,   // cm: a partir daqui recomenda nivelador em vez de espaçador
  passoClip: 35,       // cm entre clips
  areaDia: 20,         // m² assentados por dia com nivelador: as cunhas voltam no dia seguinte
  corRejunte: "Cinza Platina", // cor que vem marcada primeiro
};

const Materiais = {
  escolhas: {},   // produto escolhido pelo cliente em cada linha (id da linha → código)
  fora: new Set(), // linhas que o cliente desmarcou (não entram no total nem no WhatsApp)

  produtos(tipo) {
    return ((window.MATERIAIS && window.MATERIAIS.itens) || []).filter((m) => m.tipo === tipo);
  },

  preco(m) {
    return m.oferta || m.vista || m.prazo || 0;
  },

  // Linhas de material para cobrir `area` m² com o produto p (parede = true: revestimento na parede).
  calcular(p, area, parede = false) {
    if (!(area > 0) || !p.medida_cm) return [];
    const [a, b] = p.medida_cm;                // cm
    const maior = Math.max(a, b), areaPeca = a * b;
    const pecas = Math.ceil(area * (10000 / areaPeca) * (1 + MATERIAIS.perda));
    const junta = p.retificado ? 2 : 3;
    const mm = String(junta).replace(".", ",");
    const linhas = [];

    // argamassa
    const consumo = areaPeca <= 400 ? 4.0 : areaPeca <= 900 ? 4.5 : 8.0;
    const sacos = Math.ceil(area * consumo * (1 + MATERIAIS.perda) / MATERIAIS.sacoArgamassa - 1e-9);
    const classe = Materiais.tipoArgamassa(p);
    // SUPER = Garramax Super 7x1 (uso geral, interno e externo): opção em qualquer classe, nunca a 1ª da AC-III
    const aceitas = { "AC-I": ["AC-I", "AC-II", "AC-III", "SUPER"], "AC-II": ["AC-II", "AC-III", "SUPER"],
      "AC-III": ["AC-III", "SUPER", ...((p.onde || []).includes("externa") ? [] : ["PORC"])] }[classe];
    linhas.push(Materiais.linha({
      id: "argamassa", nome: `Argamassa ${classe}`, rotulo: (m) => m.nome.replace(/^Cimentcola /, ""),
      qtd: `${sacos} saco${sacos > 1 ? "s" : ""} de 20 kg`,
      det: areaPeca > 900 ? "dupla colagem: na base e no verso da peça" : `desempenadeira dente ${areaPeca <= 400 ? 6 : 8} mm`,
      opcoes: Materiais.produtos("argamassa").filter((m) => aceitas.includes(m.classe)),
      unidades: () => sacos,
      ordem: (m) => [m.classe === classe ? 0 : 1, Materiais.preco(m), m.cor === "Cinza" ? 0 : 1],
    }));

    // rejunte
    const E = maior < 60 ? 8 : 9;
    const kgM2 = ((a + b) * 10 / (a * 10 * b * 10)) * E * junta * MATERIAIS.densidadeRejunte;
    const kg = Math.max(1, Math.ceil(area * kgM2 * (1 + MATERIAIS.perda) - 1e-9));
    const porc = p.retificado || p.acabamento === "Polido";
    linhas.push(Materiais.linha({
      id: "rejunte", nome: "Rejunte", rotulo: (m) => `${m.cor} · ${m.marca || ""}${m.porcelanato ? " p/ porcelanato" : ""}`,
      qtd: `${kg} kg`,
      det: `junta de ${mm} mm${porc ? " · peça retificada: rejunte p/ porcelanato" : ""} · escolha a cor`,
      opcoes: Materiais.produtos("rejunte"),
      unidades: () => kg,
      ordem: (m) => [m.porcelanato === porc ? 0 : 1, m.cor === MATERIAIS.corRejunte ? 0 : 1, m.cor, Materiais.preco(m)],
    }));

    if (!parede && maior >= MATERIAIS.ladoNivelador) {
      const porPeca = Math.ceil(a / MATERIAIS.passoClip) + Math.ceil(b / MATERIAIS.passoClip);
      const clips = pecas * porPeca;
      linhas.push(Materiais.linha({
        id: "clip", nome: `Nivelador ${mm} mm (clips)`, rotulo: (m) => m.nome.replace(/^Espaçador Nivelador /, ""),
        qtd: (m) => m ? `${Math.ceil(clips / m.pacote)} pacote${Math.ceil(clips / m.pacote) > 1 ? "s" : ""} de ${m.pacote}` : `${clips} clips`,
        det: `${clips} clips · ${porPeca} por peça · descartável: 1 por ponto, não dá para reutilizar`,
        opcoes: Materiais.produtos("clip").filter((m) => m.mm === junta),
        unidades: (m) => Math.ceil(clips / m.pacote),
        ordem: (m) => [Math.ceil(clips / m.pacote) * Materiais.preco(m)],
      }));
      // cunha reutilizável: só o que fica preso num dia de trabalho (os clips desse trecho)
      const cunhas = Math.ceil(clips * Math.min(1, MATERIAIS.areaDia / area));
      linhas.push(Materiais.linha({
        id: "cunha", nome: "Cunhas niveladoras", rotulo: (m) => m.nome.replace(/^Cunha Niveladora /, ""),
        qtd: (m) => m ? `${Math.ceil(cunhas / m.pacote)} pacote${Math.ceil(cunhas / m.pacote) > 1 ? "s" : ""} de ${m.pacote}` : `${cunhas} cunhas`,
        det: area > MATERIAIS.areaDia
          ? `reutilizável: ${cunhas} cunhas dão para ~${MATERIAIS.areaDia} m² por dia; depois de 24 h tire e use no próximo trecho`
          : `reutilizável, mas a obra cabe em 1 dia (até ~${MATERIAIS.areaDia} m²): 1 por clip`,
        opcoes: Materiais.produtos("cunha"),
        unidades: (m) => Math.ceil(cunhas / m.pacote),
        ordem: (m) => [Math.ceil(cunhas / m.pacote) * Materiais.preco(m)],
      }));
    } else {
      linhas.push(Materiais.linha({
        id: "espacador", nome: `Espaçador ${mm} mm`, rotulo: (m) => m.nome.replace(/^Espaçador Piso /, ""),
        qtd: (m) => m ? `${Math.ceil(pecas / m.pacote)} pacote${Math.ceil(pecas / m.pacote) > 1 ? "s" : ""} de ${m.pacote}` : `${pecas} unidades`,
        det: `${pecas} cruzetas · 1 por peça`,
        opcoes: Materiais.produtos("espacador").filter((m) => m.mm === junta),
        unidades: (m) => Math.ceil(pecas / m.pacote),
        ordem: (m) => [Math.ceil(pecas / m.pacote) * Materiais.preco(m)],
      }));
    }
    return linhas;
  },

  // Monta uma linha: filtra o que tem estoque para a quantidade, ordena e escolhe o produto.
  linha(cfg) {
    const comp = (x, y) => {
      const a = cfg.ordem(x), b = cfg.ordem(y);
      for (let i = 0; i < a.length; i++) {
        if (a[i] < b[i]) return -1;
        if (a[i] > b[i]) return 1;
      }
      return 0;
    };
    const opcoes = cfg.opcoes.filter((m) => (m.estoque || 0) >= cfg.unidades(m)).sort(comp);
    const salvo = opcoes.find((m) => m.codigo === Materiais.escolhas[cfg.id]);
    return { ...cfg, opcoes, produto: salvo || opcoes[0] || null };
  },

  tipoArgamassa(p) {
    const [a, b] = p.medida_cm || [0, 0];
    if (p.acabamento === "Polido" || p.retificado || a * b >= 3600) return "AC-III";
    if ((p.onde || []).includes("externa")) return "AC-II";
    return "AC-I";
  },

  qtd(l) {
    return typeof l.qtd === "function" ? l.qtd(l.produto) : l.qtd;
  },

  subtotal(l) {
    return l.produto ? l.unidades(l.produto) * Materiais.preco(l.produto) : 0;
  },

  marcada(l) {
    return !Materiais.fora.has(l.id);
  },

  // só soma as linhas marcadas
  total(lista) {
    return lista.filter(Materiais.marcada).reduce((s, l) => s + Materiais.subtotal(l), 0);
  },

  // Desenha a lista em `caixa`. `totalPiso` entra no "Total da obra". `aoMudar` é chamado quando
  // o cliente troca um produto (para atualizar o WhatsApp).
  montar(caixa, lista, totalPiso, aoMudar) {
    if (!lista.length) {
      caixa.innerHTML = "";
      return;
    }
    const nomeOpcao = (l, m) => `${l.rotulo ? l.rotulo(m) : m.nome} — ${App.dinheiro(Materiais.preco(m))}`;
    caixa.innerHTML = `<div class="materiais">
      <p class="materiais-tit">Para assentar, você vai precisar de:</p>
      <ul>${lista.map((l) => `
        <li data-linha="${l.id}" class="${Materiais.marcada(l) ? "" : "mat-off"}">
          <label class="mat-nome"><input type="checkbox" class="mat-check" ${Materiais.marcada(l) ? "checked" : ""}> ${App.esc(l.nome)}</label>
          <strong class="mat-qtd">${App.esc(Materiais.qtd(l))}</strong>
          <span class="mat-det">${App.esc(l.det)}</span>
          ${l.opcoes.length > 1
            ? `<select class="mat-prod" ${Materiais.marcada(l) ? "" : "disabled"} aria-label="Produto: ${App.esc(l.nome)}">${l.opcoes.map((m) =>
                `<option value="${m.codigo}" ${m === l.produto ? "selected" : ""}>${App.esc(nomeOpcao(l, m))}</option>`).join("")}</select>`
            : l.produto
              ? `<span class="mat-unico">${App.esc(nomeOpcao(l, l.produto))}</span>`
              : `<span class="mat-unico mat-falta">Sem estoque agora: consulte o vendedor</span>`}
          <span class="mat-sub">${l.produto ? App.dinheiro(Materiais.subtotal(l)) : ""}</span>
        </li>`).join("")}
      </ul>
      <p class="mat-totais">
        <span>${lista.some(Materiais.marcada) ? `Materiais <strong>${App.dinheiro(Materiais.total(lista))}</strong>` : "Só o piso, sem materiais"}</span>
        ${totalPiso ? `<span class="mat-obra">Total da obra <strong>${App.dinheiro(totalPiso + Materiais.total(lista))}</strong></span>` : ""}
      </p>
      <p class="materiais-aviso">Desmarque o que não quiser no orçamento. Quantidades estimadas pelas tabelas dos fabricantes; confirme com o vendedor.</p>
    </div>`;
    caixa.querySelectorAll(".mat-prod").forEach((sel) => sel.addEventListener("change", () => {
      const l = lista.find((x) => x.id === sel.closest("[data-linha]").dataset.linha);
      l.produto = l.opcoes.find((m) => m.codigo === sel.value);
      Materiais.escolhas[l.id] = l.produto.codigo;
      Materiais.montar(caixa, lista, totalPiso, aoMudar);
      if (aoMudar) aoMudar();
    }));
    caixa.querySelectorAll(".mat-check").forEach((chk) => chk.addEventListener("change", () => {
      const id = chk.closest("[data-linha]").dataset.linha;
      if (chk.checked) Materiais.fora.delete(id);
      else Materiais.fora.add(id);
      Materiais.montar(caixa, lista, totalPiso, aoMudar);
      caixa.querySelector(`[data-linha="${id}"] .mat-check`).focus();
      if (aoMudar) aoMudar();
    }));
  },

  // Texto para a mensagem do WhatsApp.
  texto(lista) {
    return lista.filter(Materiais.marcada).map((l) => l.produto
      ? `${l.produto.nome} (cód. ${l.produto.codigo}): ${Materiais.qtd(l)}`
      : `${l.nome}: ${Materiais.qtd(l)}`).join("; ");
  },
};
