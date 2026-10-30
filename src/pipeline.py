"""
Ponto de entrada do pipeline.

ISTO NAO E ORQUESTRACAO
=======================
Um orquestrador de verdade (Airflow, Prefect, Dagster) agenda sozinho,
entende dependencias em grafo, tenta de novo, avisa alguem e reprocessa
periodos passados. Este arquivo nao faz nada disso: roda as etapas na
ordem certa, registra o que aconteceu e para quando alguma quebra.

COMO EXECUTAR, a partir de qualquer pasta
=========================================
    python src/pipeline.py                  roda tudo
    python src/pipeline.py transformacao    retoma a partir de uma etapa

A retomada existe porque a ingestao bate nas fontes de novo e demora.
Quando o erro esta numa etapa do meio, nao se refaz a primeira.

ETAPAS
======
    ingestao        baixa as fontes para a bronze (precisa de internet e
                    do kaggle.json)
    transformacao   bronze -> prata, uma fonte por vez, e depois a
                    classificacao calculada dos proprios jogos
    enriquecimento  junta as tabelas da prata
    carga           ainda nao implementada
    modelagem       ainda nao implementada
"""

import logging
import sys
import time

import config

log = logging.getLogger(__name__)


def etapa_ingestao():
    # Os scripts de ingestao ficam em dados/bronze/, junto da camada que
    # alimentam. Importar so aqui evita exigir kagglehub nas outras etapas.
    sys.path.insert(0, str(config.BRONZE))
    import ingerir
    import ingerir_classificacao

    ingerir.main()
    ingerir_classificacao.main()


def etapa_transformacao():
    import calcular_classificacao
    import transformar_classificacao
    import transformar_futebol

    transformar_futebol.main()
    transformar_classificacao.main()
    # Depende da prata de odds, por isso vem depois de transformar_futebol.
    calcular_classificacao.main()


def etapa_enriquecimento():
    import enriquecer

    enriquecer.main()


ETAPAS = [
    ("ingestao", etapa_ingestao),
    ("transformacao", etapa_transformacao),
    ("enriquecimento", etapa_enriquecimento),
    ("carga", None),        # proximas aulas
    ("modelagem", None),    # proximas aulas
]


def executar(nome, funcao):
    log.info("etapa %s: inicio", nome)
    comeco = time.perf_counter()
    try:
        funcao()
    except Exception:
        # log.exception grava a mensagem e o rastro inteiro do erro;
        # raise devolve o erro para cima, para o pipeline nao seguir
        # para a proxima etapa com dado pela metade.
        log.exception("etapa %s falhou", nome)
        raise
    log.info("etapa %s: fim em %.0fs", nome, time.perf_counter() - comeco)


def main(a_partir_de=None):
    config.configurar_log()
    config.criar_pastas()

    nomes = [nome for nome, _ in ETAPAS]
    if a_partir_de and a_partir_de not in nomes:
        log.error("etapa desconhecida: %s", a_partir_de)
        log.error("etapas validas: %s", ", ".join(nomes))
        return 1

    comecou = a_partir_de is None
    for nome, funcao in ETAPAS:
        if nome == a_partir_de:
            comecou = True
        if not comecou:
            log.info("etapa %s: pulada", nome)
            continue
        if funcao is None:
            log.warning("etapa %s: ainda nao implementada", nome)
            continue
        executar(nome, funcao)

    log.info("pipeline concluido")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))
