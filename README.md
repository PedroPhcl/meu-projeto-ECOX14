# Projeto ECOX14 — Calibração de Odds em Apostas Esportivas de Futebol

## Tema
Calibração de odds pré-jogo no mercado de apostas esportivas de futebol (Premier League)

## Pergunta norteadora
As odds pré-jogo (probabilidades implícitas do mercado) são bem calibradas em relação
à frequência real de resultados observados, ou existe viés sistemático (ex: favoritismo
ao mandante)?

## Fontes de dados

| Fonte | Formato | Acesso | Extraído | Link |
|---|---|---|---|---|
| Odds de futebol (football-data.co.uk, via Kaggle) | CSV | token | 20/08/2026 | kaggle.com/datasets/ahmadasadi00/football-betting-odds |
| Classificação Premier League (TheSportsDB) | JSON | aberto | 20/08/2026 | thesportsdb.com/api.php |

## Defeitos conhecidos das fontes

### Odds de futebol (Kaggle)
- Colunas de odds de diferentes casas de apostas (B365, BW, IW, VC, WH) são
  fortemente correlacionadas entre si -- todas precificam o mesmo jogo.
  Não há necessidade de manter todas na análise.
- FTAG/FTHG (gols no fim) correlacionados com HTAG/HTHG (gols no intervalo)
  -- redundância esperada, não é erro.
- 'Unnamed: 0' é uma coluna de índice residual da exportação (única e
  uniforme, sem informação útil); correlacionada com 'Div' (divisão).
  Removida na camada prata.
- HTHG, HTAG, FTHG e FTAG têm muitos zeros (23% a 61%) -- comportamento
  esperado do futebol (times fazem 0 gol com frequência, especialmente no
  intervalo), não é defeito da fonte.
- 'Unique_ID' tem valores únicos -- esperado, é o identificador de cada partida.
- O arquivo baixado (all_avail_games.csv) traz 18 ligas europeias e ~18
  temporadas misturadas (119.790 linhas), não só Premier League.
- Formato de data é AAAA-MM-DD, diferente do DD/MM/AAAA usado no site
  original football-data.co.uk.

### Classificação (TheSportsDB)
- Tabela limitada a 5 times por consulta (chave gratuita da API); tabela
  completa dos 20 times exigiria assinatura paga.
- strGroup vem 100% vazia -- conceito não se aplica a competições de pontos
  corridos como a Premier League.
- idLeague, strLeague, strSeason, strDescription, intPlayed e dateUpdated
  são constantes -- esperado, pois a consulta já filtra por uma única liga
  e temporada.
- Vários alertas de "correlação alta" e "valores únicos" são efeito do
  tamanho pequeno da amostra (5 times), não defeitos reais da fonte.

## Decisões de tratamento

### Odds de futebol (Kaggle)
- Filtrado para Premier League (Div = E0): 6.730 de 119.790 linhas.
- Temporada calculada a partir da Data (ago-dez = ano corrente, jan-jul =
  ano anterior), já que a fonte não trazia essa coluna.
- Filtrado para as 2 temporadas mais recentes disponíveis no arquivo
  (2021/22 e 2022/23): 760 jogos. Nota: o dataset do Kaggle vai só até
  05/2023, mais antigo que os CSVs baixados manualmente do
  football-data.co.uk (que chegavam a 2024/25).
- Chave (Unique_ID) conferida: 0 duplicatas.
- Odds convertidas para numérico (nenhum valor inválido encontrado).
- Extremos marcados por IQR (69 na odd de visitante, 67 na de mandante) e
  z-score (22 e 21) -- divergência esperada pela distribuição assimétrica
  das odds. Inspecionados manualmente: são jogos reais entre times de
  força desigual (ex: Man City/Liverpool em casa contra times rebaixados),
  não erros de coleta. Mantidos no dataset, apenas marcados.
- Nenhuma odd abaixo de 1.0 encontrada (seria erro de domínio).
- Salvo em dados/prata/odds_futebol.parquet (760 linhas, 32 colunas).