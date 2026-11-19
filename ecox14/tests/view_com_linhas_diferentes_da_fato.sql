-- Passa quando devolve ZERO linhas.
-- A view não pode multiplicar nem perder jogos: precisa ter exatamente as
-- linhas da fato_jogo. Se um join da view duplicasse algo, a conta mudaria.
select
    (select count(*) from {{ ref('vw_jogo_completo') }}) as linhas_view,
    (select count(*) from {{ ref('fato_jogo') }})        as linhas_fato
where (select count(*) from {{ ref('vw_jogo_completo') }})
   <> (select count(*) from {{ ref('fato_jogo') }})
