/* Vitrine: destaque grande + abas de ambiente. */

const Vitrine = {
  desenhar() {
    const el = document.getElementById("vitrine");
    const p = App.piso(App.estado.pisoId);
    if (!p) {
      el.innerHTML = `<div class="vitrine-vazia">Nenhum piso encontrado com esses filtros.</div>`;
      return;
    }
    const amb = App.ambienteDo(p);
    const abas = App.dados.ambientes.map((a) => {
      const ok = p.ambientes.includes(a.id);
      return `<button type="button" class="aba" role="tab" data-amb="${a.id}" aria-selected="${a.id === amb}"
        ${ok ? "" : 'disabled title="Este piso não é indicado para este ambiente"'}>${App.esc(a.nome)}</button>`;
    }).join("");

    el.innerHTML = `
      <div class="vitrine-conteudo">
        <div class="vitrine-foto">
          <img id="vitrine-img" src="${App.img.grande(amb, p.id)}" alt="${App.esc(p.nome)} aplicado em ${App.esc(App.nomeAmbiente[amb])}" width="1280" height="853">
          <img class="vitrine-peca" src="${App.img.peca(p.id)}" alt="Peça ${App.esc(p.nome)}">
          ${p.superOferta ? '<span class="selo selo-grande">Super oferta</span>' : ""}
        </div>
        <div class="abas" role="tablist" aria-label="Ver em outro ambiente">${abas}</div>
        <aside class="vitrine-info">
          <p class="vitrine-marca">${App.esc(p.fabricante)} · ${App.esc(p.tipo)}</p>
          <h1 class="vitrine-nome">${App.esc(p.nome)}</h1>
          <p class="vitrine-medida">${App.esc(p.medida)} · ${App.esc(p.acabamento)} · ${App.esc(p.estilo)}</p>
          ${Vitrine.precos(p)}
          <button type="button" class="botao" id="vitrine-detalhe">Ver detalhes e calcular</button>
        </aside>
      </div>`;

    el.querySelectorAll(".aba:not([disabled])").forEach((b) => b.addEventListener("click", () => {
      App.estado.ambiente = b.dataset.amb;
      Vitrine.desenhar();
      Cards.trocarAmbiente();
    }));
    el.querySelector("#vitrine-detalhe").addEventListener("click", () => Detalhe.abrir(p.id));
  },

  precos(p) {
    const oferta = p.oferta
      ? `<p class="preco-oferta"><span>Oferta</span> ${App.dinheiro(p.oferta)}<small>/m²</small></p>`
      : "";
    return `<div class="precos">
      ${oferta}
      <p class="${p.oferta ? "preco-riscado" : "preco-principal"}">À vista ${App.dinheiro(p.vista)}<small>/m²</small></p>
      <p class="preco-prazo">A prazo ${App.dinheiro(p.prazo)}/m²</p>
      ${p.desconto ? `<p class="desconto">${Math.round(p.desconto * 100)}% de desconto sobre o preço a prazo</p>` : ""}
    </div>`;
  },

  // Chamado pelos cards: troca o piso em destaque e sobe a tela até ele.
  mostrar(id) {
    App.estado.pisoId = id;
    Vitrine.desenhar();
    document.getElementById("vitrine").scrollIntoView({ behavior: "smooth", block: "start" });
  },
};
