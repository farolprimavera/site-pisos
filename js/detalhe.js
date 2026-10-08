/* Modal de detalhe + calculadora + WhatsApp. */

const PERDA = 0.1;   // 10% a mais para recortes e quebras

const Detalhe = {
  iniciar() {
    const dlg = document.getElementById("detalhe");
    // clique fora do conteúdo fecha
    dlg.addEventListener("click", (ev) => { if (ev.target === dlg) dlg.close(); });
    dlg.addEventListener("close", () => {
      if (location.hash) history.replaceState(null, "", location.pathname + location.search);
    });
  },

  // Carrossel de ambientes que desliza para o lado (setas, abas, teclado e arrastar com o dedo).
  carrossel(dlg, inicio) {
    const caixa = dlg.querySelector(".amb-carrossel");
    const trilho = caixa.querySelector(".amb-trilho");
    const figs = [...trilho.children];
    const abas = [...dlg.querySelectorAll(".abas-detalhe .aba")];
    const n = figs.length;
    let atual = 0;

    const ir = (i, animar = true) => {
      atual = Math.min(Math.max(i, 0), n - 1);
      trilho.style.transition = animar ? "" : "none";
      trilho.style.transform = `translateX(${-atual * 100}%)`;
      // carrega a foto atual e as vizinhas
      figs.forEach((f, k) => {
        const img = f.querySelector("img");
        if (!img.src && Math.abs(k - atual) <= 1) img.src = img.dataset.src;
        f.setAttribute("aria-hidden", k !== atual);
      });
      abas.forEach((a, k) => a.setAttribute("aria-selected", k === atual));
      if (abas[atual]) abas[atual].scrollIntoView({ block: "nearest", inline: "nearest" });
      caixa.classList.toggle("na-peca", atual === 0);
      const conta = caixa.querySelector(".amb-conta");
      if (conta) conta.textContent = `${atual + 1} / ${n}`;
      const ant = caixa.querySelector(".seta-ant"), prox = caixa.querySelector(".seta-prox");
      if (ant) ant.disabled = atual === 0;
      if (prox) prox.disabled = atual === n - 1;
    };

    abas.forEach((a) => a.addEventListener("click", () => ir(+a.dataset.i)));
    const ant = caixa.querySelector(".seta-ant"), prox = caixa.querySelector(".seta-prox");
    if (ant) ant.addEventListener("click", () => ir(atual - 1));
    if (prox) prox.addEventListener("click", () => ir(atual + 1));
    dlg.onkeydown = (ev) => {
      if (ev.target.closest("input")) return;
      if (ev.key === "ArrowLeft") ir(atual - 1);
      if (ev.key === "ArrowRight") ir(atual + 1);
    };

    // arrastar: a foto acompanha o dedo e solta na mais próxima
    let x0 = null, dx = 0;
    trilho.addEventListener("pointerdown", (ev) => {
      if (n < 2) return;
      x0 = ev.clientX; dx = 0;
      trilho.setPointerCapture(ev.pointerId);
      trilho.style.transition = "none";
    });
    trilho.addEventListener("pointermove", (ev) => {
      if (x0 === null) return;
      dx = ev.clientX - x0;
      trilho.style.transform = `translateX(calc(${-atual * 100}% + ${dx}px))`;
    });
    const soltar = () => {
      if (x0 === null) return;
      x0 = null;
      const limite = trilho.clientWidth * 0.15;
      ir(dx < -limite ? atual + 1 : dx > limite ? atual - 1 : atual);
    };
    trilho.addEventListener("pointerup", soltar);
    trilho.addEventListener("pointercancel", soltar);

    ir(inicio, false);
  },

  abrir(id) {
    const p = App.piso(id);
    if (!p) return;
    const dlg = document.getElementById("detalhe");
    let amb = App.ambienteDo(p);
    const lugares = p.onde.map((o) => App.nomeLocal[o] || o);

    // 1º slide: a peça; depois, um slide por ambiente em que ela se aplica
    const abas = `<button type="button" class="aba" data-i="0" aria-selected="true">Peça</button>` +
      p.ambientes.map((a, i) =>
        `<button type="button" class="aba" data-i="${i + 1}" aria-selected="false">${App.esc(App.nomeAmbiente[a])}</button>`).join("");
    const slides = `
      <figure class="amb-slide slide-peca">
        <img data-src="${App.img.peca(p.id)}" alt="Peça ${App.esc(p.nome)}" draggable="false">
      </figure>` + p.ambientes.map((a) => `
      <figure class="amb-slide">
        <img data-src="${App.img.grande(a, p.id)}" alt="${App.esc(p.nome)} em ${App.esc(App.nomeAmbiente[a])}" width="1280" height="853" draggable="false">
        <figcaption>${App.esc(App.nomeAmbiente[a])}</figcaption>
      </figure>`).join("");
    const varios = p.ambientes.length > 1;

    dlg.innerHTML = `
      <div class="detalhe-conteudo">
        <button type="button" class="fechar" aria-label="Fechar">×</button>
        <div class="detalhe-fotos">
          ${amb
            ? `<div class="amb-carrossel" aria-roledescription="carrossel" aria-label="Ambientes onde ${App.esc(p.nome)} se aplica">
                 <div class="amb-trilho">${slides}</div>
                 <button type="button" class="seta seta-ant" aria-label="Foto anterior">‹</button>
                 <button type="button" class="seta seta-prox" aria-label="Próxima foto">›</button>
                 <span class="amb-conta"></span>
                 <span class="amb-dica">Veja nos ambientes ›</span>
               </div>
               <p class="amb-titulo">Aplica-se em ${p.ambientes.length} ambiente${varios ? "s" : ""}</p>
               <div class="abas abas-detalhe">${abas}</div>`
            : `<img class="detalhe-peca sozinha" src="${App.img.peca(p.id)}" alt="Peça ${App.esc(p.nome)}">`}
        </div>
        <div class="detalhe-info">
          <p class="vitrine-marca">${App.esc(p.fabricante)} · ${App.esc(p.tipo)}</p>
          <h2>${App.esc(p.nome)}</h2>
          ${Vitrine.precos(p)}

          <h3>Onde usar</h3>
          <ul class="onde">${lugares.map((l) => `<li>${App.esc(l)}</li>`).join("")}</ul>

          <h3>Ficha</h3>
          <dl class="ficha">
            <dt>Medida</dt><dd>${App.esc(p.medida)}</dd>
            <dt>Acabamento</dt><dd>${App.esc(p.acabamento)}</dd>
            <dt>Estilo</dt><dd>${App.esc(p.estilo)}</dd>
            <dt>Retificado</dt><dd>${p.retificado ? "Sim" : "Não"}</dd>
            ${p.caixa_m2 ? `<dt>Caixa</dt><dd>${String(p.caixa_m2).replace(".", ",")} m²${p.caixa_pecas ? ` · ${p.caixa_pecas} peças` : ""}</dd>` : ""}
            <dt>Código</dt><dd>${App.esc(p.codigos.join(", "))}</dd>
          </dl>

          <h3>Quanto preciso?</h3>
          <div class="calc">
            <label>Área do ambiente (m²)
              <input type="number" id="calc-m2" min="0" step="0.5" inputmode="decimal" placeholder="Ex.: 12">
            </label>
            <p id="calc-res" class="calc-res">Informe a área para calcular, já com ${PERDA * 100}% de perda.</p>
          </div>

          <div class="acoes">
            ${WHATSAPP ? `<a class="botao botao-whats" id="det-whats" target="_blank" rel="noopener">Pedir orçamento no WhatsApp</a>` : ""}
            <button type="button" class="botao botao-sec" id="det-link">Copiar link</button>
          </div>
        </div>
      </div>`;

    dlg.querySelector(".fechar").addEventListener("click", () => dlg.close());
    if (amb) Detalhe.carrossel(dlg, 0);

    const link = location.href.split("#")[0] + "#" + encodeURIComponent(p.id);
    let m2Pedido = null;
    const atualizarWhats = () => {
      const w = dlg.querySelector("#det-whats");
      if (!w) return;
      let msg = `Olá! Tenho interesse no piso ${p.nome} (${p.fabricante}, ${p.medida}, cód. ${p.codigos[0]}).`;
      if (m2Pedido) msg += ` Preciso de cerca de ${m2Pedido}.`;
      w.href = `https://wa.me/${WHATSAPP}?text=${encodeURIComponent(msg + " " + link)}`;
    };
    atualizarWhats();

    dlg.querySelector("#calc-m2").addEventListener("input", (ev) => {
      const area = parseFloat(String(ev.target.value).replace(",", "."));
      const res = dlg.querySelector("#calc-res");
      if (!(area > 0)) {
        res.textContent = `Informe a área para calcular, já com ${PERDA * 100}% de perda.`;
        m2Pedido = null;
      } else {
        const comPerda = area * (1 + PERDA);
        if (p.caixa_m2) {
          const caixas = Math.ceil(comPerda / p.caixa_m2 - 1e-9);
          const m2 = caixas * p.caixa_m2;
          res.innerHTML = `<strong>${caixas} caixa${caixas > 1 ? "s" : ""}</strong> = ${m2.toFixed(2).replace(".", ",")} m²
            <br>Total: <strong>${App.dinheiro(m2 * p.preco)}</strong>`;
          m2Pedido = `${caixas} caixas (${m2.toFixed(2).replace(".", ",")} m²)`;
        } else {
          res.innerHTML = `<strong>${comPerda.toFixed(2).replace(".", ",")} m²</strong> com perda
            <br>Total aproximado: <strong>${App.dinheiro(comPerda * p.preco)}</strong>`;
          m2Pedido = `${comPerda.toFixed(1).replace(".", ",")} m²`;
        }
      }
      atualizarWhats();
    });

    dlg.querySelector("#det-link").addEventListener("click", async (ev) => {
      const b = ev.currentTarget;
      try {
        await navigator.clipboard.writeText(link);
        b.textContent = "Link copiado!";
      } catch {
        prompt("Copie o link:", link);
      }
      setTimeout(() => (b.textContent = "Copiar link"), 2000);
    });

    if (location.hash !== "#" + encodeURIComponent(p.id)) history.replaceState(null, "", "#" + encodeURIComponent(p.id));
    if (!dlg.open) dlg.showModal();
    dlg.scrollTop = 0;
  },
};
