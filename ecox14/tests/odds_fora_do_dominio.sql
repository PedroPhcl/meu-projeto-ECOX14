-- Passa quando devolve ZERO linhas.
-- Odd decimal nunca é menor que 1,0 (pagaria menos do que a aposta). Seria
-- erro de coleta, e a probabilidade implícita (1/odd) passaria de 100%.
select jogo_id, odd_casa, odd_empate, odd_visitante
from {{ ref('fato_jogo') }}
where odd_casa < 1 or odd_empate < 1 or odd_visitante < 1
