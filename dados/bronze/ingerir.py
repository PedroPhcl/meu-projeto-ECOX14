from pathlib import Path
import kagglehub

DATASET = "ahmadasadi00/football-betting-odds"
BRONZE = Path("dados/bronze/futebol")

def baixar():
    pasta = kagglehub.dataset_download(DATASET)
    print("baixado em:", pasta)
    return Path(pasta)

def localizar(pasta):
    arquivos = list(pasta.glob("*.csv"))
    if not arquivos:
        raise FileNotFoundError("nenhum CSV")
    print("encontrados:", [a.name for a in arquivos])
    return arquivos[0]

from datetime import date
import shutil
def copiar(origem):
    BRONZE.mkdir(parents=True, exist_ok=True)
    hoje = date.today().strftime("%Y%m%d")
    destino = BRONZE / f"odds_{hoje}.csv"
    shutil.copy(origem, destino)
    return destino

import json
from datetime import datetime

def registrar(origem, destino):
    info = {
        "fonte": DATASET,
        "arquivo_origem": origem.name,
        "arquivo_bronze": destino.name,
        "extraido_em": datetime.now().isoformat(),
    }
    (BRONZE / "proveniencia.json").write_text(
        json.dumps(info, indent=2))

def main():
    pasta = baixar()
    origem = localizar(pasta)
    destino = copiar(origem)
    registrar(origem, destino)

if __name__ == "__main__":
    main()