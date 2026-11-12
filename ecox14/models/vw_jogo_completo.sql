{{ config(materialized='view') }}

-- A tabela achatada da aula de enriquecimento, como consulta salva: nao
-- guarda dado, o banco executa o join na hora. As dimensoes entram com
-- join; a classificacao entra com left join para que um jogo sem posicao
-- apareca com nulo em vez de sumir.
select
    f.*,
    c.nome                          as time_casa,
    v.nome                          as time_visitante,
    pc.posicao                      as posicao_casa,
    pv.posicao                      as posicao_visitante,
    pc.pontos                       as pontos_casa,
    pv.pontos                       as pontos_visitante,
    pv.posicao - pc.posicao         as dif_posicao,
    pc.pontos - pv.pontos           as dif_pontos,
    pv.posicao > pc.posicao         as mandante_melhor_posicionado
from {{ ref('fato_jogo') }} f
join {{ ref('dim_time') }} c on f.time_casa_id = c.time_id
join {{ ref('dim_time') }} v on f.time_visitante_id = v.time_id
left join {{ ref('fato_classificacao') }} pc
       on pc.time_id = f.time_casa_id and pc.temporada = f.temporada
left join {{ ref('fato_classificacao') }} pv
       on pv.time_id = f.time_visitante_id and pv.temporada = f.temporada
