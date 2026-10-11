"""Gera previa_baralhos.png (folha de contato dos 8 baralhos) e baralhos.html
(galeria no navegador, gerada a partir do mesmo dicionário SKINS).
Uso, a partir da raiz do projeto:  python design/baralhos/previa_baralhos.py"""
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import pygame
import baralhos_skins as bs


class C:  # carta de teste com o mesmo contrato de core/deck.Card
    def __init__(self, texto, naipe, simbolo):
        self.texto, self.naipe, self.simbolo_naipe = texto, naipe, simbolo


MAO = [C("A", "espadas", "S"), C("K", "copas", "H"), C("10", "ouros", "D"), C("Q", "paus", "C"), C("JK", "coringa", "★")]


def png():
    pygame.init()
    W, H = 64, 90
    fundo = (120, 120, 120)
    tela = pygame.Surface((8 + 7 * (W + 14) + 150, 16 + len(bs.ORDEM_SKINS) * (H + 36)))
    tela.fill(fundo)
    fonte = pygame.font.SysFont("Segoe UI", 15, bold=True)
    for i, sid in enumerate(bs.ORDEM_SKINS):
        y = 12 + i * (H + 36)
        tela.blit(fonte.render(f"{i + 1}. {bs.ROTULOS_SKINS[sid]}", True, (255, 255, 255)), (10, y - 4))
        x = 10
        yy = y + 18
        for c in MAO:
            bs.desenhar_carta_skin(tela, sid, x, yy, W, H, carta=c); x += W + 14
        bs.desenhar_carta_skin(tela, sid, x, yy, W, H, virada_para_baixo=True); x += W + 14
        bs.desenhar_carta_skin(tela, sid, x, yy, W, H, vazia=True); x += W + 14
        bs.desenhar_carta_skin(tela, sid, x, yy, W, H, carta=MAO[0], destaque=True)
    pygame.image.save(tela, os.path.join(AQUI, "previa_baralhos.png"))


def css_cor(c):
    c = bs._rgba(c)
    return f"rgba({c[0]},{c[1]},{c[2]},{c[3] / 255:.2f})"


FONTE_CSS = {"mono": "Consolas,'Courier New',monospace", "serif": "Georgia,'Times New Roman',serif",
             "sans": "'Segoe UI',Verdana,sans-serif", "pixel": "Consolas,'Courier New',monospace"}
PADRAO_CSS = {
    "losango": "none", "moldura": "none",
    "rede": "repeating-linear-gradient(45deg,{c} 0 1px,transparent 1px 8px),repeating-linear-gradient(-45deg,{c} 0 1px,transparent 1px 8px)",
    "listras": "repeating-linear-gradient(45deg,{c} 0 2px,transparent 2px 8px)",
    "xadrez": "repeating-conic-gradient({c} 0 25%,transparent 0 50%) 0 0/16px 16px",
    "quadrado": "linear-gradient({c},{c}) center/30% 22% no-repeat",
    "circulo": "radial-gradient(ellipse {c} 0 40%,transparent 41%)",
    "neon": "none"}


def html():
    css, corpo = [], []
    for sid in bs.ORDEM_SKINS:
        s = bs.SKINS[sid]
        sh = s["sombra"]
        sombra = f"{sh[0]}px {sh[1]}px 0 {css_cor(sh[2])}" if sh and bs._rgba(sh[2])[3] else "none"
        if s["glow"]:
            sombra = f"0 0 14px {css_cor(s['glow'])}, 0 0 4px {css_cor(s['glow'])}"
        pad = PADRAO_CSS[s["padrao"]].format(c=css_cor(s["padrao_cor"]))
        fundo_verso = (f"linear-gradient({css_cor(s['verso_a'])},{css_cor(s['verso_b'])})" if s["verso_b"]
                       else css_cor(s["verso_a"]))
        extra = ""
        if s["padrao"] in ("losango", "moldura", "neon"):
            extra = (f".{sid} .verso:after{{content:'';position:absolute;left:50%;top:50%;width:44%;height:31%;"
                     f"transform:translate(-50%,-50%) rotate(45deg) scale(.85);border:2px solid {css_cor(s['padrao_cor'])};"
                     f"{'box-shadow:0 0 8px '+css_cor(s['padrao_cor'])+';' if s['padrao']=='neon' else ''}}}")
        borda_v = css_cor(s.get("borda_vermelha") or s["borda"])
        css.append(f""".{sid} .c{{width:64px;height:90px;position:relative;box-sizing:border-box;background:{css_cor(s['face'])};
border:{s['borda_w']}px solid {css_cor(s['borda'])};border-radius:{s['raio']}px;box-shadow:{sombra};color:{css_cor(s['tinta'])};
font:700 17px {FONT_CSS_PLACEHOLDER};display:grid;place-items:center}}
.{sid} .c.v{{color:{css_cor(s['vermelho'])};border-color:{borda_v}}}
.{sid} .c b{{position:absolute;left:6px;top:4px}}.{sid} .c b+b{{left:auto;top:auto;right:6px;bottom:4px;transform:rotate(180deg)}}
.{sid} .c span{{font-size:36px;line-height:1}}
.{sid} .verso{{background:{(pad + ', ') if pad != 'none' else ''}{fundo_verso};border:{max(2, s['borda_w'])}px solid {css_cor(s['verso_borda'])}}}
.{sid} .vazia{{background:transparent;border:2px dashed {css_cor(s['vazia'])};box-shadow:none}}
.{sid} .dest{{border-color:#ffc93c;box-shadow:0 0 0 2px #ffc93c}}
{extra}""".replace(FONT_CSS_PLACEHOLDER, FONTE_CSS[s["fonte"]]))
        cartas = "".join(
            f"<div class='c{' v' if c.naipe in ('copas', 'ouros') else ''}'><b>{c.texto}</b><span>{ {'S':'♠','H':'♥','D':'♦','C':'♣','★':'★'}[c.simbolo_naipe] }</span><b>{c.texto}</b></div>"
            for c in MAO)
        corpo.append(f"<section class='{sid}'><h2>{bs.ROTULOS_SKINS[sid]} <code>{sid}</code></h2><div class='row'>{cartas}"
                     f"<div class='c verso'></div><div class='c vazia'></div>"
                     f"<div class='c dest'><b>A</b><span>♠</span><b>A</b></div></div></section>")
    pagina = ("<!doctype html><html lang='pt-BR'><head><meta charset='utf-8'><title>Baralhos — poker_game</title><style>"
              "body{margin:0;padding:28px;background:#6f6f6f;font:15px system-ui,sans-serif;color:#fff}"
              "h1{margin:0 0 20px}h2{margin:26px 0 10px;font-size:16px}code{opacity:.7;font-weight:400;margin-left:8px}"
              ".row{display:flex;gap:14px;flex-wrap:wrap}"
              + "\n".join(css) + "</style></head><body><h1>Baralhos dos 8 estilos novos</h1>"
              "<p>Ids usados em <code>baralhos_skins.py</code>. Prévia em HTML aproximada; a referência é o PNG gerado pelo Pygame.</p>"
              + "".join(corpo) + "</body></html>")
    with open(os.path.join(AQUI, "baralhos.html"), "w", encoding="utf-8") as f:
        f.write(pagina)


FONT_CSS_PLACEHOLDER = "@@FONT@@"

if __name__ == "__main__":
    png()
    html()
    print("ok: previa_baralhos.png e baralhos.html")
