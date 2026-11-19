-- Passa quando devolve ZERO linhas.
-- Mesma regra do mandante, para o visitante.
select f.jogo_id, f.time_visitante_id, f.temporada
from {{ ref('fato_jogo') }} f
left join {{ ref('fato_classificacao') }} c
       on c.time_id = f.time_visitante_id and c.temporada = f.temporada
where c.time_id is null
