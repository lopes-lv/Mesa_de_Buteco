"""CN-* — consistência do código: constantes e funções repetidas.

Procura, por análise do código (módulo `ast`), o que o QA não enxerga: várias
variáveis para a mesma coisa e funções copiadas de uma tela para outra.

Dois tipos de teste:
- "catraca" (ratchet): a duplicação que já existe está listada abaixo e passa;
  uma duplicação NOVA reprova, com a mensagem de onde mover o valor. Se a
  repetição for proposital, acrescente à lista com um comentário do motivo.
- "dívida" (xfail): afirmam o estado ideal (cada coisa definida num lugar só).
  Falham hoje, de propósito. Para ver a lista completa:
      pytest tests/test_consistencia.py --runxfail -k divida
  Quando uma dívida for paga, o teste passa a dar XPASS: tire a marca xfail e
  apague a linha correspondente da lista de "conhecidas".

core/ui_pixelart.py fica de fora: é código antigo mantido só como referência
(CLAUDE.md) e repete de propósito os nomes de core/ui_theme.py.
"""
import ast
import collections
import functools
import json
import os

import pytest

from tests.conftest import RAIZ

PACOTES = ["core", "holdem", "pifpaf", "domino", "menus", "rede"]
IGNORADOS = {"ui_pixelart.py"}
MIN_COMANDOS_FUNCAO = 3        # funções menores que isso não contam como cópia


def _arquivos():
    caminhos = ["main.py"]
    for pacote in PACOTES:
        caminhos += [f"{pacote}/{nome}" for nome in sorted(os.listdir(os.path.join(RAIZ, pacote)))
                     if nome.endswith(".py") and nome not in IGNORADOS]
    return caminhos


@functools.lru_cache(maxsize=None)
def _arvore(caminho):
    with open(os.path.join(RAIZ, caminho), encoding="utf-8") as f:
        return ast.parse(f.read())


def _constantes():
    """{nome: [(arquivo, valor)]} das constantes de módulo (NOME_EM_MAIUSCULAS = ...)."""
    achadas = collections.defaultdict(list)
    for caminho in _arquivos():
        for no in _arvore(caminho).body:
            if not isinstance(no, ast.Assign):
                continue
            for alvo in no.targets:
                if isinstance(alvo, ast.Name) and alvo.id.lstrip("_").isupper():
                    try:
                        valor = ast.literal_eval(no.value)
                    except ValueError:
                        valor = "<expr> " + ast.unparse(no.value)
                    achadas[alvo.id].append((caminho, valor))
    return achadas


def _funcoes_copiadas():
    """[(nomes, tamanho_do_grupo, arquivos)] de funções com corpo idêntico em
    lugares diferentes (o docstring não conta)."""
    grupos = collections.defaultdict(list)
    for caminho in _arquivos():
        for no in ast.walk(_arvore(caminho)):
            if not isinstance(no, ast.FunctionDef) or (no.name.startswith("__") and no.name.endswith("__")):
                continue
            corpo = list(no.body)
            if corpo and isinstance(corpo[0], ast.Expr) and isinstance(getattr(corpo[0], "value", None), ast.Constant) \
                    and isinstance(corpo[0].value.value, str):
                corpo = corpo[1:]
            if len(corpo) >= MIN_COMANDOS_FUNCAO:
                grupos[ast.dump(ast.Module(body=corpo, type_ignores=[]))].append((caminho, no.name))
    return [("|".join(sorted({nome for _, nome in lista})), len(lista), sorted(c for c, _ in lista))
            for lista in grupos.values() if len(lista) > 1]


# ---------------------------------------------------------------- Conhecidas (catraca)
# Constantes com o MESMO NOME definidas em mais de um módulo (valores iguais).
CONSTANTES_REPETIDAS_CONHECIDAS = {
    "ANIM_CROUPIER_DURACAO", "HIST_LARGURA", "HIST_MARGEM", "HIST_MAX_LINHAS", "VAO_PAINEL_CARTAS_BOT",
    "LIMIAR_ARRASTO_PX", "MEIA_LARGURA_ASSENTO", "NAIPE_UNICODE", "PALETA_AVATAR",
    "TIPO_BOT", "TIPO_HUMANO_LOCAL", "TIPO_HUMANO_REMOTO",
}
# Nomes repetidos cujo valor DIFERE de propósito entre jogos (cada jogo tem o seu).
VALOR_DIFERENTE_ENTRE_JOGOS = {"MEIA_LARGURA_ASSENTO"}    # Hold'em 112; Pif Paf e Dominó 97

# Constantes com NOMES DIFERENTES e o mesmo valor (podem ser coincidência; revise).
VALORES_IGUAIS_CONHECIDOS = {
    ("int", 60): {"FPS", "MAX_MENSAGENS"},                       # coincidência
    ("int", 24): {"FOLGA_BOTAO_PASSAR", "HIST_MARGEM"},          # coincidência
    ("int", 70): {"FOLGA_ASSENTO", "FOLGA_ASSENTO_BAIXO"},       # provável duplicação
}

# Funções copiadas (nomes, quantidade de cópias).
FUNCOES_COPIADAS_CONHECIDAS = {
    ("_posicoes_assentos", 2), ("_iniciais", 6), ("_meu_jogador", 3), ("_desenhar_botao_sair", 6),
    ("_desenhar_mensagem_final", 3), ("_desenhar_tela_final", 3), ("_enviar_chat_host", 3),
    ("_broadcast_estado", 2), ("_tamanho_peca", 2), ("_mesa_rect", 2), ("_rects_pilha_escolha", 2),
    ("_desenhar_embaralhando", 2), ("_rects_mao|_rects_mao_pecas", 2),
}

# Chaves do layout_padrao.json com o mesmo valor (podem ser coincidência).
VALORES_IGUAIS_NO_LAYOUT_CONHECIDOS = [
    {"geral.borda", "holdem.espaco_cartas_oponente", "domino.espaco_mesa"},
    {"geral.delay_bot_normal_ms", "pifpaf.delay_bot_ms"},
    {"holdem.carta_oponente", "pifpaf.carta_oponente"},
    {"holdem.deslocamento_cartas_jogador", "pifpaf.espaco_monte"},
    {"holdem.espaco_cartas_jogador", "domino.espaco_mao"},
    {"holdem.espaco_botoes", "pifpaf.espaco_botoes"},
    {"pifpaf.espaco_mao", "domino.espaco_pilha_escolha"},
    {"pifpaf.botao_compra", "pifpaf.botao_jogada"},
]


# ---------------------------------------------------------------- Constantes
def test_cn_01_constante_com_o_mesmo_nome_tem_o_mesmo_valor_em_todo_lugar():
    divergentes = {}
    for nome, definicoes in _constantes().items():
        if len(definicoes) > 1 and len({repr(v) for _, v in definicoes}) > 1:
            divergentes[nome] = definicoes
    inesperadas = {n: d for n, d in divergentes.items() if n not in VALOR_DIFERENTE_ENTRE_JOGOS}
    assert not inesperadas, f"mesmo nome, valores diferentes (um deles deve estar errado): {inesperadas}"


def test_cn_01_o_valor_que_difere_de_proposito_e_igual_dentro_de_cada_jogo():
    for nome in VALOR_DIFERENTE_ENTRE_JOGOS:
        por_jogo = collections.defaultdict(set)
        for caminho, valor in _constantes()[nome]:
            por_jogo[caminho.split("/")[0]].add(repr(valor))
        assert all(len(valores) == 1 for valores in por_jogo.values()), f"{nome}: {dict(por_jogo)}"


def test_cn_02_nenhuma_constante_nova_foi_repetida_em_varios_modulos():
    repetidas = {nome for nome, d in _constantes().items() if len({c for c, _ in d}) > 1}
    novas = repetidas - CONSTANTES_REPETIDAS_CONHECIDAS
    assert not novas, (f"constante definida em mais de um módulo: {sorted(novas)}. Defina uma vez (em core/ ou "
                       f"em config/layout_padrao.json) e importe; se a repetição for proposital, acrescente "
                       f"a CONSTANTES_REPETIDAS_CONHECIDAS com o motivo.")


def test_cn_03_nenhum_valor_novo_aparece_com_dois_nomes_diferentes():
    porvalor = collections.defaultdict(set)
    for nome, definicoes in _constantes().items():
        for _, valor in definicoes:
            if isinstance(valor, (int, float, str)) and not isinstance(valor, bool) \
                    and valor not in (0, 1, 2, 3, 4, 5, 10, "") and not str(valor).startswith("<expr>"):
                porvalor[(type(valor).__name__, valor)].add(nome)
    novos = {v: sorted(n) for v, n in porvalor.items()
             if len(n) > 1 and n != VALORES_IGUAIS_CONHECIDOS.get(v)}
    assert not novos, (f"mesmo valor com nomes diferentes: {novos}. Se for a mesma coisa, use uma constante só; "
                       f"se for coincidência, acrescente a VALORES_IGUAIS_CONHECIDOS.")


def test_cn_04_o_stack_padrao_do_motor_e_o_das_fichas_iniciais_do_layout():
    from core import layout
    from holdem.game_logic import STACK_INICIAL
    assert STACK_INICIAL == layout.padrao("geral.fichas_iniciais")


@pytest.mark.parametrize("nome", ["TIPO_BOT", "TIPO_HUMANO_LOCAL", "TIPO_HUMANO_REMOTO"])
def test_cn_05_os_tres_motores_usam_os_mesmos_valores_de_tipo_de_jogador(nome):
    from domino import domino_logic
    from holdem import game_logic
    from pifpaf import pifpaf_logic
    assert getattr(game_logic, nome) == getattr(pifpaf_logic, nome) == getattr(domino_logic, nome)


@pytest.mark.parametrize("nome", ["ANIM_CROUPIER_DURACAO", "HIST_LARGURA", "HIST_MARGEM", "HIST_MAX_LINHAS",
                                  "VAO_PAINEL_CARTAS_BOT", "PALETA_AVATAR"])
def test_cn_06_hold_em_host_e_cliente_remoto_nao_divergem(nome):
    """O CLAUDE.md avisa 'mude os dois': esta é a trava contra esquecer um."""
    from holdem import mesa_remota_screen, table_screen
    assert repr(getattr(table_screen, nome)) == repr(getattr(mesa_remota_screen, nome))


def test_cn_06_os_simbolos_dos_naipes_sao_iguais_nas_telas_que_os_definem():
    from pifpaf import mesa_remota_pifpaf_screen, pifpaf_screen
    from holdem import table_screen
    assert table_screen.NAIPE_UNICODE == pifpaf_screen.NAIPE_UNICODE == mesa_remota_pifpaf_screen.NAIPE_UNICODE


# ---------------------------------------------------------------- Layout
def test_cn_07_nenhum_valor_novo_se_repete_em_chaves_diferentes_do_layout():
    with open(os.path.join(RAIZ, "config", "layout_padrao.json"), encoding="utf-8") as f:
        padrao = json.load(f)
    porvalor = collections.defaultdict(set)
    for grupo, itens in padrao.items():
        if grupo.startswith("_") or grupo == "cores":
            continue
        for nome, item in itens.items():
            porvalor[json.dumps(item["valor"])].add(f"{grupo}.{nome}")
    novos = [sorted(chaves) for valor, chaves in porvalor.items()
             if len(chaves) > 1 and valor not in ("0", "1") and chaves not in VALORES_IGUAIS_NO_LAYOUT_CONHECIDOS]
    assert not novos, (f"chaves do layout com o mesmo valor: {novos}. Se medem a mesma coisa, use uma chave só; "
                       f"se for coincidência, acrescente a VALORES_IGUAIS_NO_LAYOUT_CONHECIDOS.")


# ---------------------------------------------------------------- Funções
def test_cn_08_nenhuma_funcao_nova_foi_copiada_entre_telas():
    atuais = {(nomes, tamanho) for nomes, tamanho, _ in _funcoes_copiadas()}
    novas = atuais - FUNCOES_COPIADAS_CONHECIDAS
    assert not novas, (f"funções com corpo idêntico em mais de um lugar: {sorted(novas)}. Extraia para um módulo "
                       f"comum (core/ui_theme.py ou core/) e importe; se a cópia for proposital, acrescente a "
                       f"FUNCOES_COPIADAS_CONHECIDAS.")


# ---------------------------------------------------------------- Dívidas (xfail de propósito)
@pytest.mark.xfail(reason="DÍVIDA: TIPO_BOT, TIPO_HUMANO_LOCAL e TIPO_HUMANO_REMOTO são definidos 3 vezes "
                          "(game_logic, pifpaf_logic, domino_logic). Mover para core/ e importar nos motores.")
@pytest.mark.parametrize("nome", ["TIPO_BOT", "TIPO_HUMANO_LOCAL", "TIPO_HUMANO_REMOTO"])
def test_cn_09_divida_tipos_de_jogador_definidos_num_lugar_so(nome):
    arquivos = [c for c, _ in _constantes()[nome]]
    assert len(arquivos) == 1, f"{nome} definido em {arquivos}"


@pytest.mark.xfail(reason="DÍVIDA: o Hold'em duplica as constantes e a geometria entre table_screen.py e "
                          "mesa_remota_screen.py (HIST_*, ANIM_CROUPIER_DURACAO, VAO_PAINEL_CARTAS_BOT, "
                          "NAIPE_UNICODE, PALETA_AVATAR, LIMIAR_ARRASTO_PX). Pif Paf e Dominó já importam a "
                          "geometria do host, mas PALETA_AVATAR existe em 6 telas.")
def test_cn_10_divida_constantes_de_tela_definidas_num_lugar_so():
    repetidas = {n: sorted({c for c, _ in d}) for n, d in _constantes().items() if len({c for c, _ in d}) > 1}
    assert not repetidas, f"constantes em mais de um módulo: {repetidas}"


@pytest.mark.xfail(reason="DÍVIDA: 15 grupos de funções idênticas entre telas de host e de cliente remoto "
                          "(_iniciais e _desenhar_botao_sair 6 vezes cada; _meu_jogador, _desenhar_tela_final, "
                          "_desenhar_mensagem_final, _enviar_chat_host 3 vezes...). Extrair para core/.")
def test_cn_11_divida_funcoes_de_tela_sem_copias():
    copiadas = [(nomes, tamanho) for nomes, tamanho, _ in _funcoes_copiadas()]
    assert not copiadas, f"funções com corpo idêntico em vários lugares: {sorted(copiadas)}"
