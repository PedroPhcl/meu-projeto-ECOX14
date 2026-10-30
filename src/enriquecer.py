"""Enriquecimento: junta a prata de odds com duas tabelas de classificacao.

Junção A (principal): classificacao calculada dos proprios jogos
    chave (Temporada, time), 20 times por temporada.
Junção B (demonstrativa): classificacao do TheSportsDB
    chave time, so 5 times e so a temporada 2024/25, que nao existe nas odds.
    Fica no arquivo com a temporada no nome da coluna e nao entra na analise.

Grao do resultado: 1 linha por jogo (o mesmo das odds).
"""

import json
import logging
from datetime import datetime

import pandas as pd

import config
import limpeza

PRATA = config.PRATA

log = logging.getLogger(__name__)


def carregar():
    odds = pd.read_parquet(config.PRATA_ODDS)
    calculada = pd.read_parquet(config.PRATA_CLASSIFICACAO_CALCULADA)
    tsdb = pd.read_parquet(config.PRATA_CLASSIFICACAO)
    log.info("odds: %s (1 linha por jogo)", odds.shape)
    log.info("calculada: %s (1 linha por time e temporada)", calculada.shape)
    log.info("tsdb: %s (1 linha por time, so 2024/25)", tsdb.shape)
    return odds, calculada, tsdb


def criar_chaves(odds):
    odds["chave_casa"] = limpeza.chave_texto(odds["HomeTeam"])
    odds["chave_visitante"] = limpeza.chave_texto(odds["AwayTeam"])
    return odds


def conferir_chaves(esquerda, direita, nome):
    """Passo 1 da aula: preve o que a juncao vai fazer, antes de juntar."""
    so_esq = esquerda - direita
    so_dir = direita - esquerda
    log.info("chaves [%s] so nas odds: %d | so na classificacao: %d | nos dois: %d",
             nome, len(so_esq), len(so_dir), len(esquerda & direita))
    return so_esq, so_dir


def validar(esquerda, resultado, coluna_nova, nome):
    """Passo 3 da aula: a contagem antes e depois precisa fechar."""
    sem_par = resultado[coluna_nova].isna()
    if len(resultado) != len(esquerda):
        raise ValueError(f"[{nome}] o numero de linhas mudou: o grao mudou")
    log.info("[%s] esquerda: %d | resultado: %d | sem par: %d",
             nome, len(esquerda), len(resultado), sem_par.sum())
    if sem_par.any():
        log.warning("[%s] %d linhas sem par", nome, sem_par.sum())
    return resultado[sem_par]


def juntar_calculada(odds, calculada):
    """Anexa posicao e pontos do mandante e do visitante na temporada."""
    base = calculada[["Temporada", "chave_time", "posicao", "pontos",
                      "saldo_gols"]]
    chaves_odds = set(zip(odds["Temporada"], odds["chave_casa"])) | set(
        zip(odds["Temporada"], odds["chave_visitante"]))
    chaves_tab = set(zip(base["Temporada"], base["chave_time"]))
    conferir_chaves(chaves_odds, chaves_tab, "calculada")

    resultado = odds
    sem_par = {}
    for lado, chave in (("casa", "chave_casa"), ("visitante", "chave_visitante")):
        renomear = {
            "chave_time": chave,
            "posicao": f"posicao_{lado}",
            "pontos": f"pontos_{lado}",
            "saldo_gols": f"saldo_gols_{lado}",
        }
        resultado = resultado.merge(
            base.rename(columns=renomear),
            on=["Temporada", chave],
            how="left",
            validate="many_to_one",
        )
        sem_par[lado] = validar(odds, resultado, f"posicao_{lado}",
                                f"calculada/{lado}")
    return resultado, sem_par["casa"], sem_par["visitante"]


def juntar_tsdb(odds, tsdb):
    """Anexa a posicao 2024/25 do mandante. So 5 times casam, por limite da API."""
    base = tsdb[["chave_time", "intRank", "intPoints"]].rename(columns={
        "chave_time": "chave_casa",
        "intRank": "tsdb_pos_2425_casa",
        "intPoints": "tsdb_pontos_2425_casa",
    })
    conferir_chaves(set(odds["chave_casa"]), set(base["chave_casa"]), "tsdb")
    resultado = odds.merge(base, on="chave_casa", how="left",
                           validate="many_to_one")
    sem_par = validar(odds, resultado, "tsdb_pos_2425_casa", "tsdb/casa")
    return resultado, sem_par


def descrever_nao_casados(sem_par, nome, coluna="HomeTeam"):
    times = sorted(sem_par[coluna].unique())
    if times:
        log.info("[%s] times sem par (%d): %s", nome, len(times), ", ".join(times))
    else:
        log.info("[%s] todos os times tiveram par", nome)


def criar_atributos_pos_juncao(df):
    """So existem depois da juncao: dependem de colunas de outra tabela."""
    df["dif_posicao"] = df["posicao_visitante"] - df["posicao_casa"]
    df["dif_pontos"] = df["pontos_casa"] - df["pontos_visitante"]
    df["mandante_melhor_posicionado"] = df["dif_posicao"] > 0
    return df


def salvar(df):
    destino = config.PRATA_ENRIQUECIDO
    df.to_parquet(destino, index=False)
    log.info("salvo em: %s %s", destino, df.shape)
    return destino


def registrar(destino, antes, depois, decisoes):
    info = {
        "origem": ["odds_futebol.parquet", "classificacao_calculada.parquet",
                   "classificacao.parquet"],
        "arquivo_prata": destino.name,
        "linhas_antes": antes,
        "linhas_depois": depois,
        "decisoes": decisoes,
        "transformado_em": datetime.now().isoformat(timespec="seconds"),
    }
    with config.PRATA_PROVENIENCIA.open("a", encoding="utf-8") as f:
        f.write(json.dumps(info, ensure_ascii=False) + "\n")


def main():
    odds, calculada, tsdb = carregar()
    antes = len(odds)
    odds = criar_chaves(odds)

    df, sem_casa, sem_visitante = juntar_calculada(odds, calculada)
    descrever_nao_casados(sem_casa, "calculada/casa", "HomeTeam")
    descrever_nao_casados(sem_visitante, "calculada/visitante", "AwayTeam")

    df, sem_par_tsdb = juntar_tsdb(df, tsdb)
    descrever_nao_casados(sem_par_tsdb, "tsdb")

    df = criar_atributos_pos_juncao(df)
    destino = salvar(df)
    registrar(destino, antes, len(df), [
        "juncao left com validate many_to_one, uma vez para o mandante e "
        "outra para o visitante, chave (Temporada, chave_time)",
        "classificacao calculada dos proprios jogos como tabela principal",
        "juncao com TheSportsDB so demonstrativa: 5 times e temporada 2024/25, "
        "diferente das odds (2021/22 e 2022/23)",
        "atributos pos-juncao: dif_posicao, dif_pontos, "
        "mandante_melhor_posicionado",
    ])


if __name__ == "__main__":
    config.configurar_log()
    main()
