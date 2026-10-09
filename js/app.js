/* Inicialização, estado e leitura de dados. */

// Número do WhatsApp para "Pedir orçamento" (55 + DDD + número). Vazio = botão escondido.
// O mesmo número está no link do rodapé (index.html).
const WHATSAPP = "552127763391";

// Desconto mínimo (sobre o preço a prazo) para virar "super oferta".
const SUPER_OFERTA = 0.3;

const App = {
  dados: null,   // catálogo inteiro ({ atualizado, locais, ambientes, pisos })
  estado: {
    secao: "pisos",    // aba do topo: "pisos" ou "revestimentos"
    cat: "",           // chip de ambiente ("sala", "quintal-piscina"...; em revestimentos, "banheiro"...)
    busca: "",
    marca: "",
    estilo: "",
    acabamento: "",
    formato: "",
    ordem: "desconto",
    superOferta: false,
    ambiente: "sala",  // ambiente preferido nas miniaturas da grade
    parede: "banheiro", // parede preferida nas miniaturas de revestimento
  },

  // Lê window.PISOS (dados/pisos.js); fetch do .json só como plano B.
  async carregar() {
    if (window.PISOS) return window.PISOS;
    const resp = await fetch("dados/pisos.json");
    return resp.json();
  },

  async iniciar() {
    App.dados = await App.carregar();
    App.dados.pisos.forEach((p) => {
      p.preco = p.oferta || p.vista || p.prazo || 0;
      p.desconto = p.oferta && p.prazo ? 1 - p.oferta / p.prazo : 0;
      p.superOferta = p.desconto >= SUPER_OFERTA;
      p.busca = App.normalizar([p.nome, p.fabricante, p.estilo, p.acabamento, p.formato, ...p.codigos].join(" "));
      p.paredes = p.paredes || [];
      // revestimento = vai na parede (LA ou piso que também é parede); fica na aba Revestimentos
      p.revest = p.paredes.length > 0 || !p.ambientes.length;
    });
    App.dados.paredes = App.dados.paredes || [];
    App.nomeAmbiente = Object.fromEntries((App.dados.ambientes || []).map((a) => [a.id, a.nome]));
    App.nomeParede = Object.fromEntries(App.dados.paredes.map((a) => [a.id, a.nome]));
    App.nomeLocal = Object.fromEntries((App.dados.locais || []).map((l) => [l.id, l.nome]));

    if (App.dados.atualizado) {
      document.getElementById("atualizado").textContent = `Preços atualizados em ${App.dados.atualizado}.`;
    }

    Vitrine.montar();
    Filtros.montar();
    App.atualizar();
    Detalhe.iniciar();
    document.getElementById("tema").addEventListener("click", App.trocarTema);
    window.addEventListener("hashchange", App.abrirHash);
    App.abrirHash();
  },

  // Redesenha tudo o que depende dos filtros.
  atualizar() {
    Cards.desenhar(Filtros.aplicar(App.dados.pisos));
  },

  piso(id) {
    return App.dados.pisos.find((p) => p.id === id);
  },

  // Ambiente a mostrar para um piso: o escolhido, se o piso servir para ele; senão o primeiro que serve.
  ambienteDo(p) {
    if (!p.ambientes.length) return null;
    return p.ambientes.includes(App.estado.ambiente) ? App.estado.ambiente : p.ambientes[0];
  },

  // O mesmo para a parede: a escolhida, se o produto for para ela; senão a primeira.
  paredeDo(p) {
    if (!p.paredes.length) return null;
    return p.paredes.includes(App.estado.parede) ? App.estado.parede : p.paredes[0];
  },

  img: {
    grande: (amb, id) => `imagens/${amb}/${id}.webp`,
    mini: (amb, id) => `imagens/${amb}/mini/${id}.webp`,
    parede: (amb, id) => `imagens/${amb}/parede/${id}.webp`,
    paredeMini: (amb, id) => `imagens/${amb}/parede/mini/${id}.webp`,
    peca: (id) => `imagens/pecas/${id}.webp`,
  },

  dinheiro(v) {
    return v == null ? "—" : v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
  },

  normalizar(s) {
    return String(s).toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");
  },

  esc(s) {
    return String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
  },

  // Alterna claro/escuro. Sem escolha salva, o tema segue o do sistema (ver index.html).
  trocarTema() {
    const raiz = document.documentElement;
    const escuroAgora = raiz.dataset.tema
      ? raiz.dataset.tema === "escuro"
      : matchMedia("(prefers-color-scheme: dark)").matches;
    raiz.dataset.tema = escuroAgora ? "claro" : "escuro";
    try {
      localStorage.setItem("tema", raiz.dataset.tema);
    } catch (e) {}
  },

  // index.html#<id> abre direto o detalhe daquele piso.
  abrirHash() {
    const id = decodeURIComponent(location.hash.slice(1));
    if (id === "pisos" || id === "revestimentos") return Filtros.secao(id);
    if (id && App.piso(id)) Detalhe.abrir(id);
  },
};

document.addEventListener("DOMContentLoaded", App.iniciar);
