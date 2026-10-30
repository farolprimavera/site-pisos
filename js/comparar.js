/* Comparar pisos lado a lado (até 3).

   - Botão "Comparar" em cada card e no detalhe do piso.
   - Bandeja fixa embaixo com os escolhidos; com 2 ou mais, abre a comparação.
   - Na comparação, todos aparecem NO MESMO AMBIENTE (troca pelas abas), com
     preço, ficha e uma calculadora única para a mesma área.
   - index.html#comparar=id1,id2,id3 abre direto a comparação (link para o WhatsApp). */

const MAX_COMPARAR = 3;

const Comparar = {
  ids: [],        // pisos escolhidos, na ordem em que foram marcados
  lugar: null,    // superfície mostrada na comparação: "chao:sala", "parede:banheiro"...
  area: "",       // área digitada na calculadora da comparação
  avisoTimer: null,

  iniciar() {
    // bandeja fixa (fica no fim do body)
    const b = document.getElementById("bandeja");
    b.addEventListener("click", (ev) => {
      const tirar = ev.target.closest("[data-tirar]");
      if (tirar) return Comparar.alternar(tirar.dataset.tirar);
      if (ev.target.closest("#band-comparar")) return Comparar.abrir();
      if (ev.target.closest("#band-limpar")) return Comparar.limpar();
    });

    const dlg = document.getElementById("comparar");
    dlg.addEventListener("click", (ev) => { if (ev.target === dlg) dlg.close(); });
    dlg.addEventListener("close", () => {
      if (location.hash.startsWith("#comparar")) App.trocarHash("");
    });

    // botão "Comparar" dos cards e do detalhe (os cards são redesenhados a cada filtro)
    document.addEventListener("click", (ev) => {
      const btn = ev.target.closest("[data-comparar]");
      if (!btn) return;
      ev.stopPropagation();   // no card, não abre o detalhe
      Comparar.alternar(btn.dataset.comparar);
    }, true);
  },

  tem(id) {
    return Comparar.ids.includes(id);
  },

  alternar(id) {
    if (Comparar.tem(id)) {
      Comparar.ids = Comparar.ids.filter((x) => x !== id);
    } else if (Comparar.ids.length >= MAX_COMPARAR) {
      Comparar.aviso(`Dá para comparar até ${MAX_COMPARAR}. Tire um para incluir outro.`);
      return;
    } else {
      Comparar.ids.push(id);
    }
    Comparar.sincronizar();
    const dlg = document.getElementById("comparar");
    if (dlg.open) Comparar.ids.length >= 2 ? Comparar.desenhar() : dlg.close();
  },

  limpar() {
    Comparar.ids = [];
    Comparar.sincronizar();
  },

  // Atualiza bandeja e todos os botões "Comparar" visíveis.
  sincronizar() {
    document.querySelectorAll("[data-comparar]").forEach((b) => {
      const on = Comparar.tem(b.dataset.comparar);
      b.setAttribute("aria-pressed", on);
      const txt = b.querySelector(".comparar-txt");
      if (txt) txt.textContent = on ? "Comparando" : "Comparar";
    });
    Comparar.bandeja();
  },

  bandeja() {
    const b = document.getElementById("bandeja");
    const n = Comparar.ids.length;
    b.hidden = n === 0;
    document.body.classList.toggle("com-bandeja", n > 0);
    if (!n) return;
    const pisos = Comparar.ids.map(App.piso).filter(Boolean);
    const vagas = Array.from({ length: MAX_COMPARAR - pisos.length }, () => `<span class="band-vaga" aria-hidden="true">+</span>`);
    b.innerHTML = `
      <div class="bandeja-conteudo">
        <div class="band-itens">
          ${pisos.map((p) => `
            <span class="band-item">
              <img src="${App.img.peca(p.id)}" alt="">
              <span class="band-nome">${App.esc(p.nome)}</span>
              <button type="button" class="band-tirar" data-tirar="${p.id}" aria-label="Tirar ${App.esc(p.nome)} da comparação">×</button>
            </span>`).join("")}
          ${vagas.join("")}
        </div>
        <div class="band-acoes">
          <button type="button" class="band-limpar" id="band-limpar">Limpar</button>
          <button type="button" class="botao band-botao" id="band-comparar" ${n < 2 ? "disabled" : ""}>
            ${n < 2 ? "Escolha mais 1" : `Comparar ${n}`}
          </button>
        </div>
      </div>
      <p class="band-aviso" id="band-aviso" role="status" hidden></p>`;
  },

  aviso(msg) {
    Comparar.bandeja();
    const a = document.getElementById("band-aviso");
    if (!a) return;
    a.textContent = msg;
    a.hidden = false;
    clearTimeout(Comparar.avisoTimer);
    Comparar.avisoTimer = setTimeout(() => (a.hidden = true), 4000);
  },

  // Superfícies que dá para mostrar: ambientes de chão e paredes de qualquer um dos escolhidos.
  // Fica primeiro o que serve para todos; o padrão é o primeiro comum.
  lugares(pisos) {
    const lista = [
      ...App.dados.ambientes.map((a) => ({ id: `chao:${a.id}`, amb: a.id, parede: false, nome: a.nome })),
      ...App.dados.paredes.map((a) => ({ id: `parede:${a.id}`, amb: a.id, parede: true, nome: `${a.nome} · parede` })),
    ];
    const serve = (p, l) => (l.parede ? p.paredes : p.ambientes).includes(l.amb);
    return lista
      .map((l) => ({ ...l, todos: pisos.every((p) => serve(p, l)), algum: pisos.some((p) => serve(p, l)) }))
      .filter((l) => l.algum)
      .sort((a, b) => b.todos - a.todos);
  },

  abrir() {
    if (Comparar.ids.length < 2) return;
    Comparar.lugar = null;
    Comparar.desenhar();
    const dlg = document.getElementById("comparar");
    const hash = "#comparar=" + Comparar.ids.map(encodeURIComponent).join(",");
    if (location.hash !== hash) App.trocarHash(hash);
    if (!dlg.open) dlg.showModal();
    dlg.scrollTop = 0;
  },

  // Chamado por App.abrirHash com "comparar=id1,id2".
  doHash(valor) {
    const ids = valor.split(",").map(decodeURIComponent).filter((id) => App.piso(id)).slice(0, MAX_COMPARAR);
    if (ids.length < 2) return;
    Comparar.ids = ids;
    Comparar.sincronizar();
    Comparar.abrir();
  },

  desenhar() {
    const dlg = document.getElementById("comparar");
    const pisos = Comparar.ids.map(App.piso).filter(Boolean);
    const lugares = Comparar.lugares(pisos);
    // mantém a aba escolhida; senão, a do filtro atual, se servir para todos; senão a primeira
    const preferido = App.estado.secao === "revestimentos" ? `parede:${App.estado.parede}` : `chao:${App.estado.ambiente}`;
    if (!lugares.some((l) => l.id === Comparar.lugar)) {
      const pref = lugares.find((l) => l.id === preferido && l.todos);
      Comparar.lugar = (pref || lugares[0] || {}).id || null;
    }
    const lugar = lugares.find((l) => l.id === Comparar.lugar);

    const precos = pisos.map((p) => p.preco).filter((v) => v > 0);
    const menor = precos.length > 1 ? Math.min(...precos) : null;
    const col = (fn) => pisos.map((p) => `<td>${fn(p)}</td>`).join("");
    const linha = (rotulo, fn) =>
      `<tr class="cmp-rotulo"><th colspan="${pisos.length}" scope="colgroup"><span>${rotulo}</span></th></tr><tr>${col(fn)}</tr>`;

    const foto = (p) => {
      if (!lugar) return `<div class="cmp-foto cmp-so-peca"><img src="${App.img.peca(p.id)}" alt="Peça ${App.esc(p.nome)}"></div>`;
      const serve = (lugar.parede ? p.paredes : p.ambientes).includes(lugar.amb);
      if (!serve) {
        return `<div class="cmp-foto cmp-so-peca">
          <img src="${App.img.peca(p.id)}" alt="Peça ${App.esc(p.nome)}">
          <span class="cmp-nao">Não indicado para ${App.esc(lugar.nome.replace(" · parede", lugar.parede ? " (parede)" : ""))}</span>
        </div>`;
      }
      const src = lugar.parede ? App.img.parede(lugar.amb, p.id) : App.img.grande(lugar.amb, p.id);
      return `<div class="cmp-foto">
        <img src="${src}" alt="${App.esc(p.nome)} em ${App.esc(lugar.nome)}" width="1280" height="853">
        <img class="peca-mini" src="${App.img.peca(p.id)}" alt="">
      </div>`;
    };

    const preco = (p) => {
      const selo = menor !== null && p.preco === menor ? `<span class="cmp-melhor">Menor preço</span>` : "";
      return `${selo}${Vitrine.precos(p)}`;
    };
    const onde = (p) => `<ul class="onde">${p.onde.map((o) => `<li>${App.esc(App.nomeLocal[o] || o)}</li>`).join("")}</ul>`;
    const caixa = (p) => p.caixa_m2
      ? `${String(p.caixa_m2).replace(".", ",")} m²${p.caixa_pecas ? ` · ${p.caixa_pecas} peças` : ""}`
      : "—";

    dlg.innerHTML = `
      <div class="cmp-conteudo">
        <div class="cmp-topo">
          <h2>Comparar ${pisos.length} ${pisos.some((p) => p.tipo === "Piso") ? "pisos" : "revestimentos"}</h2>
          <button type="button" class="fechar cmp-fechar" aria-label="Fechar">×</button>
        </div>
        ${lugares.length ? `
        <div class="cmp-lugares">
          <span class="cmp-lugares-rot">Ver todos em:</span>
          <div class="abas cmp-abas">
            ${lugares.map((l) => `<button type="button" class="aba" data-lugar="${l.id}" aria-selected="${l.id === Comparar.lugar}"
                ${l.todos ? "" : 'title="Nem todos servem para este ambiente"'}>${App.esc(l.nome)}${l.todos ? "" : " *"}</button>`).join("")}
          </div>
          ${lugares.some((l) => !l.todos) ? `<p class="cmp-nota">* nem todos os escolhidos são indicados para esse ambiente</p>` : ""}
        </div>` : ""}

        <div class="cmp-rolagem">
          <table class="cmp-tabela" style="--cols:${pisos.length}">
            <thead>
              <tr>${col(foto)}</tr>
              <tr class="cmp-nomes">${pisos.map((p) => `<th scope="col">
                <span class="vitrine-marca">${App.esc(p.fabricante)} · ${App.esc(p.tipo)}</span>
                <span class="cmp-nome">${App.esc(p.nome)}</span>
                <span class="cmp-medida">${App.esc(p.medida)}</span>
              </th>`).join("")}</tr>
            </thead>
            <tbody>
              ${linha("Preço por m²", preco)}
              ${linha("Onde usar", onde)}
              ${linha("Acabamento", (p) => App.esc(p.acabamento))}
              ${linha("Estilo", (p) => App.esc(p.estilo))}
              ${linha("Retificado", (p) => (p.retificado ? "Sim" : "Não"))}
              ${linha("Caixa", caixa)}
              ${linha("Código", (p) => App.esc(p.codigos.join(", ")))}
              <tr class="cmp-rotulo"><th colspan="${pisos.length}" scope="colgroup"><span>Quanto fica para a sua obra?</span></th></tr>
              <tr class="cmp-calc-linha">
                <td colspan="${pisos.length}"><div class="cmp-calc-caixa">
                  <label class="cmp-calc">Área a cobrir (m²)
                    <input type="number" id="cmp-area" min="0" step="0.5" inputmode="decimal" placeholder="Ex.: 12" value="${App.esc(Comparar.area)}">
                  </label>
                  <span class="cmp-calc-dica">Já com ${PERDA * 100}% de perda para recortes.</span>
                </div></td>
              </tr>
              <tr class="cmp-totais">${col((p) => `<span class="cmp-total" data-total="${p.id}">—</span>`)}</tr>
              <tr class="cmp-acoes-linha">${col((p) => `
                <button type="button" class="botao botao-sec cmp-ver" data-ver="${p.id}">Ver detalhes</button>
                <button type="button" class="cmp-tirar" data-tirar-cmp="${p.id}">Tirar da comparação</button>`)}</tr>
            </tbody>
          </table>
        </div>

        <div class="acoes cmp-rodape">
          <p class="totem-vendedor">Gostou? Chame um vendedor para fechar o orçamento.</p>
          ${WHATSAPP ? `<a class="botao botao-whats" id="cmp-whats" target="_blank" rel="noopener">Pedir orçamento dos ${pisos.length} no WhatsApp</a>` : ""}
          <button type="button" class="botao botao-sec" id="cmp-link">Copiar link da comparação</button>
        </div>
      </div>`;

    dlg.querySelector(".cmp-fechar").addEventListener("click", () => dlg.close());
    dlg.querySelectorAll("[data-lugar]").forEach((b) => b.addEventListener("click", () => {
      Comparar.lugar = b.dataset.lugar;
      const rolar = dlg.scrollTop;
      Comparar.desenhar();
      dlg.scrollTop = rolar;
    }));
    dlg.querySelectorAll("[data-ver]").forEach((b) => b.addEventListener("click", () => Detalhe.abrir(b.dataset.ver)));
    dlg.querySelectorAll("[data-tirar-cmp]").forEach((b) => b.addEventListener("click", () => Comparar.alternar(b.dataset.tirarCmp)));

    const link = App.link("#comparar=") + Comparar.ids.map(encodeURIComponent).join(",");
    const calcular = () => {
      Comparar.area = dlg.querySelector("#cmp-area").value;
      const area = parseFloat(String(Comparar.area).replace(",", "."));
      const linhas = [];
      pisos.forEach((p) => {
        const el = dlg.querySelector(`[data-total="${p.id}"]`);
        if (!(area > 0)) {
          el.textContent = "Informe a área";
          el.classList.add("cmp-total-vazio");
          linhas.push(`• ${p.nome} (${p.fabricante}, ${p.medida}, cód. ${p.codigos[0]})`);
          return;
        }
        el.classList.remove("cmp-total-vazio");
        const comPerda = area * (1 + PERDA);
        if (p.caixa_m2) {
          const caixas = Math.ceil(comPerda / p.caixa_m2 - 1e-9);
          const m2 = caixas * p.caixa_m2;
          el.innerHTML = `<strong>${caixas} caixa${caixas > 1 ? "s" : ""}</strong> · ${m2.toFixed(2).replace(".", ",")} m²
            <span class="cmp-total-valor">${App.dinheiro(m2 * p.preco)}</span>`;
          linhas.push(`• ${p.nome} (${p.fabricante}, ${p.medida}, cód. ${p.codigos[0]}): ${caixas} caixas`);
        } else {
          el.innerHTML = `<strong>${comPerda.toFixed(2).replace(".", ",")} m²</strong>
            <span class="cmp-total-valor">${App.dinheiro(comPerda * p.preco)}</span>`;
          linhas.push(`• ${p.nome} (${p.fabricante}, ${p.medida}, cód. ${p.codigos[0]}): ${comPerda.toFixed(1).replace(".", ",")} m²`);
        }
      });
      // destaca quem sai mais barato para a obra inteira (o preço/m² sozinho engana: a caixa muda de tamanho)
      dlg.querySelectorAll(".cmp-mais-barato").forEach((e) => e.remove());
      if (area > 0 && pisos.length > 1) {
        const totais = pisos.map((p) => {
          const comPerda = area * (1 + PERDA);
          return p.caixa_m2 ? Math.ceil(comPerda / p.caixa_m2 - 1e-9) * p.caixa_m2 * p.preco : comPerda * p.preco;
        });
        const min = Math.min(...totais.filter((t) => t > 0));
        pisos.forEach((p, i) => {
          if (totais[i] > 0 && Math.abs(totais[i] - min) < 0.005) {
            dlg.querySelector(`[data-total="${p.id}"]`)
              .insertAdjacentHTML("afterbegin", `<span class="cmp-melhor cmp-mais-barato">Mais em conta para a obra</span>`);
          }
        });
      }
      const w = dlg.querySelector("#cmp-whats");
      if (w) {
        const area_txt = area > 0 ? ` para cerca de ${String(area).replace(".", ",")} m²` : "";
        const msg = `Olá! Estou comparando estes pisos${area_txt}:\n${linhas.join("\n")}\n${link}`;
        w.href = `https://wa.me/${WHATSAPP}?text=${encodeURIComponent(msg)}`;
      }
    };
    dlg.querySelector("#cmp-area").addEventListener("input", calcular);
    calcular();

    dlg.querySelector("#cmp-link").addEventListener("click", async (ev) => {
      const b = ev.currentTarget;
      try {
        await navigator.clipboard.writeText(link);
        b.textContent = "Link copiado!";
      } catch {
        prompt("Copie o link:", link);
      }
      setTimeout(() => (b.textContent = "Copiar link da comparação"), 2000);
    });
  },
};
