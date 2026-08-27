## Fontes de dados

| Fonte | Formato | Acesso | Extraído | Link |
|---|---|---|---|---|
| Odds de futebol (football-data.co.uk, via Kaggle) | CSV | token | 20/08/2026 | kaggle.com/datasets/ahmadasadi00/football-betting-odds |
| Classificação Premier League (TheSportsDB) | JSON | aberto | 20/08/2026 | thesportsdb.com/api.php |

## Defeitos conhecidos das fontes

### Odds de futebol (Kaggle)
- Colunas de odds de diferentes casas de apostas (B365, BW, IW, VC, WH) sao 
  fortemente correlacionadas entre si -- todas precificam o mesmo jogo. 
  Nao ha necessidade de manter todas na analise.
- FTAG/FTHG (gols no fim) correlacionados com HTAG/HTHG (gols no intervalo) 
  -- redundancia esperada, nao e erro.
- 'Unnamed: 0' e uma coluna de indice residual da exportacao (unica e 
  uniforme, sem informacao util); correlacionada com 'Div' (divisao). 
  Candidata a remocao na camada prata.
- HTHG, HTAG, FTHG e FTAG tem muitos zeros (23% a 61%) -- comportamento 
  esperado do futebol (times fazem 0 gol com frequencia, especialmente no 
  intervalo), nao e defeito da fonte.
- 'Unique_ID' tem valores unicos -- esperado, e provavelmente o identificador 
  de cada partida.

### Classificacao (TheSportsDB)
- Tabela limitada a 5 times (chave gratuita da API) -- ver limitacao ja 
  registrada na secao de fontes.
- strGroup vem 100% vazia -- conceito nao se aplica a competicoes de pontos 
  corridos como a Premier League.
- idLeague, strLeague, strSeason, strDescription, intPlayed e dateUpdated 
  sao constantes -- esperado, pois a consulta ja filtra por uma unica liga 
  e temporada.
- Varios alertas de "correlacao alta" e "valores unicos" sao efeito do 
  tamanho pequeno da amostra (5 times), nao defeitos reais da fonte.
