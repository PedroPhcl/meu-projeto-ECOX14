"""
Painel: so a tela. Nenhuma linha de SQL aqui; tudo vem de consultas.py.

Rodar, a partir da raiz do projeto:
    streamlit run dashboard/painel.py
"""

import altair as alt
import pandas as pd
import streamlit as st

import consultas

st.set_page_config(page_title="Calibração das odds", layout="wide")
st.title("As odds acertam? Calibração na Premier League")
st.write(
    "Dentro de cada faixa de favoritismo do mandante, a probabilidade que a "
    "odd sugere bate com a frequência com que o mandante realmente venceu?"
)

# ------------------------------------------------------------- filtros
st.sidebar.header("Filtros")

opcoes_temporada = ["Todas"] + consultas.temporadas()["temporada"].tolist()
escolha_temporada = st.sidebar.selectbox("Temporada", opcoes_temporada)
temporada = None if escolha_temporada == "Todas" else escolha_temporada

opcoes_forca = {
    "Todos os jogos": None,
    "Mandante melhor posicionado": True,
    "Visitante melhor posicionado": False,
}
escolha_forca = st.sidebar.selectbox("Força relativa", list(opcoes_forca))
mandante_melhor = opcoes_forca[escolha_forca]

st.sidebar.caption(
    "A posição vem da classificação final da temporada, calculada com os "
    "próprios jogos (inclui o jogo em questão). Serve para separar times por "
    "força, não é informação disponível antes da partida."
)

if mandante_melhor is not None:
    st.info(
        "Cuidado ao interpretar este filtro: a posição final já embute o "
        "resultado dos jogos (inclusive este). Times que terminam bem "
        "posicionados venceram mais, então a frequência real tende a aparecer "
        "acima da probabilidade implícita sem que isso diga algo sobre as odds."
    )

# -------------------------------------------------------------- dados
resumo = consultas.resumo_mandante(temporada, mandante_melhor).iloc[0]
faixas = consultas.calibracao(temporada, mandante_melhor)

if resumo["jogos"] == 0:
    st.warning("Nenhum jogo com esses filtros.")
    st.stop()

# ------------------------------------------------------------ números
c1, c2, c3 = st.columns(3)
c1.metric("Jogos", int(resumo["jogos"]))
c2.metric("Vitórias do mandante (real)", f"{resumo['freq_real']:.1%}")
c3.metric(
    "Probabilidade implícita média",
    f"{resumo['prob_normalizada']:.1%}",
    delta=f"real − implícita: {(resumo['freq_real'] - resumo['prob_normalizada']) * 100:+.1f} p.p.",
    delta_color="off",
)

# ------------------------------------------------------ gráfico e tabela
col1, col2 = st.columns([5, 4])

with col1:
    st.subheader("Probabilidade implícita × frequência real")
    # Linha tracejada = calibração perfeita (o que o mercado diz é o que acontece).
    perfeita = alt.Chart(pd.DataFrame({"x": [0, 1], "y": [0, 1]})).mark_line(
        strokeDash=[4, 4], color="gray"
    ).encode(x="x:Q", y="y:Q")
    eixo = alt.Scale(domain=[0, 1])
    observado = alt.Chart(faixas).encode(
        x=alt.X("prob_normalizada:Q", title="Probabilidade implícita média (normalizada)",
                scale=eixo, axis=alt.Axis(format="%")),
        y=alt.Y("freq_real:Q", title="Frequência real de vitória do mandante",
                scale=eixo, axis=alt.Axis(format="%")),
        tooltip=[
            alt.Tooltip("faixa:N", title="Faixa"),
            alt.Tooltip("jogos:Q", title="Jogos"),
            alt.Tooltip("prob_normalizada:Q", title="Implícita", format=".1%"),
            alt.Tooltip("freq_real:Q", title="Real", format=".1%"),
        ],
    )
    grafico = perfeita + observado.mark_line(color="#d9701e") + observado.mark_circle(
        color="#d9701e", size=120
    )
    st.altair_chart(grafico.properties(height=360), width="stretch")
    st.caption(
        "Pontos sobre a linha tracejada = odds bem calibradas. Acima dela, o "
        "mandante venceu mais do que a odd indicava; abaixo, menos."
    )

with col2:
    st.subheader("Por faixa de favoritismo")
    tabela = faixas.rename(columns={
        "faixa": "Faixa",
        "jogos": "Jogos",
        "prob_bruta": "Bruta",
        "prob_normalizada": "Normalizada",
        "freq_real": "Real",
    })
    for coluna in ("Bruta", "Normalizada", "Real"):
        tabela[coluna] = tabela[coluna] * 100
    st.dataframe(
        tabela,
        hide_index=True,
        width="stretch",
        column_config={c: st.column_config.NumberColumn(format="%.1f%%")
                       for c in ("Bruta", "Normalizada", "Real")},
    )
    st.caption(
        "Probabilidade implícita média por faixa. Bruta = 1/odd. Normalizada = "
        "bruta dividida pela soma das três probabilidades do jogo, o que "
        "retira a margem da casa de apostas. Real = frequência de vitória do mandante. "
        "Faixas com poucos jogos oscilam muito: veja a coluna Jogos."
    )

# ------------------------------------------------------------- origem
origem = consultas.fonte()
if origem:
    texto_fonte = (
        f"Fonte: odds da Bet365 no dataset Kaggle {origem['fonte']}, extraído em "
        f"{origem['extraido_em'][:10]}."
    )
else:
    texto_fonte = "Fonte: odds da Bet365 (dataset do Kaggle)."
st.caption(
    f"{texto_fonte} Premier League, {len(consultas.temporadas())} temporadas. "
    f"Classificação calculada a partir dos próprios jogos. "
    f"{int(resumo['jogos'])} jogos nesta seleção."
)
