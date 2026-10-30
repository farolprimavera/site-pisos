/* totem.js — modo totem: depois de 2 minutos sem ninguém mexer, volta para a
   tela inicial (index.html), limpa e no topo.

   VEIO DOS SITES DE TINTAS E DE IMPERMEABILIZANTES, com o mesmo comportamento:
   2 minutos parado, aviso "Ainda está aí?" nos últimos 15 segundos e volta ao
   início. Adaptado a este site em quatro pontos (cada um explicado onde acontece):
   as cores ficam no styles.css (o site tem tema escuro), a volta ao início
   esquece o tema escolhido pelo cliente anterior, aplica versão nova do site
   se houver uma esperando, e os links copiados/QR nunca levam o ?totem=1.

   Só funciona no aparelho que foi marcado como totem, para não atrapalhar
   quem usa o site em casa:
     - abra uma vez  .../index.html?totem=1   → o aparelho vira totem
     - para desligar .../index.html?totem=0
   A marca fica guardada no navegador do aparelho (localStorage).

   Com a marca, o <html> ganha data-totem="1" e o CSS esconde o que não serve
   no aparelho da loja (Instalar app, Copiar link). O detalhe do piso mostra
   um QR code "Leve no celular" (js/detalhe.js).

   Na tela inicial limpa o contador só começa quando alguém mexe: o totem não
   fica recarregando sozinho a cada 2 minutos a noite inteira. */

(() => {
  const MINUTOS = 2;      // tempo parado até voltar ao início
  const AVISO = 15;       // segundos de aviso antes de voltar
  const CHAVE = "farol-totem";
  const INICIO = "index.html";

  // liga/desliga pelo endereço e lembra no aparelho
  let ligado = false;
  try {
    const p = new URLSearchParams(location.search).get("totem");
    if (p === "1") localStorage.setItem(CHAVE, "1");
    if (p === "0") localStorage.removeItem(CHAVE);
    ligado = localStorage.getItem(CHAVE) === "1";
  } catch (e) {
    // navegador com dados bloqueados: vale só para esta visita
    ligado = new URLSearchParams(location.search).get("totem") === "1";
  }
  if (!ligado) return;
  document.documentElement.dataset.totem = "1";

  // Piso de 1 s: com AVISO maior que o total (tempos encurtados para teste) a conta
  // daria negativo e o aviso reapareceria no instante em que é dispensado.
  const espera = Math.max(MINUTOS * 60 * 1000 - AVISO * 1000, 1000);
  let timer = null, contagem = null, aviso = null;

  /* Recarrega a página em vez de só limpar o endereço: a bandeja do Comparar, a
     metragem digitada, os materiais escolhidos e a rolagem vivem na memória, e
     recarregar é o que limpa tudo para o próximo cliente.
     O tema (claro/escuro) é preferência do cliente anterior e fica no localStorage:
     esquece antes de voltar. Se houver versão nova do site esperando, ativa agora
     (no totem ninguém toca em "Atualizar"); o pwa.js recarrega quando ela assume. */
  async function voltar() {
    try { localStorage.removeItem("tema"); } catch (e) {}
    try {
      const reg = navigator.serviceWorker && (await navigator.serviceWorker.getRegistration());
      if (reg && reg.waiting && navigator.serviceWorker.controller) {
        reg.waiting.postMessage("PULAR_ESPERA");
        setTimeout(() => location.replace(INICIO), 3000); // se o recarregamento do pwa.js não vier
        return;
      }
    } catch (e) {}
    location.replace(INICIO);
  }

  function esconderAviso() {
    clearInterval(contagem);
    contagem = null;
    if (aviso) { aviso.remove(); aviso = null; }
  }

  function mostrarAviso() {
    let resta = AVISO;
    aviso = document.createElement("div");
    aviso.className = "totem-aviso";
    aviso.setAttribute("role", "alertdialog");
    aviso.setAttribute("aria-live", "assertive");
    aviso.setAttribute("aria-labelledby", "totemTitulo");
    aviso.innerHTML = `
      <div class="totem-caixa">
        <p class="totem-titulo" id="totemTitulo">Ainda está aí?</p>
        <p class="totem-texto">Voltando para o início em <b id="totemSeg">${resta}</b> s.</p>
        <button type="button" class="botao totem-botao">Continuar aqui</button>
      </div>`;
    // por cima do detalhe/comparação abertos (<dialog> fica na camada de cima)
    (document.querySelector("dialog[open]") || document.body).appendChild(aviso);
    const botao = aviso.querySelector(".totem-botao");
    if (botao) botao.focus();
    contagem = setInterval(() => {
      resta -= 1;
      const s = document.getElementById("totemSeg");
      if (s) s.textContent = resta;
      if (resta <= 0) { clearInterval(contagem); contagem = null; voltar(); }
    }, 1000);
  }

  function armar() {
    clearTimeout(timer);
    timer = setTimeout(mostrarAviso, espera);
  }

  // Qualquer toque desarma o aviso e recomeça a contagem (o "Continuar aqui" também passa por aqui).
  function atividade() {
    if (aviso) esconderAviso();
    armar();
  }

  ["pointerdown", "touchstart", "keydown", "wheel", "scroll", "input"].forEach((ev) =>
    window.addEventListener(ev, atividade, { passive: true, capture: true }));

  // Tela inicial limpa: caminho index.html (ou a pasta) e sem nada depois do #.
  // Abrir/fechar um piso troca o # (#id do piso) e o toque que fez isso já arma o contador.
  const naInicial = /(^|\/)(index\.html)?$/.test(location.pathname) && !location.hash;
  if (!naInicial) armar();
})();
