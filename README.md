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

O resultado do enriquecimento é `dados/prata/odds_enriquecido.parquet` (760 linhas, 49 colunas).

## Como executar

A partir de qualquer pasta, com o ambiente virtual ativo e o `kaggle.json` configurado:

```
python src/pipeline.py                  # roda tudo
python src/pipeline.py transformacao    # retoma a partir de uma etapa
```

| Etapa | O que faz | Scripts |
|---|---|---|
| `ingestao` | baixa as duas fontes para a bronze | `dados/bronze/ingerir.py`, `dados/bronze/ingerir_classificacao.py` |
| `transformacao` | bronze → prata e classificação calculada | `transformar_futebol.py`, `transformar_classificacao.py`, `calcular_classificacao.py` |
| `enriquecimento` | junta as tabelas da prata | `enriquecer.py` |
| `carga` | carrega a prata no DuckDB (ler arquivo não é transformação) | `carga.py` |
| `modelagem` | `dbt run` constrói a ouro e `dbt test` confere as regras; se um teste falhar, o pipeline para | `ecox14/` (projeto dbt) |

Etapas sem função (hoje nenhuma) apareceriam no log como aviso, em vez de ficarem escondidas.
A retomada existe porque a ingestão bate nas fontes de novo e demora: se o erro está no
enriquecimento, não há motivo para baixar tudo outra vez. Cada script também roda sozinho
(`python src/enriquecer.py`), e a ordem entre eles está na tabela acima.

Os scripts de ingestão continuam em `dados/bronze/`, junto da camada que alimentam
(decisão tomada na Aula 3). O `pipeline.py` adiciona essa pasta ao caminho de importação
só ao rodar a ingestão.

## Configuração (`src/config.py`)

Caminhos de pasta, padrões de nome dos arquivos datados e parâmetros ficam em um lugar só.
O teste usado para decidir o que entra ali: se outra pessoa fosse rodar o projeto em outra
máquina ou com outra temporada, quais linhas ela precisaria editar?

- **Caminhos:** `RAIZ` é calculada a partir do próprio arquivo, então rodar de dentro de
  `src/` ou de qualquer outra pasta não quebra o caminho dos dados.
- **Parâmetros:** `DIVISAO` (E0 = Premier League), `N_TEMPORADAS` (2), `Z_LIMITE` (3),
  `ID_LIGA` e `TEMPORADA_API` da TheSportsDB, `DATASET_KAGGLE`.
- **Fora do config:** lógica de transformação e segredos. O token do Kaggle fica no
  `kaggle.json`, que está no `.gitignore`.

## Log (`pipeline.log`)

Os `print` foram trocados por `logging`. Cada mensagem sai na tela e no arquivo
`pipeline.log` (ignorado pelo Git), com hora, nível e módulo.

| Nível | Uso neste projeto |
|---|---|
| DEBUG | detalhe para investigar: colunas lidas, nulos por coluna, lista de times |
| INFO | o que se vai querer saber depois: linhas lidas, mantidas, descartadas, arquivo salvo |
| WARNING | estranho, mas seguiu: linhas sem par numa junção, odds que viraram NaN, chave repetida |
| ERROR | não deu para continuar |

Exemplo real: na junção com o TheSportsDB o log registra `WARNING [tsdb/casa] 570 linhas sem par`
e o pipeline segue, porque essa limitação já está documentada. Já uma junção que mudasse o
número de linhas (o grão) levanta erro e interrompe a etapa. Quando uma etapa falha, o
pipeline grava o rastro completo do erro no log, devolve o erro e não segue para a etapa
seguinte com dado pela metade.

## O que este pipeline não faz

O `pipeline.py` é um ponto de entrada, não um orquestrador. Não agenda a execução, não tenta
de novo sozinho, não avisa ninguém quando falha, não roda etapas em paralelo e não reprocessa
períodos passados. Para este projeto, rodar com as mãos está certo; um orquestrador só valeria
se alguma dessas necessidades aparecesse de verdade, e manter um (banco de metadados, agendador
e servidor web) é trabalho contínuo.

## Modelagem (camada Ouro)

Modelar não é sobre o dado que existe, é sobre as perguntas que vão ser feitas a ele. As
perguntas deste projeto:

1. Dentro de cada faixa de probabilidade implícita, a frequência real de vitória do mandante bate com ela?
2. Isso muda conforme a força relativa dos times (posição na tabela)?
3. Existe viés sistemático a favor do mandante?

A camada Ouro deixa de ser uma pasta e vira um esquema do banco `dados/ouro/projeto.duckdb`
(DuckDB: um banco embutido, o banco inteiro é um arquivo). O esquema `prata` recebe os parquets
como estão; o esquema `ouro` nasce dentro do banco, a partir da prata, e quem o constrói é o
dbt (seção abaixo).

### O grão de cada tabela

Escritas antes do `CREATE TABLE`, porque delas decorre o resto:

- **`fato_jogo`: uma linha é uma partida** (um mandante contra um visitante, em uma temporada).
- **`fato_classificacao`: uma linha é um time em uma temporada.**
- **`dim_time`: uma linha é um time.**

| Tabela | Natureza | Chave primária | O que pode ser somado | O que é duplicata |
|---|---|---|---|---|
| `ouro.fato_jogo` | fato (o que se mede) | `jogo_id` | gols entre jogos; odds e probabilidades só admitem média, nunca soma | o mesmo `jogo_id` duas vezes |
| `ouro.fato_classificacao` | fato | `(time_id, temporada)`, e não o time sozinho | pontos, gols e jogos entre times; a posição não se soma | o mesmo time na mesma temporada duas vezes |
| `ouro.dim_time` | dimensão (o que descreve) | `time_id` | nada | o mesmo time duas vezes |

Teste usado para separar: se a resposta é um número que se soma ou se tira média, é fato; se é
uma palavra pela qual se agrupa ou filtra, é dimensão.

### Como as tabelas se ligam

```
fato_jogo (uma partida, 760 linhas)
 |-- time_casa_id ............................> dim_time.time_id
 |-- time_visitante_id .......................> dim_time.time_id
 |-- (temporada, time_casa_id) ...............> fato_classificacao (temporada, time_id)
 `-- (temporada, time_visitante_id) ..........> fato_classificacao (temporada, time_id)

fato_classificacao (um time numa temporada, 40 linhas)
 `-- time_id .................................> dim_time.time_id

dim_time (um time, 23 linhas)
```

- `fato_jogo.time_casa_id` e `fato_jogo.time_visitante_id` apontam, os dois, para `dim_time.time_id`
  (a mesma dimensão desempenha dois papéis: mandante e visitante).
- `fato_jogo (temporada, time_casa_id)` e `(temporada, time_visitante_id)` apontam para
  `fato_classificacao (temporada, time_id)`.
- Não é uma estrela pura: a ligação entre as duas fatos existe para a posição do time não ser
  copiada dentro de cada jogo. Corrigir uma posição é uma linha em `fato_classificacao`.
- `time_id` é o `chave_time` (nome sem acento, minúsculo), a mesma chave que já cruzava as fontes.

### Decisões de modelagem

- **Entrada da `fato_jogo`:** `prata.odds_enriquecido`, a tabela da aula de enriquecimento. O join
  daquela aula não foi exercício: é a entrada da fato. O `WHERE posicao_casa IS NOT NULL AND
  posicao_visitante IS NOT NULL` é o filtro de integridade (a validação do join virou o filtro
  da fato). Nenhum jogo é excluído hoje, e a carga avisa se algum for.
- **Colunas que entram na fato:** identificadores, data, temporada, gols, resultado, odds da
  Bet365, probabilidades implícitas, faixa e marcação de extremos por IQR.
- **Colunas que ficam só na prata:** odds das outras casas (correlacionadas com a Bet365, ver
  defeitos conhecidos), placar do intervalo (não serve às perguntas), `Unnamed: 0` e `Div` (sem
  informação), marcação por z-score e as colunas `tsdb_*` (são de 2024/25, outra temporada).
- **Nomes de negócio:** `B365H` vira `odd_casa`, `FTHG` vira `gols_casa`, e `FTR` (H, D, A) vira
  `resultado` com os valores `casa`, `empate` e `visitante`.
- **A tabela achatada** da aula de enriquecimento passa a ser a view `ouro.vw_jogo_completo`:
  não guarda dado, o banco executa o join na hora, então não tem arquivo para manter nem risco
  de ficar desatualizada. As dimensões entram com `JOIN`; a classificação entra com `LEFT JOIN`,
  para um jogo sem posição aparecer com nulo em vez de sumir. O `odds_enriquecido.parquet`
  continua sendo gerado pela etapa de enriquecimento e é a origem da estrela.
- **Cuidado de interpretação:** a posição vem da classificação **final** da temporada, calculada
  com os próprios jogos, então inclui o jogo em questão. Serve para agrupar times por força, mas
  não é informação disponível antes da partida.

### Conferências da ouro

Eram 9 consultas escritas à mão no `carga.py`; agora são **testes do dbt** (seção *Testes e
documentação (dbt)*), com o mesmo critério: grão de cada tabela, nenhum fato órfão e a view sem
multiplicar linhas.

### Como rodar e consultar

```
python src/pipeline.py carga        # só a carga da prata no banco
python src/pipeline.py modelagem    # dbt run (constrói a ouro) + dbt test (confere)
```

Apagar `dados/ouro/projeto.duckdb` é uma forma legítima de recomeçar do zero: a carga recria
a prata e o dbt recria a ouro, a partir dos parquets. O banco fica fora do Git (`dados/ouro/*` está no
`.gitignore`), pelo mesmo motivo da prata: é reproduzível.

Exemplo de consulta (probabilidade implícita contra a frequência real, por faixa):

```sql
SELECT
    prob_casa_faixa,
    COUNT(*)                                                           AS jogos,
    AVG(prob_casa)                                                     AS prob_implicita_media,
    AVG(CASE WHEN resultado = 'casa' THEN 1.0 ELSE 0.0 END)            AS freq_vitoria_casa
FROM ouro.fato_jogo
GROUP BY prob_casa_faixa
ORDER BY MIN(prob_casa);
```

## Transformação declarativa (dbt)

Até a aula anterior, a ouro era construída por `CREATE TABLE ... AS SELECT` escritos como
texto dentro de `carga.py`. Funcionava, mas a ordem entre as tabelas só existia na cabeça de
quem escreveu, não dava para refazer só um pedaço, o `conferir()` era um registro que alguém
precisava ler e a documentação ficava em comentário solto. Nenhum desses problemas é do DuckDB
ou do Python: são problemas de organizar transformação.

O **dbt** (data build tool, versão Core, gratuita) pega um `SELECT` e materializa o resultado
dentro do banco, como tabela ou view. Ele **não executa** SQL: escreve o SQL e entrega ao
DuckDB, pelo adaptador `dbt-duckdb`. O que ele **não faz** continua em Python: baixar dado,
ler arquivo para dentro do banco, agendar.

### Estrutura (`ecox14/`)

```
ecox14/
  dbt_project.yml          nome, pastas, materialização padrão (tabela)
  profiles.yml             como conectar: ../dados/ouro/projeto.duckdb, esquema ouro
  models/
    sources.yml            as 4 tabelas da prata que o carga.py leva ao banco
    schema.yml             descrição de cada coluna + testes (ver seção abaixo)
    docs.md                descrições reaproveitadas pela fato e pela view
    dim_time.sql           tabela
    fato_classificacao.sql tabela
    fato_jogo.sql          tabela
    vw_jogo_completo.sql   view ({{ config(materialized='view') }}, usa ref)
  tests/                   testes escritos à mão (uma consulta por arquivo)
```

- **Um modelo é um arquivo `.sql` com um `SELECT`.** O nome do arquivo é o nome da tabela. Os
  `SELECT` são os mesmos da aula 9, sem o `CREATE TABLE` em volta.
- **`source('prata', 'odds_enriquecido')`** aponta para uma tabela que o dbt não cria.
  **`ref('fato_jogo')`** aponta para outro modelo e cria a dependência: só a view usa `ref`.
  Daí o dbt monta o grafo e decide a ordem sozinho (as três tabelas, depois a view).
- **Tabela ou view** é uma linha de configuração: a view da aula 9 é um modelo com
  `materialized='view'` no topo. Trocar por tabela, se um dia ficar lenta, é mudar uma palavra.
- O `where posicao_casa is not null and posicao_visitante is not null` da `fato_jogo`
  continua sendo o filtro de integridade que veio da junção da aula 7.

### Decisões

- **`profiles.yml` dentro do repositório**, e não em `C:\Users\<usuario>\.dbt`: o dbt procura
  primeiro o arquivo da pasta onde roda, e o pipeline roda o dbt de dentro de `ecox14/`. Assim o
  caminho do banco é relativo (`../dados/ouro/projeto.duckdb`), o projeto funciona em qualquer
  máquina sem configuração extra e não há segredo no arquivo. Um `profiles.yml` na pasta de
  usuário continua existindo sem atrapalhar.
- **O pipeline chama `python -m dbt.cli.main run`**, com o mesmo Python que roda o pipeline,
  em vez do comando `dbt`: não depende do PATH nem do `dbt.exe` do ambiente virtual. Com
  `check=True`, se o dbt falhar o Python levanta erro e o pipeline para; sem isso diria que
  terminou bem com a ouro quebrada.
- **`construir_ouro` ficou em `carga.py`, só com a chamada comentada**, para comparar as duas
  formas. A carga agora só carrega a prata. As conferências antigas (`conferir_ouro`) também
  ficaram, sem uso: quem cobra as regras é o `dbt test`, que roda depois do `dbt run` na etapa
  `modelagem`.
- **O dbt não cria `dev.duckdb` nem `models/example/`**: o projeto foi escrito à mão em vez de
  `dbt init`, então não há banco vazio para o perfil apontar por engano. `target/` e `logs/`
  (gerados a cada execução, inclusive o SQL que o dbt enviou ao banco) ficam fora do Git.

### Como rodar

```
python src/pipeline.py modelagem        # dbt run + conferências
cd ecox14
dbt debug                               # mostra qual profiles.yml lê e testa a conexão
dbt run                                 # constrói os 4 modelos
dbt run --select dim_time+              # só a dimensão e o que depende dela
```

`Database Error: file is locked` significa que o banco está aberto em outro lugar (um
notebook, um terminal com `duckdb.connect`): feche a outra conexão e rode de novo.

### Verificação da migração

A ouro construída pelo dbt foi comparada com a construída pelo SQL antigo, tabela por tabela
(`EXCEPT` nos dois sentidos): mesmas linhas (23, 40, 760 e 760 na view), mesmas colunas e
tipos, zero diferença. Rodar o pipeline do zero, com o banco apagado, dá o mesmo resultado e
todos os testes passam. Trocar uma coluna por uma inexistente num modelo faz o dbt
falhar e o pipeline terminar com erro.

## Testes e documentação (dbt)

Um teste automatizado é uma regra escrita que o computador confere sozinho toda vez que o
pipeline roda. Em dado, o que se testa é o **resultado** (o código pode estar certo e o dado
chegar errado da fonte). Antes, a conferência era um `log.info` que alguém precisava ler; agora
um teste que falha **para o pipeline**.

**Convenção:** um teste é uma consulta que procura o defeito e **passa quando devolve zero
linhas**. `FAIL 7` quer dizer "encontrou 7 linhas que não deveriam existir".

### Dois tipos de teste

- **Pronto:** declarado no `ecox14/models/schema.yml`; o dbt escreve a consulta. Usados aqui:
  `unique`, `not_null`, `relationships` e `accepted_values`.
- **Próprio:** um `.sql` em `ecox14/tests/`, para o que nenhum teste pronto cobre. É o caso das
  chaves compostas.

| Conferência antiga (`carga.py`) | Teste do dbt |
|---|---|
| `fato_jogo`: `jogo_id` repetido | `unique` e `not_null` em `fato_jogo.jogo_id` |
| `fato_classificacao`: (time, temporada) repetido | próprio: `tests/grao_fato_classificacao.sql` (chave composta) |
| `dim_time`: `time_id` repetido | `unique` e `not_null` em `dim_time.time_id` |
| `fato_jogo` sem o mandante na `dim_time` | `relationships` em `time_casa_id` |
| `fato_jogo` sem o visitante na `dim_time` | `relationships` em `time_visitante_id` |
| `fato_classificacao` sem o time na `dim_time` | `relationships` em `time_id` |
| jogo sem classificação do mandante na temporada | próprio: `tests/jogo_sem_classificacao_mandante.sql` |
| jogo sem classificação do visitante na temporada | próprio: `tests/jogo_sem_classificacao_visitante.sql` |
| view com linhas a mais ou a menos que a fato | próprio: `tests/view_com_linhas_diferentes_da_fato.sql` |

Além desses nove, entraram regras novas: `accepted_values` em `resultado` (só `casa`, `empate`,
`visitante`), `not_null` nas colunas essenciais e um teste próprio de domínio
(`tests/odds_fora_do_dominio.sql`: odd decimal nunca é menor que 1,0, e a decisão de tratamento
já dizia que isso seria erro de coleta). Total: **26 testes** (21 gerados do YAML e 5 próprios).

```
cd ecox14
dbt test                                                        # todos
dbt test --select fato_jogo                                     # só os da fato_jogo
dbt test --select grao_fato_classificacao --store-failures      # grava as linhas que falharam
```

Com `--store-failures` o dbt grava as linhas defeituosas numa tabela (esquema
`ouro_dbt_test__audit`) para investigar: teste que só diz "falhou" não ajuda ninguém.

**Os testes foram provados, não só escritos.** Cinco defeitos foram injetados na ouro (jogo
repetido, classificação repetida, mandante inexistente, resultado inválido, odd abaixo de 1,0) e
o `dbt test` acusou 7 falhas, saindo com erro. Com um modelo alterado de propósito, a etapa
`modelagem` do pipeline falhou e o pipeline parou.

### Documentação

A descrição de cada coluna fica no `schema.yml`, ao lado do teste. As frases reaproveitadas pela
`fato_jogo` e pela `vw_jogo_completo` ficam uma vez só em `ecox14/models/docs.md` (blocos
`docs`). Os 4 modelos e as 56 colunas estão documentados. Nada é escrito duas vezes, então a
descrição não fica desatualizada: ou está certa, ou o código mudou junto.

```
cd ecox14
dbt docs generate
dbt docs serve            # abre o site em localhost:8080 (Ctrl+C para parar)
```

O site mostra o grafo dos modelos (as fontes da prata, as três tabelas, a view) e o que cada
coluna significa. É o que mostra **o que as tabelas são**. Para ver **o que há dentro delas**, as
linhas de verdade, use a interface do DuckDB:

1. baixe o pacote de linha de comando do Windows em duckdb.org e descompacte o `duckdb.exe` na
   raiz do projeto (ele está no `.gitignore`: é programa, não é código);
2. na raiz do projeto: `.\duckdb.exe -ui dados/ouro/projeto.duckdb` (abre em `localhost:4213`).

Feche o painel do DuckDB antes de rodar o pipeline, e o pipeline antes de abrir o painel: o
DuckDB trava o arquivo.

## Painel (`dashboard/`)

O dado chega a quem precisa dele. O painel é feito em **Streamlit** (biblioteca que transforma
um script Python em página web, grátis e local) e responde à pergunta do projeto: dentro de cada
faixa de favoritismo do mandante, a probabilidade implícita na odd bate com a frequência real de
vitória?

```
streamlit run dashboard/painel.py       # a partir da raiz; abre o navegador. Ctrl+C para parar
```

```
dashboard/
  consultas.py     todo o SQL de leitura: uma função por pergunta
  painel.py        só a tela: nenhuma linha de SQL
```

- **Consumidor, não produtor.** O painel abre o banco com `read_only=True`: não cria nem altera
  nada e, aberto, não impede o dbt de rodar. A seta aponta num sentido só, da ouro para o painel,
  e por isso a pasta fica fora de `src/` e fora do pipeline. Ele precisa que a ouro já exista
  (`python src/pipeline.py modelagem`).
- **Onde o SQL mora.** SQL que cria tabela vive no dbt, versionado e testado. SQL de leitura vive
  em `consultas.py`, reaproveitável fora do painel. A tela não tem SQL. Valor que vem da tela
  entra como parâmetro (`?`), nunca concatenado no texto, e o banco nunca o interpreta como
  comando (testado com um valor do tipo `2021/22' or '1'='1`, que devolve zero linhas).
- **Tela:** filtros de temporada e de força relativa (mandante ou visitante melhor posicionado),
  três números (jogos, vitórias do mandante, probabilidade implícita média), o gráfico de
  calibração com a diagonal de calibração perfeita, a tabela por faixa e um rodapé com a fonte
  lida da proveniência da ingestão.
- **A probabilidade é normalizada no painel.** A ouro guarda `prob_casa` bruta (1/odd), cuja soma
  das três opções é em média 1,054, porque a odd embute a margem da casa de apostas. Comparar a
  bruta com a frequência real faria o mercado parecer enviesado só por causa da margem. A consulta
  divide pela soma das três e mostra as duas versões lado a lado. Se essa normalização virar
  definição oficial do projeto, o lugar certo dela é uma coluna do `fato_jogo` no dbt.
- **O filtro de força relativa exige cuidado**, e o painel avisa na tela quando ele está ligado:
  a posição vem da classificação final da temporada, que já inclui o resultado dos jogos. Times
  que terminam bem posicionados venceram mais, então a frequência real aparece acima da
  probabilidade implícita sem que isso diga algo sobre as odds (por exemplo, "mandante melhor
  posicionado" mostra +6,8 pontos percentuais; no total geral a diferença é de +2,1). Para
  afirmar algo sobre força relativa seria preciso uma classificação anterior ao jogo.

## Governança

No momento em que o número aparece na tela de alguém, ele deixa de ser só do projeto e passa a
embasar uma decisão. Três perguntas:

- **De onde veio este número?** Registrado em todas as camadas: a bronze guarda a fonte, o
  arquivo e a data de extração (`proveniencia.json`), a prata registra o que foi feito em cada
  transformação (`proveniencia.jsonl`) e o painel mostra a fonte no rodapé.
- **Quem pode vê-lo?** O painel roda na máquina de quem o executa (`localhost`), sem publicação
  e sem acesso externo.
- **O que acontece se estiver errado?** Os testes do dbt param o pipeline. Limite conhecido: o
  `dbt run` já gravou a ouro quando o `dbt test` falha, então um painel aberto depois disso
  mostraria a ouro defeituosa. O pipeline avisa, mas o painel não sabe. Dá para reconstruir como
  qualquer número foi calculado: a bronze é versionada, a prata é reproduzível, o SQL dos modelos
  está no repositório e o dbt grava o SQL que enviou ao banco em `ecox14/target/`.

**Dado pessoal.** Nenhum dado do projeto identifica pessoas: são resultados de partidas, odds e
classificação de times, de fontes públicas e agregadas. Isso foi uma escolha de projeto. Com dado
pessoal (LGPD) seriam outras decisões, todas registradas e nenhuma técnica: coletar só o
necessário, dizer para que serve, definir prazo de descarte e controlar quem acessa.
