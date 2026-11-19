-- Passa quando devolve ZERO linhas.
-- Todo jogo precisa ter, na fato_classificacao, a linha do mandante naquela
-- temporada. É um relationships com chave composta (time e temporada), que
-- o teste pronto não cobre.
select f.jogo_id, f.time_casa_id, f.temporada
from {{ ref('fato_jogo') }} f
left join {{ ref('fato_classificacao') }} c
       on c.time_id = f.time_casa_id and c.temporada = f.temporada
where c.time_id is null
