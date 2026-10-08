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

  abrir(id) {
    const p = App.piso(id);
    if (!p) return;
    const dlg = document.getElementById("detalhe");
    let amb = App.ambienteDo(p);
    const lugares = p.onde.map((o) => App.nomeLocal[o] || o);

    const abas = p.ambientes.map((a) =>
      `<button type="button" class="aba" data-amb="${a}" aria-selected="${a === amb}">${App.esc(App.nomeAmbiente[a])}</button>`).join("");

    dlg.innerHTML = `
      <div class="detalhe-conteudo">
        <button type="button" class="fechar" aria-label="Fechar">×</button>
        <div class="detalhe-fotos">
          ${amb
            ? `<img id="detalhe-img" src="${App.img.grande(amb, p.id)}" alt="${App.esc(p.nome)} em ${App.esc(App.nomeAmbiente[amb])}" width="1280" height="853">
               <div class="abas abas-detalhe">${abas}</div>`
            : ""}
          <img class="detalhe-peca ${amb ? "" : "sozinha"}" src="${App.img.peca(p.id)}" alt="Peça ${App.esc(p.nome)}">
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
    dlg.querySelectorAll(".abas-detalhe .aba").forEach((b) => b.addEventListener("click", () => {
      amb = b.dataset.amb;
      dlg.querySelector("#detalhe-img").src = App.img.grande(amb, p.id);
      dlg.querySelectorAll(".abas-detalhe .aba").forEach((x) => x.setAttribute("aria-selected", x === b));
    }));

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
