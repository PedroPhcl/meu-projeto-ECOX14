-- dim_time: uma linha e um time.
select
    chave        as time_id,
    min(nome)    as nome
from (
    select chave_casa as chave, "HomeTeam" as nome
    from {{ source('prata', 'odds_enriquecido') }}
    union all
    select chave_visitante, "AwayTeam"
    from {{ source('prata', 'odds_enriquecido') }}
)
group by chave
