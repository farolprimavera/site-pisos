/* Filtros, busca e ordenação. */

// Locais de uso (LU) da ficha técnica. LS não é um local_uso do site: vale para todo piso de uso externo.
const LOCAIS_USO = [
  { id: "LA", nome: "Sem tráfego", dica: "só parede" },
  { id: "LB", nome: "Pouco tráfego", dica: "quarto e sala" },
  { id: "LC", nome: "Médio tráfego", dica: "+ cozinha e banheiro" },
  { id: "LD", nome: "Alto tráfego", dica: "+ áreas cobertas e comércio leve" },
  { id: "LE", nome: "Altíssimo tráfego", dica: "comércio e tráfego intenso" },
  { id: "LS", nome: "Uso externo", dica: "quintal, calçada, piscina" },
];
const temLU = (p, lu) => (lu === "LS" ? (p.onde || []).includes("externa") : p.local_uso === lu || (lu === "LE" && p.local_uso === "LF"));

const Filtros = {
  montar() {
    const pisos = App.dados.pisos;
    const valores = (campo) => [...new Set(pisos.map((p) => p[campo]).filter(Boolean))]
      .sort((a, b) => a.localeCompare(b, "pt-BR", { numeric: true }));
    const opcoes = (campo, rotulo) =>
      `<option value="">${rotulo}</option>` + valores(campo).map((v) => `<option>${App.esc(v)}</option>`).join("");

    const el = document.getElementById("filtros");
    el.innerHTML = `
      <div class="filtros-conteudo">
        <div class="secoes" role="tablist" aria-label="Tipo de produto">
          <button type="button" class="secao-aba" role="tab" data-secao="pisos" aria-selected="true">Pisos</button>
          <button type="button" class="secao-aba" role="tab" data-secao="revestimentos" aria-selected="false">Revestimentos</button>
        </div>
        <div class="filtros-linha">
          <div class="chips" role="group" aria-label="Ambiente"></div>
          <input type="search" id="f-busca" class="busca" placeholder="Buscar por nome ou código" aria-label="Buscar">
          <button type="button" id="f-mais" class="botao-mais" aria-expanded="false" aria-controls="f-extra">Mais filtros</button>
        </div>
        <div class="filtros-extra" id="f-extra">
          <select id="f-marca" aria-label="Marca">${opcoes("fabricante", "Todas as marcas")}</select>
          <select id="f-estilo" aria-label="Estilo">${opcoes("estilo", "Todos os estilos")}</select>
          <select id="f-acabamento" aria-label="Acabamento">${opcoes("acabamento", "Todos os acabamentos")}</select>
          <select id="f-formato" aria-label="Formato">${opcoes("formato", "Todos os formatos")}</select>
          <details class="multi" id="f-lu">
            <summary>Locais de uso (LU) <span class="multi-qtd" hidden></span></summary>
            <div class="multi-lista" role="group" aria-label="Locais de uso">${LOCAIS_USO.map((l) => `
              <label class="multi-op" title="${App.esc(l.dica)}"><input type="checkbox" value="${l.id}">
                <span><b>${l.id}</b> - ${App.esc(l.nome)}</span> <span class="multi-n" data-lu="${l.id}"></span></label>`).join("")}
            </div>
          </details>
          <select id="f-ordem" aria-label="Ordenar">
            <option value="desconto">Maior desconto</option>
            <option value="preco">Menor preço</option>
            <option value="nome">Nome</option>
          </select>
          <label class="check"><input type="checkbox" id="f-super"> Só super ofertas</label>
          <label class="check" id="f-novo-label"><input type="checkbox" id="f-novo"> Só novidades <span class="multi-n" id="f-novo-n"></span></label>
          <button type="button" id="f-limpar" class="limpar">Limpar</button>
        </div>
      </div>`;

    const e = App.estado;
    el.querySelectorAll(".secao-aba").forEach((b) => b.addEventListener("click", () => Filtros.secao(b.dataset.secao)));
    Filtros.chips();
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
    ligar("#f-novo", "novidades");

    // Locais de uso: vários de uma vez (mostra o piso que tiver qualquer um dos marcados)
    const lu = el.querySelector("#f-lu");
    lu.querySelectorAll("input").forEach((c) => c.addEventListener("change", () => {
      e.lu = [...lu.querySelectorAll("input:checked")].map((x) => x.value);
      Filtros.qtdLU();
      App.atualizar();
    }));
    document.addEventListener("click", (ev) => { if (lu.open && !lu.contains(ev.target)) lu.open = false; });
    document.addEventListener("keydown", (ev) => { if (ev.key === "Escape" && lu.open) { lu.open = false; lu.querySelector("summary").focus(); } });

    const mais = el.querySelector("#f-mais");
    mais.addEventListener("click", () => {
      const aberto = el.classList.toggle("aberto");
      mais.setAttribute("aria-expanded", aberto);
    });
    el.querySelector("#f-limpar").addEventListener("click", Filtros.limpar);
  },

  // Quantos produtos da aba atual há em cada local de uso (o número cinza ao lado de cada opção).
  contarLU() {
    const revest = App.estado.secao === "revestimentos";
    const daAba = App.dados.pisos.filter((p) => (revest ? p.revest : p.ambientes.length > 0));
    document.querySelectorAll("#f-lu .multi-n").forEach((s) => {
      const n = daAba.filter((p) => temLU(p, s.dataset.lu)).length;
      s.textContent = `(${n})`;
      // sem nenhum produto nesta aba (ex.: LA em Pisos): fica apagado, a não ser que já esteja marcado
      const c = s.parentElement.querySelector("input");
      c.disabled = !n && !c.checked;
      s.parentElement.classList.toggle("multi-vazio", c.disabled);
    });
  },

  // "Só novidades" só aparece quando a aba tem alguma novidade.
  contarNovidades() {
    const revest = App.estado.secao === "revestimentos";
    const n = App.dados.pisos.filter((p) => p.novidade && (revest ? p.revest : p.ambientes.length > 0)).length;
    const lab = document.getElementById("f-novo-label");
    lab.hidden = !n && !App.estado.novidades;
    document.getElementById("f-novo-n").textContent = `(${n})`;
  },

  qtdLU() {
    const n = (App.estado.lu || []).length, q = document.querySelector("#f-lu .multi-qtd");
    q.hidden = !n;
    q.textContent = n;
  },

  // Chips de ambiente da aba atual: os ambientes de chão (Pisos) ou as paredes (Revestimentos).
  chips() {
    const e = App.estado;
    Filtros.contarLU();
    Filtros.contarNovidades();
    const lista = e.secao === "revestimentos" ? App.dados.paredes : App.dados.ambientes;
    const box = document.querySelector("#filtros .chips");
    box.innerHTML = [{ id: "", nome: "Todos" }, ...lista]
      .map((c) => `<button type="button" class="chip" data-cat="${c.id}" aria-pressed="${c.id === e.cat}">${App.esc(c.nome)}</button>`)
      .join("");
    box.querySelectorAll(".chip").forEach((b) => b.addEventListener("click", () => {
      e.cat = b.dataset.cat;
      // as miniaturas da grade passam a mostrar o ambiente (ou a parede) escolhido
      if (e.cat) e[e.secao === "revestimentos" ? "parede" : "ambiente"] = e.cat;
      box.querySelectorAll(".chip").forEach((c) => c.setAttribute("aria-pressed", c === b));
      b.scrollIntoView({ block: "nearest", inline: "nearest", behavior: "smooth" });
      App.atualizar();
    }));
  },

  // Troca a aba do topo (Pisos | Revestimentos).
  secao(s) {
    const e = App.estado;
    if (e.secao !== s) {
      e.secao = s;
      e.cat = "";
      document.querySelectorAll("#filtros .secao-aba").forEach((b) => b.setAttribute("aria-selected", b.dataset.secao === s));
      Filtros.chips();
      App.atualizar();
    }
    document.getElementById(s).scrollIntoView({ behavior: "smooth", block: "start" });
  },

  limpar() {
    Object.assign(App.estado, { cat: "", busca: "", marca: "", estilo: "", acabamento: "", formato: "", lu: [], ordem: "desconto", superOferta: false, novidades: false });
    const el = document.getElementById("filtros");
    el.querySelectorAll("select").forEach((s) => (s.selectedIndex = 0));
    el.querySelector("#f-busca").value = "";
    el.querySelector("#f-super").checked = false;
    el.querySelector("#f-novo").checked = false;
    Filtros.contarNovidades();
    el.querySelectorAll("#f-lu input").forEach((c) => (c.checked = false));
    Filtros.qtdLU();
    el.querySelectorAll(".chip").forEach((c) => c.setAttribute("aria-pressed", c.dataset.cat === ""));
    App.atualizar();
  },

  aplicar(pisos) {
    const e = App.estado;
    const termos = App.normalizar(e.busca).split(/\s+/).filter(Boolean);
    const revest = e.secao === "revestimentos";
    const lista = pisos.filter((p) =>
      (revest ? p.revest : p.ambientes.length > 0) &&
      (!e.cat || (revest ? p.paredes : p.ambientes).includes(e.cat)) &&
      (!e.marca || p.fabricante === e.marca) &&
      (!e.estilo || p.estilo === e.estilo) &&
      (!e.acabamento || p.acabamento === e.acabamento) &&
      (!e.formato || p.formato === e.formato) &&
      (!(e.lu || []).length || e.lu.some((lu) => temLU(p, lu))) &&
      (!e.superOferta || p.superOferta) &&
      (!e.novidades || p.novidade) &&
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
