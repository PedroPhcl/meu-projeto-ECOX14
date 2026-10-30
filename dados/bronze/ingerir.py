import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
import config  # noqa: E402
import logging  # noqa: E402

import kagglehub  # noqa: E402

DATASET = config.DATASET_KAGGLE
BRONZE = config.BRONZE_ODDS

log = logging.getLogger(__name__)

def baixar():
    pasta = kagglehub.dataset_download(DATASET)
    log.info("baixado em: %s", pasta)
    return Path(pasta)

def localizar(pasta):
    arquivos = list(pasta.glob("*.csv"))
    if not arquivos:
        raise FileNotFoundError("nenhum CSV")
    log.info("encontrados: %s", [a.name for a in arquivos])
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
    config.configurar_log()
    main()