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
  Candidata a remoção: ainda presente na prata.
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

## Atributos derivados

### prob_casa, prob_empate, prob_visitante
Probabilidade implícita do mercado (1/odd) para cada resultado, calculada a
partir da odd média da Bet365 (B365H/D/A). É a base direta da pergunta
norteadora do projeto: comparar essa probabilidade com a frequência real
de resultados observados.

### prob_casa_faixa
Quartil da probabilidade implícita de vitória do mandante (qcut, 4 faixas).
Serve para agrupar jogos por faixa de favoritismo e comparar, dentro de
cada faixa, se a probabilidade média do mercado bate com a frequência real
de vitórias -- é o método de calibração central do projeto.

### chave_time (fonte de classificação)
Nome do time normalizado (sem acento, minúsculo, sinônimos mapeados) para
permitir cruzar a fonte de classificação com a fonte de odds. Mapa de
sinônimos ainda parcial (cobre só os 5 times vistos até agora, pela
limitação da chave gratuita da TheSportsDB).

## Módulo de limpeza
As funções `tirar_espacos`, `chave_texto` e `aplicar_mapa` foram movidas
para `src/limpeza.py`, por não mencionarem nenhuma fonte específica e
servirem a qualquer uma. Os dicionários de sinônimos (ex: MAPA_TIMES)
continuam nos scripts de cada fonte, pois são específicos dela.

## Correção
A função `tirar_espacos` foi criada na aula de limpeza mas nunca tinha 
sido chamada na main, foi corrigido nesta aula.

## Enriquecimento (junção de fontes)

Duas tabelas foram juntadas à prata de odds (grão: 1 linha por jogo, 760 linhas).
Nenhum dado novo é criado: a informação já existia em outra tabela.

### Classificação calculada dos próprios jogos (junção principal)
A fonte TheSportsDB só entrega 5 times e só a temporada 2024/25, que não existe
nas odds (2021/22 e 2022/23). Por isso `src/calcular_classificacao.py` monta a
classificação final de cada temporada a partir dos 760 jogos (3 pontos por
vitória, 1 por empate; desempate por saldo de gols e depois gols marcados).
Resultado: 40 linhas (20 times x 2 temporadas). Conferência com o mundo real:
Man City 93 pts e Liverpool 92 em 2021/22; Man City 89 pts e Arsenal 84 em 2022/23.

- Tabelas: odds (1 linha por jogo) x classificação calculada (1 linha por time e temporada).
- Chave: (Temporada, chave_time), uma vez para o mandante e outra para o visitante.
- Tipo: `how="left"` com `validate="many_to_one"`.
- Contagem: esquerda 760, resultado 760, sem par 0 (nos dois lados).
- Limite: as duas tabelas vêm da mesma fonte de odds, então o casamento total já era esperado.
  A posição é a final da temporada e inclui o próprio jogo; serve para agrupar favoritismo,
  não como informação disponível antes da partida.

### Classificação do TheSportsDB (junção demonstrativa)
- Chave: `chave_time` do mandante. `how="left"`, `validate="many_to_one"`.
- Contagem: esquerda 760, resultado 760, sem par 570. Casaram 190 jogos (5 times x 19 jogos em casa x 2 temporadas).
- As colunas `tsdb_pos_2425_casa` e `tsdb_pontos_2425_casa` trazem a posição de 2024/25,
  então não descrevem a temporada do jogo. Ficam na tabela só como demonstração e **não entram na análise**.

### Quem não casou
- **Calculada:** ninguém. As chaves vieram da mesma fonte (40 de 40).
- **TheSportsDB, 18 times do mandante, 570 jogos:** Aston Villa, Bournemouth, Brentford,
  Brighton, Burnley, Crystal Palace, Everton, Fulham, Leeds, Leicester, Man United,
  Norwich, Nott'm Forest, Southampton, Tottenham, Watford, West Ham e Wolves.
  Motivo: universo diferente. A chave gratuita da API devolve só os 5 primeiros colocados de 2024/25.
  Não é erro de grafia e não se resolve com mapa de sinônimos; está documentado como limitação.

### Atributos que só existem depois da junção
- `posicao_casa`, `posicao_visitante`, `pontos_casa`, `pontos_visitante`, `saldo_gols_casa`, `saldo_gols_visitante`.
- `dif_posicao` = posição do visitante menos a do mandante (positivo: mandante melhor posicionado).
- `dif_pontos` e `mandante_melhor_posicionado`.
- Ligação com a pergunta norteadora: permite checar se a probabilidade implícita do mandante
  se mantém calibrada dentro de cada faixa de força relativa dos times, e não só por quartil de odd.

Os scripts rodam nesta ordem: `transformar_futebol.py`, `transformar_classificacao.py`,
`calcular_classificacao.py`, `enriquecer.py`. O resultado é `dados/prata/odds_enriquecido.parquet`
(760 linhas, 49 colunas).

