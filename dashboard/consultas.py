"""
Consultas do painel: todo o SQL de leitura mora aqui, e so aqui.

O painel e consumidor da camada ouro, nao produtor: abre o banco em modo
somente leitura, entao nao cria nem altera nada e nao trava o arquivo para o
pipeline. Quem cria as tabelas e o dbt (pasta ecox14/).

O teste de onde uma consulta deve morar: se alguem pedir este mesmo numero
por e-mail, sem abrir o painel, a consulta existe em algum lugar
reaproveitavel? Aqui existe.

Valor que vem da tela entra como parametro (?), nunca concatenado no texto.
"""

import json
from pathlib import Path

import duckdb

# Calculado a partir deste arquivo: nao depende de onde o comando foi digitado.
RAIZ = Path(__file__).resolve().parent.parent
BANCO = RAIZ / "dados" / "ouro" / "projeto.duckdb"
PROVENIENCIA_ODDS = RAIZ / "dados" / "bronze" / "futebol" / "proveniencia.json"

# A odd embute a margem da casa de apostas: 1/odd das tres opcoes soma ~1,05.
# Dividir pela soma tira essa margem. E uma expressao fixa (nao vem da tela).
PROB_NORMALIZADA = "prob_casa / (prob_casa + prob_empate + prob_visitante)"

# Filtros opcionais: com None o filtro nao se aplica. O cast evita que o
# banco precise adivinhar o tipo de um parametro nulo.
FILTROS = """
    (cast(? as varchar) is null or temporada = ?)
    and (cast(? as boolean) is null or mandante_melhor_posicionado = ?)
"""


def _consultar(sql, parametros=None):
    con = duckdb.connect(str(BANCO), read_only=True)
    try:
        return con.execute(sql, parametros or []).df()
    finally:
        con.close()


def _filtros(temporada, mandante_melhor):
    return [temporada, temporada, mandante_melhor, mandante_melhor]


def temporadas():
    """Temporadas disponiveis na ouro, da mais antiga para a mais recente."""
    return _consultar(
        "select distinct temporada from ouro.vw_jogo_completo order by temporada"
    )


def calibracao(temporada=None, mandante_melhor=None):
    """Por faixa de favoritismo do mandante: probabilidade implicita media
    contra a frequencia real de vitoria do mandante."""
    return _consultar(
        f"""
        select
            prob_casa_faixa                                         as faixa,
            count(*)                                                as jogos,
            avg(prob_casa)                                          as prob_bruta,
            avg({PROB_NORMALIZADA})                                 as prob_normalizada,
            avg(case when resultado = 'casa' then 1.0 else 0.0 end) as freq_real
        from ouro.vw_jogo_completo
        where {FILTROS}
        group by prob_casa_faixa
        order by min(prob_casa)
        """,
        _filtros(temporada, mandante_melhor),
    )


def resumo_mandante(temporada=None, mandante_melhor=None):
    """Numeros gerais da selecao: quantos jogos, e quanto o mandante venceu
    contra o que o mercado esperava."""
    return _consultar(
        f"""
        select
            count(*)                                                as jogos,
            avg(case when resultado = 'casa' then 1.0 else 0.0 end) as freq_real,
            avg({PROB_NORMALIZADA})                                 as prob_normalizada
        from ouro.vw_jogo_completo
        where {FILTROS}
        """,
        _filtros(temporada, mandante_melhor),
    )


def fonte():
    """De onde vieram as odds, segundo a proveniencia gravada na ingestao.
    Devolve None se o arquivo nao existir (ex.: bronze ainda nao baixada)."""
    try:
        return json.loads(PROVENIENCIA_ODDS.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
