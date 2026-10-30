"""
Configuracao central do projeto.

O QUE ENTRA AQUI
================
    caminhos de pasta e arquivo
    parametros que voce ajusta e reexecuta (temporadas, liga, fonte)
    a configuracao do log

O QUE NAO ENTRA
===============
    logica de transformacao
    qualquer coisa que mude a cada execucao
    segredo: senha, token, chave de API (o kaggle.json fica fora do Git)

O TESTE
=======
Se alguem for rodar o projeto em outra maquina, ou com outra temporada
ou outra liga, quais linhas essa pessoa precisa editar? Essas linhas
pertencem a este arquivo.
"""

import logging
from pathlib import Path


# Calculada a partir deste arquivo: o caminho nao depende de onde
# o comando foi digitado.
RAIZ = Path(__file__).resolve().parent.parent

DADOS = RAIZ / "dados"
BRONZE = DADOS / "bronze"
PRATA = DADOS / "prata"
OURO = DADOS / "ouro"
RELATORIOS = RAIZ / "relatorios"

# Bronze tem um nivel por fonte.
BRONZE_ODDS = BRONZE / "futebol"
BRONZE_CLASSIFICACAO = BRONZE / "classificacao"

# Padroes de nome dos arquivos datados da bronze.
PADRAO_ODDS = "odds_*.csv"
PADRAO_CLASSIFICACAO = "classificacao_*.csv"

# Arquivos da prata.
PRATA_ODDS = PRATA / "odds_futebol.parquet"
PRATA_CLASSIFICACAO = PRATA / "classificacao.parquet"
PRATA_CLASSIFICACAO_CALCULADA = PRATA / "classificacao_calculada.parquet"
PRATA_ENRIQUECIDO = PRATA / "odds_enriquecido.parquet"
PRATA_PROVENIENCIA = PRATA / "proveniencia.jsonl"

# ---------------------------------------------------------- parametros
# Fonte primaria (odds)
DATASET_KAGGLE = "ahmadasadi00/football-betting-odds"
DIVISAO = "E0"            # E0 = Premier League na fonte de odds
N_TEMPORADAS = 2          # quantas temporadas mais recentes manter
Z_LIMITE = 3              # limite do z-score para marcar extremos

# Fonte secundaria (TheSportsDB)
URL_CLASSIFICACAO = "https://www.thesportsdb.com/api/v1/json/123/lookuptable.php"
ID_LIGA = "4328"          # Premier League na TheSportsDB
TEMPORADA_API = "2024-2025"

# ------------------------------------------------------------- logging
ARQUIVO_LOG = RAIZ / "pipeline.log"


def configurar_log(nivel=logging.INFO):
    """Manda cada mensagem para a tela e para o arquivo pipeline.log."""
    logging.basicConfig(
        level=nivel,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        handlers=[
            logging.FileHandler(ARQUIVO_LOG, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


def criar_pastas():
    for pasta in (BRONZE_ODDS, BRONZE_CLASSIFICACAO, PRATA, OURO, RELATORIOS):
        pasta.mkdir(parents=True, exist_ok=True)
