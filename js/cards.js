/* Grade de produtos (pisos e revestimentos). */

const Cards = {
  desenhar(lista) {
    const pisos = lista.filter((p) => p.ambientes.length);
    const revest = lista.filter((p) => !p.ambientes.length);
    Cards.preencher("grade-pisos", "contagem-pisos", pisos, Cards.cardPiso);
    Cards.preencher("grade-revestimentos", "contagem-revestimentos", revest, Cards.cardRevest);
    document.getElementById("revestimentos").hidden = !revest.length;
    document.getElementById("pisos").hidden = !pisos.length && revest.length > 0;
  },

  preencher(gradeId, contId, itens, fn) {
    const grade = document.getElementById(gradeId);
    document.getElementById(contId).textContent = itens.length === 1 ? "1 item" : `${itens.length} itens`;
    grade.innerHTML = itens.length ? itens.map(fn).join("") : `<p class="vazio">Nada encontrado com esses filtros.</p>`;
    grade.querySelectorAll("[data-id]").forEach((c) => c.addEventListener("click", (ev) => {
      if (ev.target.closest(".card-ver")) Vitrine.mostrar(c.dataset.id);
      else Detalhe.abrir(c.dataset.id);
    }));
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
        <button type="button" class="card-ver" title="Ver em destaque" aria-label="Ver ${App.esc(p.nome)} em destaque">⤢</button>
      </div>
      <div class="card-texto">
        <h3>${App.esc(p.nome)}</h3>
        <p class="card-sub">${App.esc(p.fabricante)} · ${App.esc(p.medida)}</p>
        <p class="card-precos">${Cards.preco(p)}</p>
      </div>
    </article>`;
  },

  cardRevest(p) {
    return `<article class="card card-revest" data-id="${p.id}" tabindex="0">
      <div class="card-foto foto-peca">
        <img src="${App.img.peca(p.id)}" alt="${App.esc(p.nome)}" loading="lazy">
        ${Cards.selo(p)}
      </div>
      <div class="card-texto">
        <h3>${App.esc(p.nome)}</h3>
        <p class="card-sub">${App.esc(p.fabricante)} · ${App.esc(p.medida)}</p>
        <p class="card-precos">${Cards.preco(p)}</p>
      </div>
    </article>`;
  },

  // Troca só a miniatura de ambiente (sem redesenhar a grade inteira).
  trocarAmbiente() {
    document.querySelectorAll("#grade-pisos .card").forEach((c) => {
      const p = App.piso(c.dataset.id);
      const amb = App.ambienteDo(p);
      const img = c.querySelector(".card-amb");
      if (img.dataset.amb !== amb) {
        img.dataset.amb = amb;
        img.src = App.img.mini(amb, p.id);
        img.alt = `${p.nome} em ${App.nomeAmbiente[amb]}`;
      }
    });
  },
};

// Enter no card (teclado) abre o detalhe.
document.addEventListener("keydown", (ev) => {
  const card = ev.target.closest && ev.target.closest(".card");
  if (card && ev.key === "Enter" && ev.target === card) Detalhe.abrir(card.dataset.id);
});
