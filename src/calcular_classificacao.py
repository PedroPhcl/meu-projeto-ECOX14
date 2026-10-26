"""Monta a classificacao final de cada temporada a partir dos proprios jogos.

Resolve o limite da fonte TheSportsDB (so 5 times, so 2024/25): a tabela
sai dos 760 jogos da prata de odds, para os 20 times de 2021/22 e 2022/23.
Grao do resultado: 1 linha por time e temporada.
"""

import json
from datetime import datetime
from pathlib import Path

import pandas as pd

import limpeza

PRATA = Path("dados/prata")
ENTRADA = PRATA / "odds_futebol.parquet"


def carregar():
    df = pd.read_parquet(ENTRADA)
    print("lido:", ENTRADA.name, df.shape)
    return df


def uma_linha_por_time(df):
    """Cada jogo vira duas linhas: uma para o mandante, outra para o visitante."""
    casa = pd.DataFrame({
        "Temporada": df["Temporada"],
        "time": df["HomeTeam"],
        "gols_pro": df["FTHG"],
        "gols_contra": df["FTAG"],
        "vitoria": df["FTR"] == "H",
        "empate": df["FTR"] == "D",
        "derrota": df["FTR"] == "A",
    })
    fora = pd.DataFrame({
        "Temporada": df["Temporada"],
        "time": df["AwayTeam"],
        "gols_pro": df["FTAG"],
        "gols_contra": df["FTHG"],
        "vitoria": df["FTR"] == "A",
        "empate": df["FTR"] == "D",
        "derrota": df["FTR"] == "H",
    })
    return pd.concat([casa, fora], ignore_index=True)


def somar_por_time(linhas):
    tabela = linhas.groupby(["Temporada", "time"], as_index=False).agg(
        jogos=("vitoria", "size"),
        vitorias=("vitoria", "sum"),
        empates=("empate", "sum"),
        derrotas=("derrota", "sum"),
        gols_pro=("gols_pro", "sum"),
        gols_contra=("gols_contra", "sum"),
    )
    tabela["saldo_gols"] = tabela["gols_pro"] - tabela["gols_contra"]
    tabela["pontos"] = 3 * tabela["vitorias"] + tabela["empates"]
    return tabela


def calcular_posicao(tabela):
    """Criterio da Premier League: pontos, saldo de gols, gols marcados."""
    tabela = tabela.sort_values(
        ["Temporada", "pontos", "saldo_gols", "gols_pro"],
        ascending=[True, False, False, False],
    )
    tabela["posicao"] = tabela.groupby("Temporada").cumcount() + 1
    return tabela.reset_index(drop=True)


def criar_chave(tabela):
    tabela["chave_time"] = limpeza.chave_texto(tabela["time"])
    return tabela


def conferir(tabela):
    print("linhas (time x temporada):", len(tabela))
    print("times por temporada:")
    print(tabela.groupby("Temporada")["time"].nunique().to_string())
    print("jogos por time (min/max):",
          tabela["jogos"].min(), "/", tabela["jogos"].max())
    for temp, grupo in tabela.groupby("Temporada"):
        lider = grupo.iloc[0]
        print(f"  {temp}: 1o {lider['time']} com {lider['pontos']} pts")
    repetidas = tabela.duplicated(["Temporada", "chave_time"]).sum()
    print("chaves (temporada, time) repetidas:", repetidas)
    return tabela


def salvar(tabela):
    PRATA.mkdir(parents=True, exist_ok=True)
    destino = PRATA / "classificacao_calculada.parquet"
    tabela.to_parquet(destino, index=False)
    print("salvo em:", destino, tabela.shape)
    return destino


def registrar(destino, antes, depois, decisoes):
    info = {
        "origem": ENTRADA.name,
        "arquivo_prata": destino.name,
        "linhas_antes": antes,
        "linhas_depois": depois,
        "decisoes": decisoes,
        "transformado_em": datetime.now().isoformat(timespec="seconds"),
    }
    with (PRATA / "proveniencia.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(info, ensure_ascii=False) + "\n")


def main():
    df = carregar()
    linhas = uma_linha_por_time(df)
    tabela = somar_por_time(linhas)
    tabela = calcular_posicao(tabela)
    tabela = criar_chave(tabela)
    tabela = conferir(tabela)
    destino = salvar(tabela)
    registrar(destino, len(df), len(tabela), [
        "classificacao final calculada a partir dos jogos da prata de odds "
        "(3 pontos por vitoria, 1 por empate)",
        "desempate: saldo de gols e depois gols marcados",
        "grao: 1 linha por time e temporada",
        "chave_time criada com chave_texto, igual a da fonte de classificacao",
    ])


if __name__ == "__main__":
    main()
