import requests
import pandas as pd
from pathlib import Path
from datetime import date, datetime
import json

URL = "https://www.thesportsdb.com/api/v1/json/123/lookuptable.php"
BRONZE = Path("dados/bronze/classificacao")


def buscar():
    r = requests.get(URL, params={
        "l": "4328",           # id da Premier League na TheSportsDB
        "s": "2024-2025"       # temporada
    }, timeout=30)
    r.raise_for_status()
    return r.json()


def conferir(dados):
    tabela = dados.get("table")
    if not tabela:
        raise ValueError("resposta veio sem 'table' -- confira parametros l/s")
    print("times na tabela:", len(tabela))
    print("exemplo:", tabela[0]["strTeam"], "-> posicao", tabela[0]["intRank"])
    return tabela


def salvar(tabela):
    BRONZE.mkdir(parents=True, exist_ok=True)
    df = pd.json_normalize(tabela)
    hoje = date.today().strftime("%Y%m%d")
    destino = BRONZE / f"classificacao_{hoje}.csv"
    df.to_csv(destino, index=False)
    return destino


def registrar(destino, tabela):
    info = {
        "fonte": URL,
        "arquivo_bronze": destino.name,
        "registros": len(tabela),
        "extraido_em": datetime.now().isoformat(),
    }
    (BRONZE / "proveniencia.json").write_text(
        json.dumps(info, indent=2))


def main():
    dados = buscar()
    tabela = conferir(dados)
    destino = salvar(tabela)
    registrar(destino, tabela)


if __name__ == "__main__":
    main()