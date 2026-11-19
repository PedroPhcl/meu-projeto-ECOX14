-- Passa quando devolve ZERO linhas.
-- Grão da fato_classificacao: um time em uma temporada. A chave é composta,
-- por isso não existe teste pronto: é o par (time_id, temporada) que não
-- pode se repetir.
select time_id, temporada, count(*) as linhas
from {{ ref('fato_classificacao') }}
group by time_id, temporada
having count(*) > 1
