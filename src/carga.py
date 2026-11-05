"""
Carga: leva a prata para o DuckDB e constroi a camada ouro em SQL.

O banco inteiro e um arquivo (config.BANCO). Apagar esse arquivo e uma
forma legitima de recomecar do zero: a carga recria tudo a partir dos
parquets da prata.

MODELO (as frases do grao e as decisoes estao no README)
=========================================================
    ouro.dim_time            um time
    ouro.fato_jogo           uma partida
    ouro.fato_classificacao  um time em uma temporada
    ouro.vw_jogo_completo    consulta salva: a tabela achatada, recriada
                             a partir da estrela

A prata entra como esta. A ouro nasce dentro do banco, a partir dela.
"""

import logging

import duckdb

import config

log = logging.getLogger(__name__)

# nome da tabela no esquema prata -> arquivo parquet de origem
TABELAS_PRATA = {
    "odds_futebol": config.PRATA_ODDS,
    "classificacao": config.PRATA_CLASSIFICACAO,
    "classificacao_calculada": config.PRATA_CLASSIFICACAO_CALCULADA,
    "odds_enriquecido": config.PRATA_ENRIQUECIDO,
}

# ----------------------------------------------------------------- ouro
# Os nomes tecnicos da fonte viram nomes de negocio (AS): a ouro e a
# camada que pessoas consultam.

SQL_DIM_TIME = """
CREATE OR REPLACE TABLE ouro.dim_time AS
SELECT
    chave        AS time_id,
    MIN(nome)    AS nome
FROM (
    SELECT chave_casa AS chave, "HomeTeam" AS nome
    FROM prata.odds_enriquecido
    UNION ALL
    SELECT chave_visitante, "AwayTeam"
    FROM prata.odds_enriquecido
)
GROUP BY chave
"""

SQL_FATO_CLASSIFICACAO = """
CREATE OR REPLACE TABLE ouro.fato_classificacao AS
SELECT
    chave_time                  AS time_id,
    "Temporada"                 AS temporada,
    CAST(posicao AS INTEGER)    AS posicao,
    CAST(pontos AS INTEGER)     AS pontos,
    CAST(jogos AS INTEGER)      AS jogos,
    CAST(vitorias AS INTEGER)   AS vitorias,
    CAST(empates AS INTEGER)    AS empates,
    CAST(derrotas AS INTEGER)   AS derrotas,
    CAST(gols_pro AS INTEGER)   AS gols_pro,
    CAST(gols_contra AS INTEGER) AS gols_contra,
    CAST(saldo_gols AS INTEGER) AS saldo_gols
FROM prata.classificacao_calculada
"""

# O WHERE e o filtro de integridade da fato: a validacao da juncao da
# aula de enriquecimento. Posicao nula = jogo cujo time nao achou par na
# classificacao. Nesses dados nenhum e excluido, e a carga avisa se algum for.
SQL_FATO_JOGO = """
CREATE OR REPLACE TABLE ouro.fato_jogo AS
SELECT
    "Unique_ID"                 AS jogo_id,
    CAST("Date" AS DATE)        AS data,
    "Temporada"                 AS temporada,
    chave_casa                  AS time_casa_id,
    chave_visitante             AS time_visitante_id,
    CAST("FTHG" AS INTEGER)     AS gols_casa,
    CAST("FTAG" AS INTEGER)     AS gols_visitante,
    CASE "FTR"
        WHEN 'H' THEN 'casa'
        WHEN 'D' THEN 'empate'
        WHEN 'A' THEN 'visitante'
    END                         AS resultado,
    "B365H"                     AS odd_casa,
    "B365D"                     AS odd_empate,
    "B365A"                     AS odd_visitante,
    prob_casa,
    prob_empate,
    prob_visitante,
    prob_casa_faixa,
    "B365H_extremo"             AS odd_casa_extremo,
    "B365A_extremo"             AS odd_visitante_extremo
FROM prata.odds_enriquecido
WHERE posicao_casa IS NOT NULL
  AND posicao_visitante IS NOT NULL
"""

# A tabela achatada da aula de enriquecimento, agora como consulta salva:
# nao guarda dado, o banco executa o join na hora. As dimensoes entram com
# JOIN; a classificacao entra com LEFT JOIN para que um jogo sem posicao
# apareca com nulo em vez de sumir.
SQL_VIEW_JOGO_COMPLETO = """
CREATE OR REPLACE VIEW ouro.vw_jogo_completo AS
SELECT
    f.*,
    c.nome                          AS time_casa,
    v.nome                          AS time_visitante,
    pc.posicao                      AS posicao_casa,
    pv.posicao                      AS posicao_visitante,
    pc.pontos                       AS pontos_casa,
    pv.pontos                       AS pontos_visitante,
    pv.posicao - pc.posicao         AS dif_posicao,
    pc.pontos - pv.pontos           AS dif_pontos,
    pv.posicao > pc.posicao         AS mandante_melhor_posicionado
FROM ouro.fato_jogo f
JOIN ouro.dim_time c ON f.time_casa_id = c.time_id
JOIN ouro.dim_time v ON f.time_visitante_id = v.time_id
LEFT JOIN ouro.fato_classificacao pc
       ON pc.time_id = f.time_casa_id AND pc.temporada = f.temporada
LEFT JOIN ouro.fato_classificacao pv
       ON pv.time_id = f.time_visitante_id AND pv.temporada = f.temporada
"""

# Cada consulta precisa devolver zero. Prova o grao, que nao ha fato
# orfao e que a view nao multiplica linhas.
VERIFICACOES = [
    ("fato_jogo: jogo_id repetido (grao)",
     "SELECT COUNT(*) FROM (SELECT jogo_id FROM ouro.fato_jogo "
     "GROUP BY jogo_id HAVING COUNT(*) > 1)"),
    ("fato_classificacao: time e temporada repetidos (grao)",
     "SELECT COUNT(*) FROM (SELECT time_id, temporada "
     "FROM ouro.fato_classificacao "
     "GROUP BY time_id, temporada HAVING COUNT(*) > 1)"),
    ("dim_time: time_id repetido (grao)",
     "SELECT COUNT(*) FROM (SELECT time_id FROM ouro.dim_time "
     "GROUP BY time_id HAVING COUNT(*) > 1)"),
    ("fato_jogo sem o time mandante na dim_time",
     "SELECT COUNT(*) FROM ouro.fato_jogo f "
     "LEFT JOIN ouro.dim_time d ON f.time_casa_id = d.time_id "
     "WHERE d.time_id IS NULL"),
    ("fato_jogo sem o time visitante na dim_time",
     "SELECT COUNT(*) FROM ouro.fato_jogo f "
     "LEFT JOIN ouro.dim_time d ON f.time_visitante_id = d.time_id "
     "WHERE d.time_id IS NULL"),
    ("fato_classificacao sem o time na dim_time",
     "SELECT COUNT(*) FROM ouro.fato_classificacao f "
     "LEFT JOIN ouro.dim_time d ON f.time_id = d.time_id "
     "WHERE d.time_id IS NULL"),
    ("fato_jogo sem classificacao do mandante na temporada",
     "SELECT COUNT(*) FROM ouro.fato_jogo f "
     "LEFT JOIN ouro.fato_classificacao c "
     "ON c.time_id = f.time_casa_id AND c.temporada = f.temporada "
     "WHERE c.time_id IS NULL"),
    ("fato_jogo sem classificacao do visitante na temporada",
     "SELECT COUNT(*) FROM ouro.fato_jogo f "
     "LEFT JOIN ouro.fato_classificacao c "
     "ON c.time_id = f.time_visitante_id AND c.temporada = f.temporada "
     "WHERE c.time_id IS NULL"),
    ("vw_jogo_completo com linhas a mais ou a menos que a fato_jogo",
     "SELECT ABS((SELECT COUNT(*) FROM ouro.vw_jogo_completo) "
     "- (SELECT COUNT(*) FROM ouro.fato_jogo))"),
]


def um_valor(con, sql):
    # con.execute e nao con.sql: o objeto de con.sql nem sempre tem fetchone.
    return con.execute(sql).fetchone()[0]


def conectar():
    config.OURO.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(config.BANCO))


def criar_esquemas(con):
    con.execute("CREATE SCHEMA IF NOT EXISTS prata")
    con.execute("CREATE SCHEMA IF NOT EXISTS ouro")


def carregar_prata(con):
    for nome, arquivo in TABELAS_PRATA.items():
        if not arquivo.exists():
            raise FileNotFoundError(
                f"{arquivo} nao existe: rode a transformacao antes da carga")
        # as_posix troca a barra invertida do Windows pela comum, que e o
        # que o SQL espera dentro de uma string.
        caminho = arquivo.as_posix().replace("'", "''")
        con.execute(f"""
            CREATE OR REPLACE TABLE prata.{nome} AS
            SELECT * FROM read_parquet('{caminho}')
        """)
        linhas = um_valor(con, f"SELECT COUNT(*) FROM prata.{nome}")
        log.info("prata.%s: %d linhas", nome, linhas)


def construir_ouro(con):
    con.execute(SQL_DIM_TIME)
    con.execute(SQL_FATO_CLASSIFICACAO)
    con.execute(SQL_FATO_JOGO)
    con.execute(SQL_VIEW_JOGO_COMPLETO)

    for tabela in ("dim_time", "fato_classificacao", "fato_jogo"):
        linhas = um_valor(con, f"SELECT COUNT(*) FROM ouro.{tabela}")
        log.info("ouro.%s: %d linhas", tabela, linhas)

    na_prata = um_valor(con, "SELECT COUNT(*) FROM prata.odds_enriquecido")
    na_fato = um_valor(con, "SELECT COUNT(*) FROM ouro.fato_jogo")
    if na_fato != na_prata:
        log.warning("fato_jogo: %d jogos ficaram de fora por falta de posicao "
                    "(prata: %d, fato: %d)", na_prata - na_fato, na_prata, na_fato)


def conferir(con):
    problemas = []
    for descricao, sql in VERIFICACOES:
        n = um_valor(con, sql)
        if n:
            log.error("conferencia falhou: %s = %d (deveria ser 0)", descricao, n)
            problemas.append(descricao)
        else:
            log.info("conferido: %s = 0", descricao)
    if problemas:
        raise ValueError(f"{len(problemas)} conferencia(s) do modelo falharam")


def main():
    con = conectar()
    try:
        criar_esquemas(con)
        carregar_prata(con)
        construir_ouro(con)
        conferir(con)
    finally:
        # o DuckDB deixa um processo escrever por vez: fechar libera o arquivo
        con.close()
    log.info("banco pronto em %s", config.BANCO)


if __name__ == "__main__":
    config.configurar_log()
    main()
