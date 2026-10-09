/* Grade de produtos (pisos e revestimentos). */

const POR_PAGINA = 12;   // cards por página (3 fileiras de 4 no computador)

const Cards = {
  listas: {},   // itens filtrados de cada seção
  paginas: {},  // página atual de cada seção

  // Chamado a cada mudança de filtro: mostra só a seção da aba atual, na página 1.
  desenhar(lista) {
    const secao = App.estado.secao;
    Cards.listas[secao] = lista;
    Cards.paginas[secao] = 1;
    Cards.pagina(secao);
    document.getElementById("pisos").hidden = secao !== "pisos";
    document.getElementById("revestimentos").hidden = secao !== "revestimentos";
  },

  // Desenha a página atual de uma seção ("pisos" ou "revestimentos").
  pagina(secao) {
    const itens = Cards.listas[secao];
    const total = Math.max(1, Math.ceil(itens.length / POR_PAGINA));
    const n = Math.min(Math.max(Cards.paginas[secao], 1), total);
    Cards.paginas[secao] = n;
    const fatia = itens.slice((n - 1) * POR_PAGINA, n * POR_PAGINA);
    const fn = secao === "pisos" ? Cards.cardPiso : Cards.cardRevest;

    document.getElementById(`contagem-${secao}`).textContent = itens.length === 1 ? "1 item" : `${itens.length} itens`;
    const grade = document.getElementById(`grade-${secao}`);
    grade.innerHTML = fatia.length ? fatia.map(fn).join("") : `<p class="vazio">Nada encontrado com esses filtros.</p>`;
    grade.querySelectorAll("[data-id]").forEach((c) => c.addEventListener("click", () => Detalhe.abrir(c.dataset.id)));

    const nav = document.getElementById(`paginas-${secao}`);
    nav.innerHTML = total > 1 ? Cards.botoes(n, total) : "";
    nav.querySelectorAll("[data-pag]").forEach((b) => b.addEventListener("click", () => {
      Cards.paginas[secao] = +b.dataset.pag;
      Cards.pagina(secao);
      document.getElementById(secao).scrollIntoView({ behavior: "smooth", block: "start" });
    }));
  },

  // ‹ Anterior  1 … 4 5 6 … 12  Próxima ›
  botoes(n, total) {
    const nums = [...new Set([1, n - 1, n, n + 1, total])].filter((k) => k >= 1 && k <= total).sort((a, b) => a - b);
    let html = `<button type="button" class="pag pag-seta" data-pag="${n - 1}" ${n === 1 ? "disabled" : ""} aria-label="Página anterior">‹ <span>Anterior</span></button>`;
    nums.forEach((k, i) => {
      if (i && k - nums[i - 1] > 1) html += `<span class="pag-reti">…</span>`;
      html += `<button type="button" class="pag" data-pag="${k}" ${k === n ? 'aria-current="page"' : ""} aria-label="Página ${k}">${k}</button>`;
    });
    html += `<button type="button" class="pag pag-seta" data-pag="${n + 1}" ${n === total ? "disabled" : ""} aria-label="Próxima página"><span>Próxima</span> ›</button>`;
    return html;
  },

  preco(p) {
    return p.oferta
      ? `<span class="card-preco oferta">${App.dinheiro(p.oferta)}<small>/m²</small></span><span class="card-de">${App.dinheiro(p.prazo)}</span>`
      : `<span class="card-preco">${App.dinheiro(p.vista)}<small>/m²</small></span>`;
  },

  selo(p) {
    if (p.superOferta) return `<span class="selo">-${Math.round(p.desconto * 100)}%</span>`;
    if (p.oferta) return `<span class="selo selo-leve">Oferta</span>`;
    return "";
  },

  cardPiso(p) {
    const amb = App.ambienteDo(p);
    return `<article class="card" data-id="${p.id}" tabindex="0">
      <div class="card-foto">
        <img class="card-amb" src="${App.img.mini(amb, p.id)}" data-amb="${amb}" alt="${App.esc(p.nome)} em ${App.esc(App.nomeAmbiente[amb])}" loading="lazy" width="520" height="347">
        <img class="peca-mini" src="${App.img.peca(p.id)}" alt="" loading="lazy">
        ${Cards.selo(p)}
      </div>
      <div class="card-texto">
        <h3>${App.esc(p.nome)}</h3>
        <p class="card-sub">${App.esc(p.fabricante)} · ${App.esc(p.medida)}</p>
        <p class="card-precos">${Cards.preco(p)}</p>
      </div>
    </article>`;
  },

  // Revestimento: a parede com ele aplicado e a peça no canto (sem parede simulada, só a peça).
  cardRevest(p) {
    const par = App.paredeDo(p);
    const foto = par
      ? `<div class="card-foto">
          <img class="card-amb card-parede" src="${App.img.paredeMini(par, p.id)}" alt="${App.esc(p.nome)} na parede: ${App.esc(App.nomeParede[par])}" loading="lazy" width="520" height="416">
          <img class="peca-mini" src="${App.img.peca(p.id)}" alt="" loading="lazy">
          ${Cards.selo(p)}
        </div>`
      : `<div class="card-foto foto-peca">
          <img src="${App.img.peca(p.id)}" alt="${App.esc(p.nome)}" loading="lazy">
          ${Cards.selo(p)}
        </div>`;
    return `<article class="card card-revest" data-id="${p.id}" tabindex="0">
      ${foto}
      <div class="card-texto">
        <h3>${App.esc(p.nome)}</h3>
        <p class="card-sub">${App.esc(p.fabricante)} · ${App.esc(p.medida)}</p>
        <p class="card-precos">${Cards.preco(p)}</p>
      </div>
    </article>`;
  },
};

// Enter no card (teclado) abre o detalhe.
document.addEventListener("keydown", (ev) => {
  const card = ev.target.closest && ev.target.closest(".card");
  if (card && ev.key === "Enter" && ev.target === card) Detalhe.abrir(card.dataset.id);
});
