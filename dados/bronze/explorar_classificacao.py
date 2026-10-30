import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
import config  # noqa: E402
import logging  # noqa: E402

import pandas as pd  # noqa: E402
from data_profiling import ProfileReport  # noqa: E402

BRONZE = config.BRONZE_CLASSIFICACAO
PADRAO = config.PADRAO_CLASSIFICACAO
RELATORIOS = config.RELATORIOS

log = logging.getLogger(__name__)


def mais_recente():
    arquivos = sorted(BRONZE.glob(PADRAO))
    if not arquivos:
        raise FileNotFoundError("bronze vazia")
    return arquivos[-1]


def gerar(caminho):
    df = pd.read_csv(caminho)
    perfil = ProfileReport(df, title=caminho.name)
    RELATORIOS.mkdir(parents=True, exist_ok=True)
    saida = RELATORIOS / f"{caminho.stem}.html"
    perfil.to_file(saida)
    return saida


def main():
    caminho = mais_recente()
    log.info("perfilando: %s", caminho.name)
    log.info("relatorio gerado: %s", gerar(caminho))


if __name__ == "__main__":
    config.configurar_log()
    main()