import json
import logging
from datetime import datetime

import pandas as pd

import config
import limpeza

BRONZE = config.BRONZE_CLASSIFICACAO
PRATA = config.PRATA
PADRAO = config.PADRAO_CLASSIFICACAO

log = logging.getLogger(__name__)

# mapa de sinonimos especifico desta fonte -- fica aqui, nao no modulo
MAPA_TIMES = {
    "manchester city": "man city",
    "newcastle united": "newcastle",
}


def carregar():
    arquivos = sorted(BRONZE.glob(PADRAO))
    if not arquivos:
        raise FileNotFoundError(f"nada em {BRONZE}")
    caminho = arquivos[-1]
    df = pd.read_csv(caminho)
    log.info("lido: %s %s", caminho.name, df.shape)
    return df, caminho


def remover_colunas_vazias(df):
    colunas = ["idLeague", "strLeague", "strSeason", "strDescription",
               "intPlayed", "dateUpdated", "strGroup", "strBadge", "strForm"]
    existentes = [c for c in colunas if c in df.columns]
    log.debug("colunas removidas: %s", existentes)
    return df.drop(columns=existentes)


def padronizar_times(df):
    df["chave_time"] = limpeza.chave_texto(df["strTeam"])
    df["chave_time"] = limpeza.aplicar_mapa(df["chave_time"], MAPA_TIMES)
    return df


def converter_tipos(df):
    colunas = ["intRank", "intWin", "intDraw", "intLoss",
               "intGoalsFor", "intGoalsAgainst",
               "intGoalDifference", "intPoints"]
    for c in colunas:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def salvar(df):
    PRATA.mkdir(parents=True, exist_ok=True)
    destino = config.PRATA_CLASSIFICACAO
    df.to_parquet(destino, index=False)
    log.info("salvo em: %s %s", destino, df.shape)
    return destino


def registrar(origem, destino, antes, depois, decisoes):
    info = {
        "origem": origem.name,
        "arquivo_prata": destino.name,
        "linhas_antes": antes,
        "linhas_depois": depois,
        "decisoes": decisoes,
        "transformado_em": datetime.now().isoformat(timespec="seconds"),
    }
    caminho = config.PRATA_PROVENIENCIA
    with caminho.open("a", encoding="utf-8") as f:
        f.write(json.dumps(info, ensure_ascii=False) + "\n")


def main():
    df, origem = carregar()
    antes = len(df)
    df = limpeza.tirar_espacos(df)
    df = remover_colunas_vazias(df)
    df = padronizar_times(df)
    df = converter_tipos(df)
    destino = salvar(df)
    registrar(origem, destino, antes, len(df), [
        "espacos removidos",
        "colunas vazias/constantes removidas (idLeague, strLeague, strSeason, "
        "strDescription, intPlayed, dateUpdated, strGroup, strBadge, strForm)",
        "chave_time criada (chave_texto + mapa de sinonimos parcial, cobre so "
        "os 5 times vistos -- limite da API gratuita) para cruzar com odds",
        "colunas numericas convertidas",
    ])


if __name__ == "__main__":
    config.configurar_log()
    main()