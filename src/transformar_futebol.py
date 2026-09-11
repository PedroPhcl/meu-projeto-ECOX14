import json
from datetime import datetime
from pathlib import Path

import pandas as pd

BRONZE = Path("dados/bronze/futebol")
PRATA = Path("dados/prata")
PADRAO = "odds_*.csv"

def carregar():
    arquivos = sorted(BRONZE.glob(PADRAO))
    if not arquivos:
        raise FileNotFoundError(f"nada em {BRONZE}")
    caminho = arquivos[-1]
    df = pd.read_csv(caminho)
    print("lido:", caminho.name, df.shape)
    print(df.columns.tolist())
    print(df.isna().sum())
    return df, caminho

def tirar_espacos(df):
    df.columns = df.columns.str.strip()
    for coluna in df.select_dtypes(include="object"):
        df[coluna] = df[coluna].str.strip()
    return df

def separar_premier_league(df):
    e_premier = df["Div"] == "E0"
    print("premier league:", e_premier.sum())
    print("outras ligas  :", (~e_premier).sum())
    return df[e_premier].copy()

def calcular_temporada(df):
    df["Date"] = pd.to_datetime(df["Date"], format="%Y-%m-%d")
    ano_temporada = df["Date"].dt.year.where(
        df["Date"].dt.month >= 7, df["Date"].dt.year - 1
    )
    df["Temporada"] = ano_temporada.astype(str) + "/" + (ano_temporada + 1).astype(str).str[-2:]
    return df

def separar_ultimas_temporadas(df, n=2):
    temporadas_recentes = sorted(df["Temporada"].unique())[-n:]
    print("temporadas mantidas:", temporadas_recentes)
    e_recente = df["Temporada"].isin(temporadas_recentes)
    print("jogos mantidos :", e_recente.sum())
    print("jogos descartados:", (~e_recente).sum())
    return df[e_recente].copy()

def conferir_chave(df, chave="Unique_ID"):
    repetidas = df[chave].duplicated().sum()
    print("chaves repetidas:", repetidas)
    if repetidas:
        print(df[df[chave].duplicated(keep=False)])
    return df.drop_duplicates(subset=chave)

def converter_tipos(df):
    colunas_odds = [
        "B365H", "B365D", "B365A",
        "BWH", "BWD", "BWA",
        "IWH", "IWD", "IWA",
        "WHH", "WHD", "WHA",
        "VCH", "VCD", "VCA",
    ]
    for coluna in colunas_odds:
        df[coluna] = pd.to_numeric(df[coluna], errors="coerce")
    return df

def limites_iqr(serie):
    q1 = serie.quantile(0.25)
    q3 = serie.quantile(0.75)
    iqr = q3 - q1
    return q1 - 1.5 * iqr, q3 + 1.5 * iqr


def marcar_extremos(df, coluna):
    baixo, alto = limites_iqr(df[coluna])
    df[coluna + "_extremo"] = (
        (df[coluna] < baixo) | (df[coluna] > alto))
    print(coluna, df[coluna + "_extremo"].sum())
    return df


def marcar_zscore(df, coluna, limite=3):
    z = (df[coluna] - df[coluna].mean()) / df[coluna].std()
    df[coluna + "_z"] = z.abs() > limite
    print(coluna, "z acima de", limite, ":",
          df[coluna + "_z"].sum())
    return df

def salvar(df):
    PRATA.mkdir(parents=True, exist_ok=True)
    destino = PRATA / "odds_futebol.parquet"
    df.to_parquet(destino, index=False)
    print("salvo em:", destino, df.shape)
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
    caminho = PRATA / "proveniencia.jsonl"
    with caminho.open("a", encoding="utf-8") as f:
        f.write(json.dumps(info, ensure_ascii=False) + "\n")


def main():
    df, origem = carregar()
    antes = len(df)
    df = separar_premier_league(df)
    df = calcular_temporada(df)
    df = separar_ultimas_temporadas(df)
    df = conferir_chave(df)
    df = converter_tipos(df)
    df = marcar_extremos(df, "B365A")
    df = marcar_zscore(df, "B365A")
    df = marcar_extremos(df, "B365H")
    df = marcar_zscore(df, "B365H")
    destino = salvar(df)
    registrar(origem, destino, antes, len(df), [
        "filtrado para Premier League (Div=E0)",
        "filtrado para as 2 temporadas mais recentes (2021/22, 2022/23)",
        "odds convertidas para numerico",
        "extremos marcados por IQR e z-score, mas mantidos (sao jogos reais, nao erros)",
    ])


if __name__ == "__main__":
    main()
