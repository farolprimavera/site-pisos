/* Inicialização, estado e leitura de dados. */

// Número do WhatsApp para "Pedir orçamento" (55 + DDD + número). Vazio = botão escondido.
// O mesmo número está no link do rodapé (index.html).
const WHATSAPP = "552127763391";

// Desconto mínimo (sobre o preço a prazo) para virar "super oferta".
const SUPER_OFERTA = 0.3;

const App = {
  dados: null,   // catálogo inteiro ({ atualizado, locais, ambientes, pisos })
  estado: {
    onde: "",          // chip "onde usar"
    busca: "",
    marca: "",
    estilo: "",
    acabamento: "",
    formato: "",
    ordem: "desconto",
    superOferta: false,
    ambiente: "sala",  // ambiente preferido nas miniaturas da grade
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
    });
    App.nomeAmbiente = Object.fromEntries((App.dados.ambientes || []).map((a) => [a.id, a.nome]));
    App.nomeLocal = Object.fromEntries((App.dados.locais || []).map((l) => [l.id, l.nome]));

    if (App.dados.atualizado) {
      document.getElementById("atualizado").textContent = `Preços atualizados em ${App.dados.atualizado}.`;
    }

    Vitrine.montar();
    Filtros.montar();
    App.atualizar();
    Detalhe.iniciar();
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

  img: {
    grande: (amb, id) => `imagens/${amb}/${id}.webp`,
    mini: (amb, id) => `imagens/${amb}/mini/${id}.webp`,
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

  // index.html#<id> abre direto o detalhe daquele piso.
  abrirHash() {
    const id = decodeURIComponent(location.hash.slice(1));
    if (id && App.piso(id)) Detalhe.abrir(id);
  },
};

document.addEventListener("DOMContentLoaded", App.iniciar);
