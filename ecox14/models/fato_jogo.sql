-- fato_jogo: uma linha e uma partida.
-- O where e o filtro de integridade da fato: a validacao da juncao da
-- aula de enriquecimento. Posicao nula = jogo cujo time nao achou par na
-- classificacao. Nesses dados nenhum e excluido.
select
    "Unique_ID"                 as jogo_id,
    cast("Date" as date)        as data,
    "Temporada"                 as temporada,
    chave_casa                  as time_casa_id,
    chave_visitante             as time_visitante_id,
    cast("FTHG" as integer)     as gols_casa,
    cast("FTAG" as integer)     as gols_visitante,
    case "FTR"
        when 'H' then 'casa'
        when 'D' then 'empate'
        when 'A' then 'visitante'
    end                         as resultado,
    "B365H"                     as odd_casa,
    "B365D"                     as odd_empate,
    "B365A"                     as odd_visitante,
    prob_casa,
    prob_empate,
    prob_visitante,
    prob_casa_faixa,
    "B365H_extremo"             as odd_casa_extremo,
    "B365A_extremo"             as odd_visitante_extremo
from {{ source('prata', 'odds_enriquecido') }}
where posicao_casa is not null
  and posicao_visitante is not null
