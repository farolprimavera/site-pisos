/* Instalar como aplicativo: registro do service worker (sw.js), botão
   "Instalar app" e aviso de versão nova.

   Abrindo o index.html com dois cliques (file://) nada disto roda e o site
   funciona igual, só não instala. O localhost entra para dar para testar
   antes de publicar (`python -m http.server` na pasta). */

const Pwa = {
  evento: null,        // beforeinstallprompt guardado (Android / Chrome / Edge)
  avisoFechado: false, // fechou as instruções do iPhone: não oferece de novo nesta visita
  recarregando: false,

  instalado() {
    return matchMedia("(display-mode: standalone)").matches || navigator.standalone === true;
  },

  // iPhone/iPad não têm beforeinstallprompt; o iPad novo se diz "Macintosh".
  ios() {
    return /iphone|ipad|ipod/i.test(navigator.userAgent) ||
      (navigator.platform === "MacIntel" && navigator.maxTouchPoints > 1);
  },

  iniciar() {
    const servidorSeguro =
      location.protocol === "https:" ||
      location.hostname === "localhost" ||
      location.hostname === "127.0.0.1";
    if (!("serviceWorker" in navigator) || !servidorSeguro) return;

    Pwa.registrar();
    Pwa.botaoInstalar();
  },

  /* ---------- service worker e aviso de atualização ---------- */

  registrar() {
    navigator.serviceWorker.register("sw.js").then((reg) => {
      // versão nova já baixada e esperando (outra aba, visita anterior)
      if (reg.waiting && navigator.serviceWorker.controller) Pwa.avisarAtualizacao(reg.waiting);

      reg.addEventListener("updatefound", () => {
        const novo = reg.installing;
        if (!novo) return;
        novo.addEventListener("statechange", () => {
          // "installed" com um controlador ativo = é atualização, não a primeira instalação
          if (novo.state === "installed" && navigator.serviceWorker.controller) Pwa.avisarAtualizacao(novo);
        });
      });

      // aparelho de balcão fica com a aba aberta o dia todo: procura versão nova ao voltar para ela
      document.addEventListener("visibilitychange", () => {
        if (document.visibilityState === "visible") reg.update().catch(() => {});
      });
    }).catch(() => {
      /* Sem aviso ao cliente: o site funciona igual, só não instala. */
    });

    navigator.serviceWorker.addEventListener("controllerchange", () => {
      if (Pwa.recarregando) return;
      Pwa.recarregando = true;
      location.reload();
    });
  },

  avisarAtualizacao(worker) {
    const aviso = document.getElementById("avisoVersao");
    aviso.hidden = false;
    document.getElementById("btnAtualizar").onclick = () => {
      aviso.hidden = true;
      worker.postMessage("PULAR_ESPERA");
    };
  },

  /* ---------- botão "Instalar app" ---------- */

  botaoInstalar() {
    const botao = document.getElementById("btnInstalar");
    const avisoIos = document.getElementById("avisoIos");
    if (Pwa.instalado()) return;

    window.addEventListener("beforeinstallprompt", (ev) => {
      ev.preventDefault();
      Pwa.evento = ev;
      botao.hidden = false;
    });

    window.addEventListener("appinstalled", () => {
      Pwa.evento = null;
      botao.hidden = true;
    });

    if (Pwa.ios()) botao.hidden = false;

    botao.addEventListener("click", () => {
      if (Pwa.evento) {
        Pwa.evento.prompt();
        Pwa.evento = null;
        botao.hidden = true;
      } else if (Pwa.ios() && !Pwa.avisoFechado) {
        avisoIos.hidden = false;
      }
    });

    document.getElementById("btnFecharIos").addEventListener("click", () => {
      avisoIos.hidden = true;
      Pwa.avisoFechado = true;
      botao.hidden = true;
    });
  },
};

Pwa.iniciar();
