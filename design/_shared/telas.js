/* telas.js - monta TODAS as telas de referência do jogo a partir de window.TEMA.
   Menu, Modos, Config, Multiplayer, Ajustes, Criar sala, Entrar em sala, Sala de
   espera, Mesa Hold'em, Showdown, Pif Paf, Dominó e Fim de jogo.
   Cada mockup só traz o CSS do estilo (cores/bordas/fontes). Palco 1280x800. */
(function () {
  const T = Object.assign({
    titulo: "TEXAS HOLD'EM", sub: "Solo vs Bots • Mesa de 8 jogadores",
    btns: ["Jogar", "Configurações", "Sair"], keys: ["Enter", "", "Esc"],
    modosTitulo: "Escolha o modo",
    modos: [
      ["♠", "Texas Hold'em", "No-Limit, torneio contra bots", "Ativo"],
      ["♣", "Pif Paf", "Compra, descarte e batida", "Ativo"],
      ["▯", "Dominó", "Corrida aos 250 pontos, 3 a 4 jogadores", "Ativo"],
      ["?", "Modo inédito", "Em breve", "Em breve"]],
    mesaInfo: "Mão #7 • Blinds 10/20", pote: "Pote 340",
    acoes: [["Fold", "F"], ["Call 20", "C"], ["Raise", "R"]],
    historico: ["Bot Ana pagou 20", "Bot Caio aumentou para 60", "Você pagou 60", "Flop: A♠ K♥ 7♦"],
    vez: "Sua vez", voltar: "‹ Voltar", baralho: "Padrão"
  }, window.TEMA || {});

  const ES = { copas: "♥", ouros: "♦", paus: "♣", espadas: "♠" };
  const carta = (r, s) => `<div class="carta ${s === "♥" || s === "♦" ? "vermelha" : "preta"}"><span class="r">${r}</span><span class="n">${s}</span><span class="r b">${r}</span></div>`;
  const verso = '<div class="carta verso"><i></i></div>';
  const vazio = '<div class="carta vazia"></div>';
  const go = (s, txt, cls = "", key = "") => `<button class="btn ${cls}" data-go="${s}">${txt}${key ? `<kbd>${key}</kbd>` : ""}</button>`;
  const av = (t) => `<div class="av">${t}</div>`;
  const P = (x, y, w, h, html, cls = "") => `<div class="painel ${cls}" style="left:${x}px;top:${y}px;width:${w}px;${h ? `height:${h}px` : ""}">${html}</div>`;
  const tela = (id, html) => `<section id="s-${id}" class="tela">${html}</section>`;
  const voltar = (s) => go(s, T.voltar, "voltar");
  const sw = (on) => `<span class="sw${on ? " on" : ""}"></span>`;
  const linha = (t, sub, ctl) => `<div class="linha"><div><b>${t}</b><small>${sub}</small></div>${ctl}</div>`;
  const stepper = (v) => `<div class="stepper"><button class="btn">−</button><output>${v}</output><button class="btn">+</button></div>`;

  /* ---------- peças de dominó ---------- */
  const PIPS = { 0: [], 1: [4], 2: [0, 8], 3: [0, 4, 8], 4: [0, 2, 6, 8], 5: [0, 2, 4, 6, 8], 6: [0, 2, 3, 5, 6, 8] };
  const metade = (n) => `<div class="m">${[...Array(9).keys()].map(i => PIPS[n].includes(i) ? "<i></i>" : "<b></b>").join("")}</div>`;
  const peca = (a, b, v, style = "", cls = "") => `<div class="peca${v ? " v" : ""} ${cls}" style="${style}">${metade(a)}${metade(b)}</div>`;
  const pecaVerso = (v) => `<div class="peca verso-p${v ? " v" : ""}"><div class="m"></div><div class="m"></div></div>`;

  /* ---------- telas ---------- */
  const menu = tela("menu", `
    <div class="logo"><div class="logo-ic">♠</div><div><h1>${T.titulo}</h1><p class="sub">${T.sub}</p></div></div>
    <div class="botoes">${T.btns.map((b, i) => `<button class="btn b${i}" ${i === 0 ? 'data-go="modos"' : i === 1 ? 'data-go="ajustes"' : ""}>${b}${T.keys[i] ? `<kbd>${T.keys[i]}</kbd>` : ""}</button>`).join("")}</div>
    <div class="rodape">v1.0 • feito com Python + Pygame</div>`);

  const modos = tela("modos", `${voltar("menu")}<h2>${T.modosTitulo}</h2>
    <div class="cards-modo">${T.modos.map((m, i) => `<div class="card-modo m${i}${i === 3 ? " off" : ""}" ${i < 3 ? `data-go="${["config", "config", "config"][i]}"` : ""}><div class="ic">${m[0]}</div><h3>${m[1]}</h3><p>${m[2]}</p><span class="badge">${m[3]}</span></div>`).join("")}</div>`);

  const config = tela("config", `${voltar("modos")}<h2>Configuração da mesa — Texas Hold'em</h2>
    ${P(410, 190, 460, 0, `
      <div class="seg"><button class="btn on">Solo vs Bots</button>${go("multi", "Multiplayer Local")}</div>
      <p class="rotulo" style="margin-top:34px">Quantidade de bots na mesa</p>${stepper(3)}
      <p class="dica">Mesa final: você + 3 bots = 4 jogadores</p>
      <p class="rotulo" style="margin-top:30px">Baralho</p>
      <div class="deckprev">${carta("A", "♠")}<span class="badge">${T.baralho}</span></div>`, "p-config")}
    <div class="cta">${go("holdem", "Iniciar Partida", "b0", "Enter")}</div>`);

  const multi = tela("multi", `${voltar("modos")}<h2>Configuração da mesa — Texas Hold'em</h2>
    ${P(410, 190, 460, 0, `
      <div class="seg">${go("config", "Solo vs Bots")}<button class="btn on">Multiplayer Local</button></div>
      <p class="dica" style="margin:34px 0 22px">Jogue com outras pessoas na mesma rede Wi-Fi/LAN</p>
      ${go("criar", "Criar sala (ser anfitrião)", "largo b0")}<div style="height:16px"></div>${go("entrar", "Entrar em sala", "largo")}`, "p-multi")}`);

  const ajustes = tela("ajustes", `${voltar("menu")}<h2>Ajustes</h2><p class="sub2">Valem a partir da próxima partida iniciada</p>
    ${P(300, 215, 680, 0, `
      ${linha("Velocidade dos bots", "Tempo de espera entre jogadas", `<span class="pill">Normal</span>`)}
      ${linha("Fichas iniciais", "Torneio de Hold'em e Pif Paf", stepper("1.500").replace('class="stepper"', 'class="stepper mini"'))}
      ${linha("Mostrar atalhos", "Teclas nas dicas dos botões", sw(true))}
      ${linha("Coringa no Pif Paf", "Adiciona 4 coringas ao baralho", sw(false))}
      ${linha("Baralho", "Aparência das cartas", `<span style="display:flex;align-items:center;gap:14px"><span class="mini-carta">${carta("A", "♠")}</span><span class="pill">${T.baralho}</span></span>`)}
      ${linha("Seleção automática de peças", "Dominó: escolhe a ponta quando só há uma", sw(false))}
      ${linha("Tela cheia", "Alternar com F11", sw(false))}`, "p-ajustes")}`);

  const criar = tela("criar", `${voltar("config")}<h2>Criar sala</h2>
    ${P(420, 210, 440, 0, `
      <p class="rotulo">Como você quer ser chamado na mesa?</p>
      <input class="campo" value="Inácio" maxlength="14">
      <p class="dica" style="margin:12px 0 26px">Modo: Texas Hold'em • até 8 jogadores</p>${go("lobby", "Criar sala", "largo b0")}`)}`);

  const entrar = tela("entrar", `${voltar("config")}<h2>Entrar em sala</h2>
    ${P(400, 170, 480, 0, `
      <label class="campo-l">Seu nome</label><input class="campo" value="Convidado">
      <label class="campo-l">Código da sala</label><input class="campo" value="K7QX" style="letter-spacing:6px;text-transform:uppercase">
      ${go("lobby", "Entrar", "largo b0")}
      <p class="dica" style="margin:18px 0 10px">— ou —</p>
      <label class="campo-l">Salas encontradas na rede</label>
      <div class="sala-item"><div><b>Sala do Caio</b><small>Hold'em • 3/8 jogadores</small></div>${go("lobby", "Entrar")}</div>
      <div class="sala-item"><div><b>Mesa da Ana</b><small>Dominó • 2/4 jogadores</small></div>${go("lobby", "Entrar")}</div>`)}`);

  const slots = [["IV", "Inácio (você)", "Anfitrião"], ["CA", "Caio", ""], ["AN", "Ana", ""], ["DU", "Duda", "Pronto"]];
  const lobby = tela("lobby", `${voltar("criar")}<h2 style="top:60px">Sala de espera</h2>
    ${P(70, 130, 640, 0, `
      <div class="codigo"><span class="campo-l" style="margin:0">Código da sala</span><b>K7QX</b><small>192.168.0.14 : 5050</small></div>
      ${slots.map(s => `<div class="slot">${av(s[0])}<b>${s[1]}</b>${s[2] ? `<span class="tag">${s[2]}</span>` : ""}</div>`).join("")}
      ${[5, 6, 7, 8].map(n => `<div class="slot vago">${av(n)}<b>Aguardando jogador…</b></div>`).join("")}
      <div class="linha" style="border:none;padding-top:20px"><div><b>Completar vagas restantes com bots</b></div>${sw(true)}</div>
      ${go("holdem", "Iniciar partida", "largo b0", "Enter")}`, "p-lobby")}
    ${P(740, 130, 470, 0, `
      <h4 class="chat-h">Chat da sala</h4>
      <div class="chat"><p><b>Caio:</b> bora!</p><p><b>Ana:</b> já tô aqui</p><p><b>Duda:</b> pode começar</p><p class="sys">Duda entrou na sala</p></div>
      <input class="campo" placeholder="Digite uma mensagem…">`, "p-chat")}`);

  /* ---------- mesas ---------- */
  const seats = [
    ["BC", "Bot Caio", "1.480", "Pensando…", 250, 62, 1, ["Q", "♠"], ["J", "♠"]],
    ["BD", "Bot Duda", "2.100", "Apostou 60", 830, 62, 0, ["K", "♦"], ["K", "♣"]],
    ["BB", "Bot Bruno", "980", "Fold", 50, 300, 0, ["3", "♣"], ["8", "♥"]],
    ["BE", "Bot Elis", "1.730", "All-in", 1040, 300, 0, ["A", "♥"], ["A", "♦"]],
    ["BA", "Bot Ana", "1.250", "Pagou 60", 215, 540, 0, ["9", "♦"], ["9", "♠"]]];
  const assento = (s, i, show, venc) => {
    const cls = show ? (i === 1 ? " vez" : "") : (s[6] ? " vez" : "");
    const st = show ? (i === 1 ? "Full House" : s[3] === "Fold" ? "Fold" : ["Dois pares", "Trinca", "", "Par"][i] || "Par") : s[3];
    return `<div class="assento${cls}${s[3] === "Fold" ? " fold" : ""}" style="left:${s[4]}px;top:${s[5]}px">
      ${av(s[0])}<div class="info"><b>${s[1]}</b><span class="stack">${s[2]}</span></div><em class="st">${st}</em>
      <div class="maos">${show && s[3] !== "Fold" ? carta(...s[7]) + carta(...s[8]) : verso + verso}</div></div>`;
  };
  const heroi = (cartasHtml, vez) => `<div class="heroi"><div class="hero-cartas">${cartasHtml}</div>
    <div class="hero-info">${av("VO")}<div class="info"><b>Você</b><span class="stack">1.500</span></div><em class="st">${vez}</em></div></div>`;
  const topo = (info, chips) => `${go("menu", "Sair", "sair")}<div class="hud">${info}</div><div class="chips-hud">${chips}</div>`;

  const holdem = tela("holdem", `${topo(T.mesaInfo, "Você: 1.500")}
    <div class="mesa"><div class="felt"></div><div class="pote">${T.pote}</div>
      <div class="comunitarias">${carta("A", "♠")}${carta("K", "♥")}${carta("7", "♦")}${verso}${vazio}</div></div>
    ${seats.map((s, i) => assento(s, i, false)).join("")}
    ${heroi(carta("K", "♣") + carta("Q", "♦"), T.vez)}
    <div class="acoes">${T.acoes.map((a, i) => `<button class="btn a${i}">${a[0]}<kbd>${a[1]}</kbd></button>`).join("")}</div>
    <div class="historico"><h4>Histórico</h4>${T.historico.map(h => `<p>${h}</p>`).join("")}</div>`);

  const showdown = tela("showdown", `${topo("Mão #7 • Showdown", "Você: 1.500")}
    <div class="mesa"><div class="felt"></div><div class="pote">${T.pote}</div>
      <div class="comunitarias">${carta("A", "♠")}${carta("K", "♥")}${carta("7", "♦")}${carta("K", "♠")}${carta("2", "♣")}</div></div>
    <div class="banner" style="top:440px">Bot Duda venceu • Full House (K K K A A)</div>
    ${seats.map((s, i) => assento(s, i, true)).join("")}
    ${heroi(carta("K", "♣") + carta("Q", "♦"), "Trinca de K")}
    <div class="acoes">${go("holdem", "Próxima mão", "a2", "Enter")}</div>
    <div class="historico"><h4>Histórico</h4><p>River: 2♣</p><p>Showdown</p><p>Bot Duda leva 340</p></div>`);

  const pseats = [["BB", "Bot Bruno", "1.500", "9 cartas", 215, 62, 0], ["BA", "Bot Ana", "1.500", "9 cartas", 40, 300, 0], ["BC", "Bot Caio", "1.500", "9 cartas", 1040, 300, 1]];
  const mao9 = [["3", "♥"], ["9", "♠"], ["7", "♦"], ["8", "♥"], ["A", "♠"], ["5", "♥"], ["Q", "♠"], ["8", "♣"], ["4", "♠"]];
  const pifpaf = tela("pifpaf", `${topo("Mão #1", "Você: 1.500")}
    <div class="mesa"><div class="felt"></div>
      <div class="banner" style="top:26px">Vira 7♠ → coringa vale 8</div>
      <div class="pilhas"><div>${verso}<small>Monte (66)</small></div><div>${carta("6", "♥")}<small>Descarte</small></div></div></div>
    ${pseats.map(s => `<div class="assento${s[6] ? " vez" : ""}" style="left:${s[4]}px;top:${s[5]}px">${av(s[0])}<div class="info"><b>${s[1]}</b><span class="stack">${s[2]}</span></div><em class="st">${s[3]}</em></div>`).join("")}
    <div class="heroi"><div class="hero-info">${av("VO")}<div class="info"><b>Você</b><span class="stack">1.500</span></div><em class="st">${T.vez}</em></div>
      <div class="hero-cartas leque">${mao9.map(c => carta(...c)).join("")}</div></div>
    <div class="acoes">${go("pifpaf", "Comprar monte", "a1", "M")}${go("pifpaf", "Comprar descarte", "a2", "D")}</div>
    <div class="historico"><h4>Histórico</h4><p>Bot Ana descartou 6♥</p><p>Bot Caio comprou do monte</p><p>Sua vez</p></div>`);

  const cx = 450, cy = 210;
  const cadeia = [
    [cx - 19, cy - 38, 6, 6, 1], [cx + 19, cy - 19, 6, 2, 0], [cx + 95, cy - 19, 2, 5, 0], [cx + 171, cy - 38, 5, 5, 1],
    [cx - 95, cy - 19, 6, 4, 0], [cx - 171, cy - 19, 4, 1, 0], [cx - 247, cy - 19, 1, 3, 0],
    [cx - 19, cy - 114, 6, 3, 1], [cx - 19, cy + 38, 6, 0, 1]];
  const dseats = [["BB", "Bot Bruno", "35 pts", "7 peças", 230, 62, 0], ["BA", "Bot Ana", "20 pts", "7 peças", 30, 290, 0], ["BC", "Bot Caio", "55 pts", "7 peças", 1040, 290, 1]];
  const domino = tela("domino", `${topo("Mão #3 • Meta: 250 pts", "Você: 70 pts")}
    <div class="mesa dom"><div class="felt"></div>${cadeia.map(c => peca(c[2], c[3], c[4], `position:absolute;left:${c[0]}px;top:${c[1]}px`)).join("")}</div>
    ${dseats.map(s => `<div class="assento${s[6] ? " vez" : ""}" style="left:${s[4]}px;top:${s[5]}px">${av(s[0])}<div class="info"><b>${s[1]}</b><span class="stack">${s[2]}</span></div><em class="st">${s[3]}</em></div>`).join("")}
    <div class="mao-dom">${[[6, 5, 1], [4, 4, 1], [3, 1, 1], [2, 0, 0], [5, 3, 0], [1, 1, 1], [6, 0, 0]].map(p => peca(p[0], p[1], true, "", p[2] ? "ok" : "")).join("")}</div>
    <div class="dica-dom">Arraste uma peça destacada para uma ponta da mesa</div>
    <div class="acoes">${go("domino", "Passar", "a0", "P")}</div>
    <div class="historico"><h4>Pontuação</h4><p>Você <b>70</b></p><p>Bot Caio <b>55</b></p><p>Bot Bruno <b>35</b></p><p>Bot Ana <b>20</b></p></div>`);

  const fim = tela("fim", `<h2 style="top:90px">Fim de jogo</h2>
    ${P(410, 190, 460, 0, `
      <div class="trofeu">♛</div><p class="rotulo" style="font-size:24px">Bot Duda venceu o torneio!</p>
      <div class="rank">${[["1º", "Bot Duda", "6.000"], ["2º", "Você", "0"], ["3º", "Bot Caio", "0"], ["4º", "Bot Ana", "0"]].map(r => `<div class="slot"><b class="pos">${r[0]}</b><b>${r[1]}</b><span class="tag">${r[2]} fichas</span></div>`).join("")}</div>
      <div style="display:flex;gap:14px;margin-top:26px">${go("modos", "Jogar de novo", "b0")}${go("menu", "Menu")}</div>`, "p-fim")}`);

  const ABAS = [["menu", "Menu"], ["modos", "Modos"], ["config", "Config"], ["multi", "Multiplayer"], ["ajustes", "Ajustes"],
    ["criar", "Criar sala"], ["entrar", "Entrar"], ["lobby", "Sala de espera"], ["holdem", "Hold'em"], ["showdown", "Showdown"],
    ["pifpaf", "Pif Paf"], ["domino", "Dominó"], ["fim", "Fim de jogo"]];

  document.body.insertAdjacentHTML("beforeend",
    `<nav id="abas"><a href="../index.html" class="home">← galeria</a>${ABAS.map(a => `<button data-s="${a[0]}">${a[1]}</button>`).join("")}</nav>
     <div id="vp"><div id="stage">${menu + modos + config + multi + ajustes + criar + entrar + lobby + holdem + showdown + pifpaf + domino + fim}</div></div>`);

  const stage = document.getElementById("stage"), vp = document.getElementById("vp");
  function ajustar() {
    const k = Math.min(innerWidth / 1280, (innerHeight - 44) / 800);
    stage.style.transform = `scale(${k})`;
    vp.style.height = (800 * k) + "px"; vp.style.width = (1280 * k) + "px";
  }
  function ir(s) {
    if (s === "mesa") s = "holdem";
    document.querySelectorAll(".tela").forEach(e => e.classList.toggle("ativa", e.id === "s-" + s));
    document.querySelectorAll("#abas button").forEach(b => b.classList.toggle("on", b.dataset.s === s));
    try { location.hash = s; } catch (e) {}
  }
  document.querySelectorAll("#abas button").forEach(b => b.onclick = () => ir(b.dataset.s));
  stage.addEventListener("click", ev => {
    const el = ev.target.closest("[data-go]");
    if (!el) return;
    let alvo = el.dataset.go;
    const m = el.closest(".card-modo");
    if (m) alvo = m.classList.contains("m0") ? "config" : m.classList.contains("m1") ? "pifpaf" : "domino";
    ir(alvo);
  });
  addEventListener("resize", ajustar); ajustar();
  const h = location.hash.slice(1);
  ir(ABAS.some(a => a[0] === h) || h === "mesa" ? h : "menu");
})();
