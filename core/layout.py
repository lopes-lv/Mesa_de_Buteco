"""
layout.py - Fonte única dos valores de layout das telas de mesa (tamanho de
cartas/peças, espaçamentos, botões), para não ficarem repetidos em cada tela
(host e cliente remoto de cada modo liam cópias próprias das mesmas
constantes).

Os padrões vivem em config/layout_padrao.json, cada item com `valor` e os
metadados `min`/`max`/`passo`/`rotulo` (validação aqui + base pro editor
visual montar a interface sozinho). Ajustes do usuário ficam em
config/layout.json, só com os itens que diferem do padrão - arquivo
opcional: ausente, corrompido ou com um item de formato errado nunca derruba
o jogo, o item afetado só volta pro padrão.

Uso: `layout.obter("holdem.carta_jogador")` -> `(100, 140)`. Tamanhos voltam
como tupla de ints, o resto como int. Os valores são lidos na hora do uso
(não copiados para constantes de módulo), então um `recarregar()` vale a
partir do próximo frame/tela.
"""
import json
import os
import sys
from typing import Any

ARQUIVO_PADRAO = "layout_padrao.json"
ARQUIVO_USUARIO = "layout.json"

_itens: Any = None  # {"grupo.chave": item do JSON padrão (dict com "valor", "min", ...)}
_padroes: dict = {}  # {"grupo.chave": valor padrão já normalizado}
_valores: dict = {}  # {"grupo.chave": valor em uso}


def _pasta_projeto():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def caminho_padrao():
    # No .exe do PyInstaller o padrão vai embutido (extraído em sys._MEIPASS).
    return os.path.join(getattr(sys, "_MEIPASS", _pasta_projeto()), "config", ARQUIVO_PADRAO)


def caminho_usuario():
    # No .exe fica ao lado do executável, para poder ser editado sem recompilar.
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = _pasta_projeto()
    return os.path.join(base, "config", ARQUIVO_USUARIO)


def _eh_numero(valor):
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def _limitar(valor, minimo, maximo):
    if minimo is not None:
        valor = max(minimo, valor)
    if maximo is not None:
        valor = min(maximo, valor)
    return valor


def _normalizar(valor, item):
    """Confere `valor` contra o formato do padrão do item (número ou lista de
    números do mesmo tamanho) e aplica min/max. None se o formato não bate."""
    padrao = item["valor"]
    if isinstance(padrao, list):
        if isinstance(valor, tuple):
            valor = list(valor)
        if (not isinstance(valor, list) or len(valor) != len(padrao)
                or not all(_eh_numero(v) for v in valor)):
            return None
        minimos = item.get("min") or [None] * len(padrao)
        maximos = item.get("max") or [None] * len(padrao)
        return tuple(_limitar(int(v), lo, hi) for v, lo, hi in zip(valor, minimos, maximos, strict=True))
    if not _eh_numero(valor):
        return None
    return _limitar(int(valor), item.get("min"), item.get("max"))


def _ler_json(caminho):
    """Dict do arquivo, ou {} se ausente/corrompido/não for um objeto JSON."""
    try:
        with open(caminho, encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
    except (OSError, ValueError):
        return {}
    return dados if isinstance(dados, dict) else {}


def _aplicar_ajustes_validos(ajustes):
    """Aplica sobre os valores em uso cada item válido de `ajustes` (formato
    do layout.json: {"grupo": {"nome": valor}}); o resto é ignorado."""
    for grupo, itens_grupo in ajustes.items():
        if not isinstance(itens_grupo, dict):
            continue  # inclui chaves de comentário como "_sobre"
        for nome, valor in itens_grupo.items():
            chave = f"{grupo}.{nome}"
            if chave in _itens:
                normalizado = _normalizar(valor, _itens[chave])
                if normalizado is not None:
                    _valores[chave] = normalizado


def carregar():
    """(Re)lê o padrão e os ajustes do usuário. Chamado sozinho no primeiro
    `obter()`; chamar de novo equivale a recarregar do disco."""
    global _itens
    with open(caminho_padrao(), encoding="utf-8") as arquivo:
        padrao = json.load(arquivo)

    _itens = {}
    _padroes.clear()
    _valores.clear()
    for grupo, itens_grupo in padrao.items():
        if grupo.startswith("_"):
            continue
        for nome, item in itens_grupo.items():
            chave = f"{grupo}.{nome}"
            _itens[chave] = item
            _padroes[chave] = _normalizar(item["valor"], item)
            _valores[chave] = _padroes[chave]

    _aplicar_ajustes_validos(_ler_json(caminho_usuario()))


recarregar = carregar


def _garantir_carregado():
    if _itens is None:
        carregar()


def obter(chave):
    """Valor em uso de `chave` ("grupo.nome"). Chave inexistente levanta
    KeyError de propósito - erro de digitação tem que aparecer na hora."""
    _garantir_carregado()
    return _valores[chave]


def chaves():
    _garantir_carregado()
    return list(_itens)


def metadados(chave):
    """O item do JSON padrão (valor padrão, min, max, passo, rotulo)."""
    _garantir_carregado()
    return dict(_itens[chave])


def padrao(chave):
    """Valor padrão de `chave` (do layout_padrao.json), no mesmo formato de
    `obter()`."""
    _garantir_carregado()
    return _padroes[chave]


def definir(chave, valor):
    """Altera o valor em memória (aplicando min/max). Use `salvar()` para
    persistir."""
    _garantir_carregado()
    normalizado = _normalizar(valor, _itens[chave])
    if normalizado is None:
        raise ValueError(f"Valor inválido para {chave}: {valor!r}")
    _valores[chave] = normalizado
    return normalizado


def restaurar_padrao(chave=None):
    """Volta um item (ou todos, com `chave=None`) ao padrão, em memória."""
    _garantir_carregado()
    for k in [chave] if chave else list(_valores):
        _valores[k] = _padroes[k]


def ajustes_atuais():
    """Os valores em uso que diferem do padrão, no formato do layout.json."""
    _garantir_carregado()
    ajustes: dict = {}
    for chave, valor in _valores.items():
        if valor != _padroes[chave]:
            grupo, nome = chave.split(".", 1)
            ajustes.setdefault(grupo, {})[nome] = list(valor) if isinstance(valor, tuple) else valor
    return ajustes


def aplicar_ajustes(ajustes):
    """Volta tudo ao padrão e aplica `ajustes` (formato do layout.json), em
    memória. Use `salvar()` para persistir."""
    _garantir_carregado()
    restaurar_padrao()
    _aplicar_ajustes_validos(ajustes)


def _gravar_json(caminho, dados):
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=2)
        arquivo.write("\n")
    return caminho


def salvar():
    """Grava em config/layout.json só os itens que diferem do padrão."""
    return _gravar_json(caminho_usuario(), ajustes_atuais())


# ---------- Presets: conjuntos nomeados de ajustes, no mesmo formato ----------
# Os que vêm com o jogo ficam em config/presets_padrao/ (versionados e
# embutidos no .exe); os criados pelo editor, em config/presets/ ao lado do
# layout.json do usuário. Exportar/importar = copiar o .json pra/dessa pasta.
PASTA_PRESETS_PADRAO = "presets_padrao"
PASTA_PRESETS_USUARIO = "presets"


def pasta_presets_padrao():
    return os.path.join(os.path.dirname(caminho_padrao()), PASTA_PRESETS_PADRAO)


def pasta_presets_usuario():
    return os.path.join(os.path.dirname(caminho_usuario()), PASTA_PRESETS_USUARIO)


def nome_arquivo_preset(nome):
    """Nome de arquivo seguro pro preset (só letras, números, espaço, - e _),
    ou None se não sobrar nada."""
    limpo = "".join(c for c in nome.strip() if c.isalnum() or c in " -_").strip()
    return f"{limpo}.json" if limpo else None


def listar_presets():
    """[(nome, "padrao" | "usuario", descrição)], os do jogo primeiro. Um
    preset do usuário com o mesmo nome de um do jogo tem prioridade."""
    presets = {}
    for origem, pasta in (("padrao", pasta_presets_padrao()), ("usuario", pasta_presets_usuario())):
        try:
            arquivos = sorted(f for f in os.listdir(pasta) if f.lower().endswith(".json"))
        except OSError:
            continue
        for arquivo in arquivos:
            dados = _ler_json(os.path.join(pasta, arquivo))
            sobre = dados.get("_sobre", "")
            presets[arquivo[:-5]] = (arquivo[:-5], origem, sobre if isinstance(sobre, str) else "")
    return sorted(presets.values(), key=lambda p: (p[1] != "padrao", p[0].lower()))


def carregar_preset(nome):
    """Aplica o preset `nome` em memória (como aplicar_ajustes). False se
    não existir."""
    for pasta in (pasta_presets_usuario(), pasta_presets_padrao()):
        caminho = os.path.join(pasta, f"{nome}.json")
        if os.path.exists(caminho):
            aplicar_ajustes(_ler_json(caminho))
            return True
    return False


def salvar_preset(nome):
    """Grava os ajustes atuais como preset do usuário. Devolve o caminho, ou
    None se o nome for inválido."""
    arquivo = nome_arquivo_preset(nome)
    if arquivo is None:
        return None
    return _gravar_json(os.path.join(pasta_presets_usuario(), arquivo), ajustes_atuais())
