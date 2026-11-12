-- fato_classificacao: uma linha e um time em uma temporada.
select
    chave_time                   as time_id,
    "Temporada"                  as temporada,
    cast(posicao as integer)     as posicao,
    cast(pontos as integer)      as pontos,
    cast(jogos as integer)       as jogos,
    cast(vitorias as integer)    as vitorias,
    cast(empates as integer)     as empates,
    cast(derrotas as integer)    as derrotas,
    cast(gols_pro as integer)    as gols_pro,
    cast(gols_contra as integer) as gols_contra,
    cast(saldo_gols as integer)  as saldo_gols
from {{ source('prata', 'classificacao_calculada') }}
