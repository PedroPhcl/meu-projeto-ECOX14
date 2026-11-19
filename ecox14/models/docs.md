{# Descrições das colunas da fato_jogo. Ficam num lugar só e são usadas
   também pela view vw_jogo_completo, que herda essas colunas: ninguém
   escreve a mesma frase duas vezes. #}

{% docs col_jogo_id %}Identificador único da partida (`Unique_ID` da fonte de odds). Chave primária da `fato_jogo`.{% enddocs %}

{% docs col_data %}Data em que a partida foi disputada.{% enddocs %}

{% docs col_temporada %}Temporada no formato `2021/22`. A fonte não trazia essa coluna: ela é calculada a partir da data (agosto a dezembro = ano corrente; janeiro a julho = ano anterior).{% enddocs %}

{% docs col_time_casa_id %}Time mandante. Chave do time (nome sem acento, em minúsculas): aponta para `dim_time.time_id`.{% enddocs %}

{% docs col_time_visitante_id %}Time visitante. Chave do time (nome sem acento, em minúsculas): aponta para `dim_time.time_id`.{% enddocs %}

{% docs col_gols_casa %}Gols do mandante ao fim da partida (`FTHG` na fonte).{% enddocs %}

{% docs col_gols_visitante %}Gols do visitante ao fim da partida (`FTAG` na fonte).{% enddocs %}

{% docs col_resultado %}Resultado da partida do ponto de vista do mandante: `casa` (vitória do mandante), `empate` ou `visitante` (vitória do visitante). Vem de `FTR` (H, D, A).{% enddocs %}

{% docs col_odd_casa %}Odd decimal da Bet365 para vitória do mandante (`B365H`). Odd menor que 1,0 seria erro de domínio, e um teste confere isso.{% enddocs %}

{% docs col_odd_empate %}Odd decimal da Bet365 para empate (`B365D`).{% enddocs %}

{% docs col_odd_visitante %}Odd decimal da Bet365 para vitória do visitante (`B365A`).{% enddocs %}

{% docs col_prob_casa %}Probabilidade implícita **bruta** de vitória do mandante: 1 / `odd_casa`. Não está normalizada: as três probabilidades de uma partida somam em média 1,054, porque a odd embute a margem da casa de apostas. Para comparar com a frequência real, divida pela soma das três.{% enddocs %}

{% docs col_prob_empate %}Probabilidade implícita **bruta** de empate: 1 / `odd_empate`. Não normalizada (ver `prob_casa`).{% enddocs %}

{% docs col_prob_visitante %}Probabilidade implícita **bruta** de vitória do visitante: 1 / `odd_visitante`. Não normalizada (ver `prob_casa`).{% enddocs %}

{% docs col_prob_casa_faixa %}Faixa de favoritismo do mandante: quartil (4 faixas) da `prob_casa` bruta, escrito como intervalo, por exemplo `(0.303, 0.444]`. É o agrupamento usado para comparar probabilidade implícita e frequência real de vitórias.{% enddocs %}

{% docs col_odd_casa_extremo %}Verdadeiro quando a `odd_casa` foi marcada como valor extremo pelo critério do IQR. O jogo é real (time muito favorito em casa); a marca só avisa, nenhuma linha foi removida.{% enddocs %}

{% docs col_odd_visitante_extremo %}Verdadeiro quando a `odd_visitante` foi marcada como valor extremo pelo critério do IQR. O jogo é real; a marca só avisa, nenhuma linha foi removida.{% enddocs %}
