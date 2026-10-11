"""Gera os mockup.html de cada estilo a partir de _shared/base.css + telas.js.
Uso: python design/_shared/gerar.py   (a partir da raiz do projeto)"""
import os

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

MODELO = """<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{titulo}</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?{fonts}&display=swap">
<link rel="stylesheet" href="../_shared/base.css">
<style>
{css}
</style></head><body>
<script>window.TEMA={tema};</script>
<script src="../_shared/telas.js"></script>
</body></html>
"""

ESTILOS = {}

ESTILOS["02_dark_glassmorphism"] = ("Dark Glassmorphism", "family=Outfit:wght@400;600;800&family=JetBrains+Mono:wght@500",
 r'''{keys:["↵","","Esc"]}''', r'''
:root{--page:#05060f;--bg:radial-gradient(circle at 20% 15%,#3b2a7a 0,transparent 45%),radial-gradient(circle at 85% 80%,#0e5a7a 0,transparent 45%),#0b0d1f;--ink:#eef0ff;--font-body:Outfit,sans-serif;--title:800 1em Outfit,sans-serif;--glass:rgba(255,255,255,.08);--line:rgba(255,255,255,.18);--ac:#8b7bff;--ac2:#34e0c4}
.logo-ic,.btn,.card-modo,.assento,.hero-info,.hud,.chips-hud,.pote,.historico{background:var(--glass);border:1px solid var(--line);backdrop-filter:blur(14px);border-radius:20px;box-shadow:0 10px 40px rgba(0,0,0,.35),inset 0 1px 0 rgba(255,255,255,.15)}
.logo-ic{color:var(--ac2);font-size:50px}h1{background:linear-gradient(90deg,#fff,var(--ac2));-webkit-background-clip:text;color:transparent}
.btn{color:var(--ink);border-radius:16px}.btn:hover{background:rgba(255,255,255,.16)}.b0,.a2{background:linear-gradient(135deg,var(--ac),#5b8cff);border-color:transparent}.b2,.a0{color:#ff9aa8}
kbd{background:rgba(255,255,255,.15);color:#fff;font-family:JetBrains Mono,monospace}
.card-modo:hover{transform:translateY(-6px)}.card-modo .ic{color:var(--ac2)}.card-modo.off{opacity:.4}.badge{border-radius:99px;background:rgba(52,224,196,.18);color:var(--ac2)}
.felt{background:radial-gradient(ellipse at 50% 40%,#1c6b6b,#0c2f3c 70%);border:2px solid var(--line);box-shadow:0 0 80px rgba(52,224,196,.25),inset 0 0 60px rgba(0,0,0,.5)}
.pote{border-radius:99px;color:var(--ac2)}.hud,.chips-hud{border-radius:99px}
.carta{border-radius:10px}.carta.preta,.carta.vermelha{background:linear-gradient(160deg,#fff,#dfe3ff);color:#14172e}.vermelha{color:#e23d6b!important}
.carta.verso{background:linear-gradient(135deg,#6b5bff,#2bd4c0);border:2px solid rgba(255,255,255,.5)}.carta.verso i{border:1px solid rgba(255,255,255,.6);border-radius:6px}
.carta.vazia{border:1.5px dashed var(--line)}
.av{background:linear-gradient(135deg,var(--ac),var(--ac2));color:#06101c}.st{border-radius:99px;background:rgba(255,255,255,.12)}
.vez{border-color:var(--ac2);box-shadow:0 0 0 2px var(--ac2),0 0 30px rgba(52,224,196,.5)}
''')

ESTILOS["04_terminal_tatico"] = ("Terminal Tático", "family=IBM+Plex+Mono:wght@400;600;700",
 r'''{titulo:"> POKER.EXE",sub:"sessao: solo // bots: 5 // seed: 0x4f2a",btns:["[ JOGAR ]","[ CONFIG ]","[ SAIR ]"],keys:["ENTER","","ESC"],modosTitulo:"// SELECIONAR PROTOCOLO",modos:[["♠","HOLDEM.SYS","no-limit / torneio","ONLINE"],["♣","PIFPAF.SYS","compra / descarte / bate","ONLINE"],["▯","DOMINO.SYS","250 pts / 3-4 jog","ONLINE"],["?","NULL","modulo nao carregado","OFFLINE"]],mesaInfo:"HAND#007 BLINDS 10/20",pote:"POT=340",vez:"> AGUARDANDO INPUT"}''', r'''
:root{--page:#000;--bg:#070b08;--ink:#7dffa0;--font-body:"IBM Plex Mono",monospace;--title:700 1em "IBM Plex Mono",monospace;--ac:#7dffa0;--am:#ffb347;--dim:#2a4a33}
#stage:after{content:"";position:absolute;inset:0;pointer-events:none;background:repeating-linear-gradient(0deg,rgba(0,0,0,.25) 0 1px,transparent 1px 3px)}
h1{font-size:46px;text-shadow:0 0 14px var(--ac)}.logo-ic{border:2px solid var(--ac);font-size:44px}.sub{text-transform:none;letter-spacing:0}
.btn,.card-modo,.assento,.hero-info,.hud,.chips-hud,.pote,.historico{background:transparent;border:1px solid var(--ac);border-radius:0;color:var(--ac)}
.btn:hover,.card-modo:hover{background:var(--ac);color:#000}.b0{border-width:2px;box-shadow:0 0 14px rgba(125,255,160,.4)}.b2,.a0{color:#ff6b6b;border-color:#ff6b6b}
kbd{background:none;border:1px solid currentColor;border-radius:0;color:inherit}.card-modo.off{border-style:dashed;opacity:.5}.badge{border:1px solid currentColor}
.felt{border:1px dashed var(--dim);border-radius:0;background:linear-gradient(var(--dim) 1px,transparent 1px) 0 0/100% 30px,linear-gradient(90deg,var(--dim) 1px,transparent 1px) 0 0/30px 100%;opacity:.55}
.pote{color:var(--am);border-color:var(--am)}.hud,.chips-hud{border:none;border-bottom:1px solid var(--ac)}
.carta{border-radius:0;border:1px solid var(--ac);background:#050805;color:var(--ac)}.carta.vermelha{color:var(--am)!important;border-color:var(--am)}
.carta.verso{background:repeating-linear-gradient(45deg,var(--dim) 0 4px,transparent 4px 8px)}.carta.vazia{border-style:dashed;border-color:var(--dim)}
.av{border:1px solid var(--ac);border-radius:0}.st{border:1px solid currentColor}.vez{background:rgba(125,255,160,.12)!important;box-shadow:0 0 18px rgba(125,255,160,.5)}
.historico p:before{content:"> ";color:var(--am)}
''')

ESTILOS["06_art_deco_cassino"] = ("Art Déco Cassino", "family=Cinzel:wght@500;700&family=Josefin+Sans:wght@400;600",
 r'''{titulo:"TEXAS HOLD’EM",sub:"Salão Privé • Mesa de oito lugares",btns:["Entrar no Salão","Configurações","Retirar-se"],keys:["","",""],modosTitulo:"Escolha sua Mesa",mesaInfo:"Mão VII • Blinds 10 / 20"}''', r'''
:root{--page:#0a0a0a;--bg:radial-gradient(circle at 50% 0,#12302c,#07110f 70%);--ink:#e9d9a6;--gold:#c9a24b;--font-body:"Josefin Sans",sans-serif;--title:700 1em Cinzel,serif}
#stage:before{content:"";position:absolute;inset:14px;border:1px solid var(--gold);outline:1px solid var(--gold);outline-offset:6px;pointer-events:none}
h1,h2{font-family:Cinzel,serif;letter-spacing:6px;color:var(--gold);font-weight:700}.logo-ic{border:2px solid var(--gold);transform:rotate(45deg);font-size:0}.logo-ic:after{content:"♠";font-size:40px;transform:rotate(-45deg);color:var(--gold)}
.sub{letter-spacing:5px;font-size:12px}.btn{background:transparent;border:1px solid var(--gold);color:var(--gold);letter-spacing:3px;text-transform:uppercase;font-size:14px;clip-path:polygon(12px 0,calc(100% - 12px) 0,100% 50%,calc(100% - 12px) 100%,12px 100%,0 50%)}
.btn:hover,.b0{background:var(--gold);color:#07110f}kbd{display:none}
.card-modo{border:1px solid var(--gold);background:linear-gradient(#0e2824,#08140f);clip-path:polygon(0 24px,24px 0,calc(100% - 24px) 0,100% 24px,100% 100%,0 100%)}.card-modo .ic{color:var(--gold)}.card-modo h3{letter-spacing:3px;color:var(--gold)}.card-modo.off{opacity:.45}.badge{border-top:1px solid var(--gold);border-bottom:1px solid var(--gold);letter-spacing:3px;color:var(--gold)}
.felt{background:radial-gradient(ellipse,#17604f,#0b2f27);border:6px double var(--gold)}.pote,.hud,.chips-hud,.historico,.assento,.hero-info{background:#0a1a16;border:1px solid var(--gold);color:var(--ink)}.pote{color:var(--gold);letter-spacing:2px}
.carta{background:#f7efd8;border-radius:6px;border:1px solid var(--gold);color:#12201c}.carta.vermelha{color:#a8281f!important}.carta.verso{background:#0f3b32;border:2px solid var(--gold)}.carta.verso i{border:1px solid var(--gold);background:repeating-linear-gradient(45deg,transparent 0 5px,rgba(201,162,75,.4) 5px 6px)}.carta.vazia{border:1px dashed var(--gold);opacity:.5}
.av{background:var(--gold);color:#07110f;border-radius:50%}.st{border:1px solid var(--gold);color:var(--gold)}.vez{box-shadow:0 0 0 2px var(--gold),0 0 30px rgba(201,162,75,.5)}
.acoes .btn{clip-path:none;border-radius:2px}
''')

ESTILOS["07_pixel_retro_crt"] = ("Pixel Art Retrô CRT", "family=Press+Start+2P&family=VT323",
 r'''{titulo:"POKER QUEST",sub:"1 JOGADOR  -  7 BOTS",btns:["JOGAR","OPCOES","SAIR"],keys:["START","","ESC"],modosTitulo:"ESCOLHA O JOGO",mesaInfo:"RODADA 07  BLINDS 10/20",pote:"POTE 340",vez:"SUA VEZ!"}''', r'''
:root{--page:#000;--bg:#1a1c2c;--ink:#f4f4f4;--font-body:VT323,monospace;--title:400 1em "Press Start 2P",monospace;--p1:#ffcd75;--p2:#b13e53;--p3:#38b764;--p4:#3b5dc9;--p5:#41a6f6;--sh:#0c0d17}
#stage{font-size:22px}#stage:after{content:"";position:absolute;inset:0;pointer-events:none;background:repeating-linear-gradient(0deg,rgba(0,0,0,.18) 0 2px,transparent 2px 4px);box-shadow:inset 0 0 120px rgba(0,0,0,.6)}
h1{font-size:34px;color:var(--p1);text-shadow:4px 4px 0 var(--p2);line-height:1.4;letter-spacing:0}h2{font-size:26px;color:var(--p1);text-shadow:3px 3px 0 var(--p2)}.sub{font-size:20px;letter-spacing:2px;color:var(--p5)}
.logo-ic{background:var(--p2);border:4px solid #fff;box-shadow:6px 6px 0 var(--sh);border-radius:0}
.btn,.card-modo,.assento,.hero-info,.hud,.chips-hud,.pote,.historico{border:4px solid #fff;border-radius:0;box-shadow:6px 6px 0 var(--sh);background:#333c57;font-size:22px}
.btn{font-family:"Press Start 2P",monospace;font-size:14px;color:#fff;padding:18px 22px}.btn:hover{transform:translate(2px,2px);box-shadow:3px 3px 0 var(--sh)}.b0,.a2{background:var(--p3)}.b2,.a0{background:var(--p2)}.a1{background:var(--p4)}
kbd{font-family:VT323;font-size:16px;background:#fff;color:#000;border-radius:0}
.card-modo h3{font-size:14px;line-height:1.5}.card-modo .ic{color:var(--p1)}.card-modo.m1{background:#3b5dc9}.card-modo.m2{background:#38b764}.card-modo.off{filter:grayscale(1);opacity:.6}.badge{background:var(--p1);color:#000;border-radius:0}
.felt{background:#257179;border:8px solid #fff;border-radius:0;box-shadow:inset 0 0 0 8px #1a4d55,8px 8px 0 var(--sh);clip-path:polygon(40px 0,calc(100% - 40px) 0,100% 40px,100% calc(100% - 40px),calc(100% - 40px) 100%,40px 100%,0 calc(100% - 40px),0 40px)}
.pote{background:var(--p1);color:#000}.carta{border-radius:0;border:4px solid #000;background:#f4f4f4;box-shadow:4px 4px 0 var(--sh);color:#1a1c2c}.carta.vermelha{color:var(--p2)!important}.carta.verso{background:var(--p4)}.carta.verso i{background:repeating-conic-gradient(var(--p5) 0 25%,var(--p4) 0 50%) 0 0/12px 12px;border:2px solid #fff}.carta.vazia{border:4px dashed #5d6a8a;box-shadow:none;background:transparent}
.av{border-radius:0;border:3px solid #fff;background:var(--p2);font-family:"Press Start 2P";font-size:11px}.st{background:var(--p5);color:#000;border-radius:0;font-size:16px}.vez{animation:p .6s steps(2) infinite}@keyframes p{50%{background:#41507a}}
''')

ESTILOS["08_synthwave_neon"] = ("Synthwave Neon", "family=Orbitron:wght@500;800&family=Rajdhani:wght@500;700",
 r'''{titulo:"NEON HOLD’EM",sub:"Night City Edition • Solo vs Bots",keys:["↵","","Esc"],modosTitulo:"SELECIONE O MODO"}''', r'''
:root{--page:#000;--bg:linear-gradient(#0b0221 0,#2a0845 55%,#ff3c8e 56%,#ff7a3c 57%,#14031f 57.2%);--ink:#f5eaff;--pk:#ff2e93;--cy:#27e8ff;--font-body:Rajdhani,sans-serif;--title:800 1em Orbitron,sans-serif}
#stage:before{content:"";position:absolute;left:-30%;right:-30%;top:57%;bottom:0;background:linear-gradient(var(--pk) 1px,transparent 1px) 0 0/100% 40px,linear-gradient(90deg,var(--pk) 1px,transparent 1px) 0 0/60px 100%;transform:perspective(300px) rotateX(55deg);transform-origin:top;opacity:.5}
.tela{z-index:1}h1,h2{font-family:Orbitron;color:#fff;text-shadow:0 0 8px var(--pk),0 0 24px var(--pk),0 0 48px var(--pk)}h1{font-size:48px}.sub{color:var(--cy);text-shadow:0 0 8px var(--cy)}
.logo-ic{border:3px solid var(--cy);box-shadow:0 0 20px var(--cy),inset 0 0 20px var(--cy);border-radius:14px;color:var(--cy)}
.btn,.card-modo,.assento,.hero-info,.hud,.chips-hud,.pote,.historico{background:rgba(20,3,40,.75);border:2px solid var(--cy);border-radius:8px;color:#fff;box-shadow:0 0 14px rgba(39,232,255,.5),inset 0 0 14px rgba(39,232,255,.2)}
.btn{font-family:Orbitron;font-size:15px;text-transform:uppercase;letter-spacing:2px}.b0,.a2{border-color:var(--pk);box-shadow:0 0 18px var(--pk),inset 0 0 14px rgba(255,46,147,.4)}.btn:hover{background:var(--pk)}kbd{background:var(--cy);color:#000;border-radius:3px}
.card-modo .ic{color:var(--pk);text-shadow:0 0 16px var(--pk)}.card-modo h3{font-family:Orbitron;font-size:16px}.card-modo.off{opacity:.45;border-color:#7a6a99;box-shadow:none}.badge{color:var(--cy);border:1px solid var(--cy);border-radius:3px}
.felt{background:radial-gradient(ellipse,#3a0d6e,#12032b);border:3px solid var(--pk);box-shadow:0 0 30px var(--pk),0 0 80px rgba(255,46,147,.4),inset 0 0 50px rgba(255,46,147,.3)}.pote{border-color:var(--pk);color:var(--pk);font-family:Orbitron}
.carta{border-radius:8px;border:2px solid var(--cy);background:#10052a;color:var(--cy);box-shadow:0 0 12px rgba(39,232,255,.5)}.carta.vermelha{color:var(--pk)!important;border-color:var(--pk);box-shadow:0 0 12px rgba(255,46,147,.6)}.carta.verso{background:linear-gradient(135deg,#2a0845,#10052a)}.carta.verso i{border:2px solid var(--pk);transform:rotate(45deg) scale(.7);box-shadow:0 0 10px var(--pk)}.carta.vazia{border:2px dashed #5d3b8a;box-shadow:none}
.av{background:linear-gradient(135deg,var(--pk),var(--cy));color:#10052a}.st{background:rgba(39,232,255,.15);border:1px solid var(--cy);border-radius:3px}.vez{border-color:var(--pk);box-shadow:0 0 24px var(--pk)}
''')

ESTILOS["09_papel_vintage"] = ("Papel Ilustrado Vintage", "family=Playfair+Display:ital,wght@0,700;0,900;1,500&family=Special+Elite&family=Libre+Baskerville",
 r'''{titulo:"Texas Hold’em",sub:"Gazeta do Jogador • Edição de Bolso",btns:["Sentar à mesa","Regulamento","Deixar o salão"],keys:["","",""],modosTitulo:"Qual jogo desta noite?",mesaInfo:"Mão nº 7 • Apostas obrigatórias 10 / 20",pote:"Pote: 340 fichas"}''', r'''
:root{--page:#2b1d12;--bg:#e8d9b5;--ink:#2a1a10;--red:#a8321f;--green:#2f5d46;--font-body:"Libre Baskerville",serif;--title:900 1em "Playfair Display",serif}
h1{font-size:60px;font-style:italic}h2{font-style:italic}.sub{font-family:"Special Elite";letter-spacing:3px}
.logo-ic{border:3px double var(--ink);border-radius:50%;color:var(--red)}
.btn,.card-modo,.assento,.hero-info,.hud,.chips-hud,.pote,.historico{background:#f3e8c9;border:2px solid var(--ink);color:var(--ink);box-shadow:4px 4px 0 rgba(42,26,16,.35)}
.btn{font-family:"Playfair Display";font-weight:700;border-radius:2px}.btn:hover,.b0{background:var(--red);color:#f3e8c9}kbd{display:none}
.card-modo{border:3px double var(--ink)}.card-modo .ic{color:var(--red)}.card-modo h3{font-style:italic}.card-modo.off{opacity:.5;border-style:dashed}.badge{font-family:"Special Elite";border:1px solid var(--ink)}
.felt{background:radial-gradient(ellipse,#3b7258,#2f5d46);border:10px solid #6b4226;box-shadow:inset 0 0 0 3px #d9c28a,6px 6px 0 rgba(42,26,16,.4)}
.pote{font-family:"Special Elite";background:#f3e8c9}.carta{background:#fbf4de;border:2px solid var(--ink);border-radius:5px;color:var(--ink);font-family:"Playfair Display"}.carta.vermelha{color:var(--red)!important}
.carta.verso{background:var(--red)}.carta.verso i{border:2px solid #f3e8c9;background:repeating-linear-gradient(45deg,transparent 0 4px,rgba(243,232,201,.5) 4px 5px)}.carta.vazia{border:2px dashed #d9c28a;opacity:.7}
.av{background:var(--green);color:#f3e8c9;font-family:"Playfair Display"}.st{font-family:"Special Elite";border:1px solid var(--ink)}.vez{background:#ffe9a0!important}.hud,.chips-hud{font-family:"Special Elite"}
''')

ESTILOS["10_editorial_suico"] = ("Editorial Suíço", "family=Archivo:wght@400;700;900&family=Archivo+Narrow:wght@500;700",
 r'''{titulo:"Hold’em",sub:"N.º 01 — Solo vs Bots — Mesa de 8",btns:["Jogar →","Configurações →","Sair →"],keys:["","",""],modosTitulo:"Modos",mesaInfo:"Mão 07 / Blinds 10—20",pote:"Pote 340"}''', r'''
:root{--page:#fff;--bg:#f4f4f0;--ink:#0d0d0d;--ac:#ff3b1f;--font-body:Archivo,sans-serif;--title:900 1em Archivo,sans-serif}
h1{font-size:120px;letter-spacing:-5px;line-height:.85}h2{font-size:80px;letter-spacing:-3px;text-align:left;left:90px;top:70px}
.logo{justify-content:flex-start;left:90px;top:90px;flex-direction:column;align-items:flex-start}.logo-ic{display:none}.sub{font-family:"Archivo Narrow";font-size:18px;color:var(--ac);font-weight:700}
.botoes{flex-direction:column;align-items:flex-start;left:90px;right:auto;top:360px;gap:0;width:560px}.btn{width:100%;text-align:left;background:none;border:none;border-top:3px solid var(--ink);border-radius:0;font-size:44px;font-weight:900;letter-spacing:-1px;padding:14px 0}.btn:last-child{border-bottom:3px solid var(--ink)}.btn:hover{color:var(--ac);padding-left:20px}kbd{display:none}
.rodape{text-align:left;left:90px}
.cards-modo{left:90px;right:90px;gap:0;top:220px;border-top:3px solid var(--ink)}.card-modo{background:none;border-right:3px solid var(--ink);align-items:flex-start;text-align:left;width:25%;height:420px;padding:20px}.card-modo:last-child{border-right:none}.card-modo .ic{font-size:90px;color:var(--ac)}.card-modo h3{font-size:30px;letter-spacing:-1px}.card-modo.off{opacity:.35}.badge{background:var(--ink);color:#fff}.card-modo:hover{background:var(--ink);color:#fff}
.voltar,.sair{background:none;border:none;font-weight:700;padding:0;top:24px;left:90px}.sair{left:24px}
.felt{background:#e4e4de;border:3px solid var(--ink);border-radius:0}.pote{background:var(--ac);color:#fff;font-weight:900}.hud,.chips-hud{background:none;font-family:"Archivo Narrow";text-transform:uppercase;letter-spacing:2px}
.carta{background:#fff;border:3px solid var(--ink);border-radius:0;color:var(--ink);font-weight:900}.carta.vermelha{color:var(--ac)!important}.carta.verso{background:var(--ink)}.carta.verso i{background:var(--ac);width:30%;height:30%}.carta.vazia{border:2px dashed #aaa}
.assento,.hero-info{background:#fff;border:3px solid var(--ink);border-radius:0}.av{border-radius:0;background:var(--ink);color:#fff}.st{background:var(--ink);color:#fff}.vez{background:var(--ac)!important;color:#fff}.vez .av{background:#fff;color:var(--ac)}
.acoes .btn{border:3px solid var(--ink);padding:12px;font-size:20px;text-align:center;width:auto}.acoes .btn:last-child{border-bottom:3px solid var(--ink)}.acoes .btn:hover{padding:12px;background:var(--ink);color:#fff}.a2{background:var(--ac);color:#fff}.historico{background:none;border:none;border-top:3px solid var(--ink);padding:10px 0}
''')

ESTILOS["11_zen_japones"] = ("Zen Japonês Hanafuda", "family=Shippori+Mincho:wght@500;800&family=Zen+Kaku+Gothic+New:wght@400;700",
 r'''{titulo:"Hold’em 花札",sub:"Uma mesa calma • contra os bots",keys:["","",""],modosTitulo:"Escolha o jogo",mesaInfo:"Mão 7 • Blinds 10/20",pote:"Pote 340"}''', r'''
:root{--page:#1c1a17;--bg:#efe7d6;--ink:#2b2622;--red:#c0392b;--green:#4f6b4a;--font-body:"Zen Kaku Gothic New",sans-serif;--title:800 1em "Shippori Mincho",serif}
#stage:before{content:"";position:absolute;right:-160px;top:-160px;width:520px;height:520px;border-radius:50%;background:var(--red);opacity:.9}
.tela{z-index:1}h1{font-size:56px}.sub{letter-spacing:6px;font-size:12px}.logo-ic{border:2px solid var(--ink);border-radius:50%;width:76px;height:76px;font-size:36px;background:#efe7d6}
.btn,.card-modo,.assento,.hero-info,.hud,.chips-hud,.pote,.historico{background:rgba(255,252,244,.9);border:1.5px solid var(--ink);border-radius:4px;color:var(--ink)}
.btn{letter-spacing:4px;border-radius:99px}.btn:hover,.b0{background:var(--ink);color:#efe7d6}kbd{display:none}
.card-modo{height:300px;border-radius:120px 120px 6px 6px;padding-top:50px}.card-modo .ic{color:var(--red)}.card-modo.m1 .ic{color:var(--green)}.card-modo.off{opacity:.45;border-style:dashed}.badge{letter-spacing:3px;border-bottom:1px solid var(--ink)}
.felt{background:var(--green);border-radius:50%;border:none;box-shadow:0 0 0 10px #efe7d6,0 0 0 12px var(--ink)}.pote{border-radius:99px}.hud,.chips-hud{border:none;background:none}
.carta{background:#fffaf0;border:1.5px solid var(--ink);border-radius:4px;color:var(--ink);font-family:"Shippori Mincho";box-shadow:0 3px 0 rgba(0,0,0,.2)}.carta.vermelha{color:var(--red)!important}.carta.verso{background:#1e2a3a}.carta.verso i{border-radius:50%;background:var(--red);width:42%;height:30%}.carta.vazia{border:1.5px dashed #efe7d6;opacity:.6}
.av{background:var(--ink);color:#efe7d6;font-family:"Shippori Mincho"}.st{border-bottom:1px solid var(--ink);padding:0}.vez{box-shadow:0 0 0 3px var(--red)}.historico{background:none;border:none;border-left:1.5px solid var(--ink);border-radius:0}
''')


# Variáveis e ajustes das telas extras (config, ajustes, lobby, dominó...) por estilo.
EXTRA = {
"06_art_deco_cassino": r"""
:root{--pn-bg:#0a1a16;--pn-bd:1px solid #c9a24b;--pn-r:2px;--pn-sh:0 0 0 5px #0a1a16,0 0 0 6px rgba(201,162,75,.55);--k-ac:#c9a24b;--k-ac-ink:#07110f;--k-mut:#b9aa7a;--sw-r:0;--pip-r:50%;--tl-face:#f7efd8;--tl-ink:#12201c;--tl-bd:1px solid #c9a24b;--tl-r:3px;--tl-sh:2px 3px 0 rgba(0,0,0,.45);--tl-sep:#c9a24b}
.btn.on,.seg .btn.on{background:var(--gold);color:#07110f}.pill,.tag,.banner{letter-spacing:2px;text-transform:uppercase;font-size:12px;border-radius:0}
.banner{font-size:14px;padding:8px 26px;background:#0a1a16;color:var(--gold);border:1px solid var(--gold);box-shadow:0 0 0 3px #0a1a16,0 0 0 4px var(--gold)}
.campo{background:#07110f;color:var(--ink)}.sw.on:after{background:#07110f}.trofeu{color:var(--gold)}.painel h4,.codigo b{color:var(--gold)}
.stepper .btn{clip-path:none;border-radius:50%}.linha b,.slot b{letter-spacing:1px}
""",
"07_pixel_retro_crt": r"""
:root{--pn-bg:#333c57;--pn-bd:4px solid #fff;--pn-r:0;--pn-sh:6px 6px 0 #0c0d17;--k-ac:#ffcd75;--k-ac-ink:#1a1c2c;--k-mut:#94b0c2;--sw-r:0;--pip-r:0;--tl-face:#f4f4f4;--tl-ink:#1a1c2c;--tl-bd:4px solid #000;--tl-r:0;--tl-sh:4px 4px 0 #0c0d17;--tl-sep:#000}
h2,.btn,.pill,.tag,.banner,.rotulo,.campo-l,.historico h4{text-transform:uppercase}
.btn.on,.seg .btn.on{background:var(--p1);color:#1a1c2c}.sw:after{border:2px solid #fff}.sw.on:after{background:#1a1c2c}.linha b{font-family:"Press Start 2P";font-size:12px;line-height:1.5}.linha small,.dica{font-size:18px}
.banner{font-family:"Press Start 2P";font-size:11px;box-shadow:4px 4px 0 var(--sh)}.pilhas small{font-size:18px}.campo{background:#1a1c2c;color:#fff;font-family:VT323;font-size:24px}.stepper output{font-size:26px}
.trofeu{color:var(--p1);text-shadow:4px 4px 0 var(--p2)}.codigo b{font-size:28px}.sala-item,.slot{font-size:20px}.slot b,.sala-item b{font-family:"Press Start 2P";font-size:11px}
.slot .av{font-size:9px}.peca .m+.m{border-width:4px}.peca.v .m+.m{border-width:4px}.sub2{font-size:20px}
""",
"09_papel_vintage": r"""
:root{--pn-bg:#f3e8c9;--pn-bd:2px solid #2a1a10;--pn-r:2px;--pn-sh:4px 4px 0 rgba(42,26,16,.35);--k-ac:#a8321f;--k-ac-ink:#f3e8c9;--k-mut:#6b5640;--sw-r:99px;--pip-r:50%;--tl-face:#fbf4de;--tl-ink:#2a1a10;--tl-bd:2px solid #2a1a10;--tl-r:4px;--tl-sh:2px 2px 0 rgba(42,26,16,.35);--tl-sep:#2a1a10}
.btn.on,.seg .btn.on{background:var(--red);color:#f3e8c9}.banner,.pill,.tag,.historico h4,.campo-l{font-family:"Special Elite"}.banner{font-size:16px;border-radius:2px;font-weight:400}
.campo{background:#fbf4de;font-family:"Libre Baskerville"}.trofeu{color:var(--red)}.rotulo,.codigo b,.stepper output{font-family:"Playfair Display"}.sub2{font-family:"Special Elite"}
.tag,.pill{border-radius:2px}.sw.on:after{background:#f3e8c9}
""",
"11_zen_japones": r"""
:root{--pn-bg:rgba(255,252,244,.92);--pn-bd:1.5px solid #2b2622;--pn-r:8px;--pn-sh:0 6px 0 rgba(43,38,34,.12);--k-ac:#c0392b;--k-ac-ink:#fff;--k-mut:#7a6f64;--sw-r:99px;--pip-r:50%;--tl-face:#fffaf0;--tl-ink:#2b2622;--tl-bd:1.5px solid #2b2622;--tl-r:4px;--tl-sh:0 3px 0 rgba(0,0,0,.2);--tl-sep:#2b2622}
.btn.on,.seg .btn.on{background:var(--ink);color:#efe7d6}.banner{font-family:"Shippori Mincho";letter-spacing:3px;font-weight:500}.tag{letter-spacing:2px}.campo{background:#fffaf0}
.trofeu{color:var(--red);font-family:"Shippori Mincho"}.rotulo,.codigo b,.stepper output{font-family:"Shippori Mincho"}.dom .felt{border-radius:50%}.stepper .btn{border-radius:50%}
""",
}

for pasta, (titulo, fonts, tema, css) in ESTILOS.items():
    css = css + EXTRA.get(pasta, '')
    os.makedirs(os.path.join(RAIZ, pasta), exist_ok=True)
    with open(os.path.join(RAIZ, pasta, "mockup.html"), "w", encoding="utf-8") as f:
        f.write(MODELO.format(titulo=titulo, fonts=fonts, css=css.strip(), tema=tema))
    print("ok", pasta)
