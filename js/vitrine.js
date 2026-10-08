/* Vitrine: carrossel de ambientes com pisos sorteados. Clicar no slide abre a página do piso. */

const SLIDES = 8;          // quantas fotos no carrossel
const INTERVALO = 10000;   // troca sozinho depois de 10 s sem interação

const Vitrine = {
  slides: [],
  atual: 0,
  timer: null,

  // Sorteia um piso para cada ambiente (ambientes também em ordem aleatória), sem repetir piso.
  sortear() {
    const embaralhar = (a) => {
      for (let i = a.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [a[i], a[j]] = [a[j], a[i]];
      }
      return a;
    };
    const usados = new Set();
    const out = [];
    for (const amb of embaralhar([...App.dados.ambientes])) {
      const opcoes = App.dados.pisos.filter((p) => p.ambientes.includes(amb.id) && !usados.has(p.id));
      if (!opcoes.length) continue;
      const p = opcoes[Math.floor(Math.random() * opcoes.length)];
      usados.add(p.id);
      out.push({ amb: amb.id, piso: p });
      if (out.length === SLIDES) break;
    }
    return out;
  },

  montar() {
    const el = document.getElementById("vitrine");
    Vitrine.slides = Vitrine.sortear();
    if (!Vitrine.slides.length) {
      el.hidden = true;
      return;
    }

    const slides = Vitrine.slides.map(({ amb, piso: p }, i) => `
      <a class="slide" href="#${encodeURIComponent(p.id)}" data-i="${i}" aria-hidden="${i !== 0}" tabindex="${i === 0 ? 0 : -1}"
         aria-label="${App.esc(p.nome)} em ${App.esc(App.nomeAmbiente[amb])} — ver piso">
        <img data-src="${App.img.grande(amb, p.id)}" alt="${App.esc(p.nome)} aplicado em ${App.esc(App.nomeAmbiente[amb])}" width="1280" height="853">
        <span class="slide-legenda">
          <span class="slide-amb">${App.esc(App.nomeAmbiente[amb])}</span>
          <strong class="slide-nome">${App.esc(p.nome)}</strong>
          <span class="slide-ver">${App.esc(p.fabricante)} · ${App.esc(p.medida)} · Ver piso →</span>
        </span>
      </a>`).join("");
    const pontos = Vitrine.slides.map((_, i) =>
      `<button type="button" class="ponto" data-i="${i}" aria-label="Foto ${i + 1}" aria-current="${i === 0}"></button>`).join("");

    el.innerHTML = `
      <div class="carrossel" aria-roledescription="carrossel" aria-label="Ambientes com nossos pisos">
        <div class="slides">${slides}</div>
        <button type="button" class="seta seta-ant" aria-label="Foto anterior">‹</button>
        <button type="button" class="seta seta-prox" aria-label="Próxima foto">›</button>
        <div class="pontos">${pontos}</div>
      </div>`;

    el.querySelector(".seta-ant").addEventListener("click", () => Vitrine.ir(Vitrine.atual - 1));
    el.querySelector(".seta-prox").addEventListener("click", () => Vitrine.ir(Vitrine.atual + 1));
    el.querySelectorAll(".ponto").forEach((b) => b.addEventListener("click", () => Vitrine.ir(+b.dataset.i)));

    // arrastar para o lado no celular
    const area = el.querySelector(".slides");
    let x0 = null, arrastou = false;
    area.addEventListener("pointerdown", (ev) => { x0 = ev.clientX; arrastou = false; });
    area.addEventListener("pointerup", (ev) => {
      if (x0 === null) return;
      const dx = ev.clientX - x0;
      x0 = null;
      if (Math.abs(dx) > 40) {
        arrastou = true;
        Vitrine.ir(Vitrine.atual + (dx < 0 ? 1 : -1));
      }
    });
    area.addEventListener("click", (ev) => { if (arrastou) ev.preventDefault(); });
    area.addEventListener("dragstart", (ev) => ev.preventDefault());

    el.addEventListener("keydown", (ev) => {
      if (ev.key === "ArrowLeft") Vitrine.ir(Vitrine.atual - 1);
      if (ev.key === "ArrowRight") Vitrine.ir(Vitrine.atual + 1);
    });
    document.addEventListener("visibilitychange", Vitrine.agendar);

    Vitrine.ir(0);
  },

  // Mostra o slide i e já carrega o próximo, para a troca ser instantânea.
  ir(i) {
    const n = Vitrine.slides.length;
    Vitrine.atual = ((i % n) + n) % n;
    const el = document.getElementById("vitrine");
    el.querySelectorAll(".slide").forEach((s, k) => {
      const ativo = k === Vitrine.atual;
      s.classList.toggle("ativo", ativo);
      s.setAttribute("aria-hidden", !ativo);
      s.tabIndex = ativo ? 0 : -1;
      const img = s.querySelector("img");
      if (!img.src && (ativo || k === (Vitrine.atual + 1) % n)) img.src = img.dataset.src;
    });
    el.querySelectorAll(".ponto").forEach((b, k) => b.setAttribute("aria-current", k === Vitrine.atual));
    Vitrine.agendar();
  },

  // Qualquer troca (automática ou do cliente) recomeça a contagem de 10 s.
  agendar() {
    clearTimeout(Vitrine.timer);
    if (!document.hidden) Vitrine.timer = setTimeout(() => Vitrine.ir(Vitrine.atual + 1), INTERVALO);
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
};
