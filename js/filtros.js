/* Filtros, busca e ordenação. */

const Filtros = {
  montar() {
    const pisos = App.dados.pisos;
    const valores = (campo) => [...new Set(pisos.map((p) => p[campo]).filter(Boolean))]
      .sort((a, b) => a.localeCompare(b, "pt-BR", { numeric: true }));
    const opcoes = (campo, rotulo) =>
      `<option value="">${rotulo}</option>` + valores(campo).map((v) => `<option>${App.esc(v)}</option>`).join("");

    // Categorias = os ambientes das simulações + "Parede" (revestimentos)
    const cats = [{ id: "", nome: "Todos" }, ...App.dados.ambientes, { id: "parede", nome: "Parede" }];
    const chips = cats
      .map((c) => `<button type="button" class="chip" data-cat="${c.id}" aria-pressed="${c.id === ""}">${App.esc(c.nome)}</button>`)
      .join("");

    const el = document.getElementById("filtros");
    el.innerHTML = `
      <div class="filtros-conteudo">
        <div class="filtros-linha">
          <div class="chips" role="group" aria-label="Ambiente">${chips}</div>
          <input type="search" id="f-busca" class="busca" placeholder="Buscar por nome ou código" aria-label="Buscar">
          <button type="button" id="f-mais" class="botao-mais" aria-expanded="false" aria-controls="f-extra">Mais filtros</button>
        </div>
        <div class="filtros-extra" id="f-extra">
          <select id="f-marca" aria-label="Marca">${opcoes("fabricante", "Todas as marcas")}</select>
          <select id="f-estilo" aria-label="Estilo">${opcoes("estilo", "Todos os estilos")}</select>
          <select id="f-acabamento" aria-label="Acabamento">${opcoes("acabamento", "Todos os acabamentos")}</select>
          <select id="f-formato" aria-label="Formato">${opcoes("formato", "Todos os formatos")}</select>
          <select id="f-ordem" aria-label="Ordenar">
            <option value="desconto">Maior desconto</option>
            <option value="preco">Menor preço</option>
            <option value="nome">Nome</option>
          </select>
          <label class="check"><input type="checkbox" id="f-super"> Só super ofertas</label>
          <button type="button" id="f-limpar" class="limpar">Limpar</button>
        </div>
      </div>`;

    const e = App.estado;
    el.querySelectorAll(".chip").forEach((b) => b.addEventListener("click", () => {
      e.cat = b.dataset.cat;
      // as miniaturas da grade passam a mostrar o ambiente escolhido
      if (e.cat && e.cat !== "parede") e.ambiente = e.cat;
      el.querySelectorAll(".chip").forEach((c) => c.setAttribute("aria-pressed", c === b));
      b.scrollIntoView({ block: "nearest", inline: "nearest", behavior: "smooth" });
      App.atualizar();
    }));
    let t;
    el.querySelector("#f-busca").addEventListener("input", (ev) => {
      clearTimeout(t);
      t = setTimeout(() => { e.busca = ev.target.value; App.atualizar(); }, 150);
    });
    const ligar = (id, campo) => el.querySelector(id).addEventListener("change", (ev) => {
      e[campo] = ev.target.type === "checkbox" ? ev.target.checked : ev.target.value;
      App.atualizar();
    });
    ligar("#f-marca", "marca");
    ligar("#f-estilo", "estilo");
    ligar("#f-acabamento", "acabamento");
    ligar("#f-formato", "formato");
    ligar("#f-ordem", "ordem");
    ligar("#f-super", "superOferta");

    const mais = el.querySelector("#f-mais");
    mais.addEventListener("click", () => {
      const aberto = el.classList.toggle("aberto");
      mais.setAttribute("aria-expanded", aberto);
    });
    el.querySelector("#f-limpar").addEventListener("click", Filtros.limpar);
  },

  limpar() {
    Object.assign(App.estado, { cat: "", busca: "", marca: "", estilo: "", acabamento: "", formato: "", ordem: "desconto", superOferta: false });
    const el = document.getElementById("filtros");
    el.querySelectorAll("select").forEach((s) => (s.selectedIndex = 0));
    el.querySelector("#f-busca").value = "";
    el.querySelector("#f-super").checked = false;
    el.querySelectorAll(".chip").forEach((c) => c.setAttribute("aria-pressed", c.dataset.cat === ""));
    App.atualizar();
  },

  aplicar(pisos) {
    const e = App.estado;
    const termos = App.normalizar(e.busca).split(/\s+/).filter(Boolean);
    const lista = pisos.filter((p) =>
      (!e.cat || (e.cat === "parede" ? p.onde.includes("parede") : p.ambientes.includes(e.cat))) &&
      (!e.marca || p.fabricante === e.marca) &&
      (!e.estilo || p.estilo === e.estilo) &&
      (!e.acabamento || p.acabamento === e.acabamento) &&
      (!e.formato || p.formato === e.formato) &&
      (!e.superOferta || p.superOferta) &&
      termos.every((t) => p.busca.includes(t)));
    const porNome = (a, b) => a.nome.localeCompare(b.nome, "pt-BR", { numeric: true });
    const ordens = {
      desconto: (a, b) => b.desconto - a.desconto || porNome(a, b),
      preco: (a, b) => a.preco - b.preco || porNome(a, b),
      nome: porNome,
    };
    return lista.sort(ordens[e.ordem] || ordens.desconto);
  },
};
