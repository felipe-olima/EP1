# Motor de tableaux — parte 3

## Como testar agora

Requer Python 3.10 ou superior (as anotações de tipos existentes no projeto
também usam essa versão). Não é necessário instalar bibliotecas externas.
Na pasta do repositório:

```bash
python -m unittest -v test_motor
```

Os testes constroem as fórmulas com as classes do `code_base_EP1.py`, sem
depender do parser. Para experimentar um caso válido e um inválido:

```bash
python - <<'PY'
from code_base_EP1 import Variable, Implies
from motor import provar
from saida import formatar

p, q = Variable('p'), Variable('q')
for premissas, conclusao in [([p, Implies(p, q)], q), ([p], q)]:
    resultado = provar(premissas, conclusao)
    print(formatar(premissas, conclusao, resultado))
    print('Estatísticas:', resultado.estatisticas)
PY
```

## Interface e resultado

`provar(premissas, conclusao, estrategia='combinada')` recebe objetos de fórmula
e devolve o `Resultado` definido em `tipos.py`. As premissas podem ser uma lista
ou outro iterável; o motor não modifica a lista nem as árvores recebidas.

A estratégia pode ser `direta`, `reversa`, `menor`, `subformula`, `combinada`,
ou uma função `(ramo, candidatos) -> indice`. A função deve apenas escolher
um dos índices fornecidos, sem modificar o ramo. Nomes desconhecidos e índices
que não são de uma β pendente causam `ValueError`.

O motor aceita os nós da linguagem combinada pelo grupo: `Variable`, `Constant`,
`Not`, `And`, `Or` e `Implies`. Conjunções e disjunções podem ter um ou mais
operandos. Nós genéricos `Proposition`, outros conectivos e `And()`/`Or()` sem
operandos são recusados com `ValueError`.

- `valido`: indica se todos os ramos fecharam.
- `contraexemplo`: `None` quando válido; caso contrário, um dicionário com todos
  os átomos do sequente e seus valores booleanos.
- `regras`: lista cronológica de `(nome_da_regra, fórmula_marcada)`. O nome vem
  de `regras.py`; a fórmula usa `str(FormulaMarcada)`, com os símbolos nativos
  do código-base, por exemplo `('β→', 'T p => q')`.
- `estatisticas['expansoes']`: quantidade de aplicações de regra, igual ao
  tamanho de `regras`. Uma regra com vários filhos conta como uma aplicação.
- `estatisticas['ramos_fechados']`: quantidade de ramos visitados que fecharam,
  incluindo fechamento inicial. Um ramo aberto não entra nessa contagem.
- `estatisticas['tempo']`: duração em segundos, medida com `perf_counter`,
  incluindo validação de entrada e conferência do contraexemplo.
- `estatisticas['atomos_livres']`: lista ordenada dos átomos que não apareceram
  como literais no ramo aberto; eles foram completados com `False`. É vazia
  quando o resultado é válido.

O contraexemplo é conferido com `evaluate(**valores)`: todas as premissas devem
ser verdadeiras e a conclusão deve ser falsa. Falha nessa condição gera
`RuntimeError`, em vez de retornar uma resposta logicamente incorreta.

## Como a DFS funciona

1. Criar o ramo `T A1, ..., T An, F B` e uma pilha vazia.
2. Se o ramo fechar, retirar a última alternativa da pilha e restaurar seu
   estado. Se não houver alternativa, o sequente é válido.
3. Aplicar as α pendentes, sempre verificando fechamento após cada adição.
   Recalcular as pendências também processa as novas α geradas nessa etapa.
4. Quando não restar α, selecionar uma β usando a estratégia recebida.
5. Marcar a β como expandida e registrar sua aplicação. Só então salvar o
   estado, empilhar as alternativas restantes e adicionar a primeira.
6. Voltar ao passo 2. Se não houver nenhuma expansão pendente e o ramo
   continuar aberto, devolver seu contraexemplo conferido.

A pilha usa `append` e `pop`: a última bifurcação é retomada primeiro. Cada
entrada contém `(alternativa, Estado)`. O `Estado` registra o tamanho do ramo
e uma cópia das marcas de expansão; `Ramo.restaurar()` trunca as fórmulas e
reconstrói o índice de fechamento. As alternativas de uma mesma bifurcação
compartilham o estado salvo, que não é modificado pelo motor.

Salvar **depois de marcar a β** evita expandir a mesma fórmula de novo ao
retomar uma alternativa. O histórico de regras não é restaurado: deve mostrar
também o trabalho realizado nos ramos que já fecharam.

Para três ou mais alternativas, as restantes são empilhadas em ordem inversa,
preservando a ordem original da exploração. Alternativas repetidas são
identificadas por tuplas de `(sinal, chave_textual)`, sem comparar fórmulas com
`==`. Se restar uma só alternativa, como na regra `F ~p -> T p`, não se salva
estado nem se empilha um ramo artificial.

### Exemplo de restauração

Para `p | q, ~p |- r`, com qualquer estratégia:

1. O ramo inicial é `T (p | q), T ~p, F r`.
2. A α da negação acrescenta `F p`.
3. A β da disjunção é marcada. Salvar esse estado e empilhar `[T q]`.
4. Adicionar `T p` fecha o ramo, pois ele já contém `F p`.
5. Restaurar o estado: retirar o `T p` acrescentado, manter as marcas anteriores
   e adicionar `T q`.
6. O ramo está aberto e saturado: `p=False, q=True, r=False` é um contraexemplo.

## Testes e integração com o grupo

Os sequentes fixos do plano são comparados com
`ArgumentForm.is_valid_truth_table()` nas cinco estratégias. Os testes também
cobrem restauração aninhada, prioridade de α, negação sem bifurcação,
conectivos com três filhos, constantes, átomos livres, histórico e escolhas
inválidas. Um gerador com semente `239` cria 500 sequentes com até cinco átomos
e profundidade quatro; cada um é executado nas cinco estratégias, totalizando
2.500 comparações aleatórias. A tabela-verdade só é usada nos testes.

O script `usar_tableaux.py` já importa `provar`, e a assinatura do motor é
compatível. Porém, o parser atual ainda cria `Proposition(texto)` em vez de uma
árvore lógica e retorna um `GenericAlias` em `parse_sequente`, em vez do par
`(premissas, conclusao)`. A execução completa a partir de texto depende da
conclusão dessa parte pelo colega responsável. O parser não foi alterado aqui.

`saida.formatar()` já aceita o resultado, como o exemplo e o teste verificam.
Como o motor devolve um contraexemplo completo, o formatador atual imprime
todos os átomos, mas não acrescenta o rótulo `(livre)`. O colega da saída pode
usar `estatisticas['atomos_livres']` para exibir esse rótulo sem mudar o contrato.

## Git: desenvolver separado e integrar depois

Para obter o projeto no seu próprio terminal, a partir da pasta desejada:

```bash
git clone https://github.com/felipe-olima/EP1.git
cd EP1
```

Se a branch já tiver sido publicada, use:

```bash
git fetch origin
git switch --track origin/feat/motor-dfs
```

Se ela ainda não existir, crie-a com `git switch -c feat/motor-dfs`.
Antes de preparar seu commit, execute os testes e confira apenas os arquivos
da sua parte:

```bash
python -m unittest -v test_motor
git diff
git status --short
git add motor.py test_motor.py docs/motor.md
git diff --cached
git commit -m "Implementa motor de tableaux com busca em profundidade"
git push -u origin feat/motor-dfs
```

No GitHub, abra um pull request de `feat/motor-dfs` para `main`, descrevendo o
motor, os testes e a dependência do parser. Peça revisão à pessoa responsável
por regras e ramo. Faça a integração depois dos testes e da revisão combinada
no grupo.

### Receber a branch pelo arquivo Git

Se você recebeu `EP1-motor-dfs.bundle`, ele contém o histórico do projeto e
o commit desta implementação. Como você ainda não clonou o projeto, pode
cloná-lo diretamente desse arquivo, substituindo o caminho abaixo pelo local
onde salvou o download:

```bash
git clone -b feat/motor-dfs /caminho/EP1-motor-dfs.bundle EP1
cd EP1
git remote set-url origin https://github.com/felipe-olima/EP1.git
python -m unittest -v test_motor
git push -u origin feat/motor-dfs
```

O commit já está incluído no arquivo; não é preciso recriá-lo. O envio exige
que seu Git esteja autenticado na conta que é colaboradora do repositório.
Depois do envio, abra o pull request para `main` como descrito acima.

## Rascunho para o relatório: estratégia de busca de ramos

Implementamos a estratégia de busca em profundidade descrita no Algoritmo 4.1
e na seção 4.1 do material complementar. O ramo inicial contém as premissas
marcadas como verdadeiras e a conclusão marcada como falsa. Em cada iteração,
as regras α são aplicadas antes das regras β, pois não criam bifurcações.

O motor mantém um ramo atual e uma pilha de alternativas. Antes de explorar a
primeira alternativa de uma regra β, registra a fórmula como expandida e salva
o tamanho do ramo e suas marcas de expansão. Quando o ramo fecha, restaura o
estado da bifurcação mais recente e explora a próxima alternativa. Assim, não
é necessário armazenar uma árvore completa de ramos. Há, porém, o custo das
cópias das marcas em cada estado salvo e do histórico completo de expansões;
não assumimos que a memória total desta implementação seja estritamente linear.

Se todos os ramos fecham, o sequente é válido. Se a busca encontra um ramo
aberto e saturado, extrai os valores de seus átomos e completa os átomos livres
com falso. Antes de devolver esse contraexemplo, verifica diretamente que ele
satisfaz todas as premissas e falsifica a conclusão. O resultado inclui também
a sequência de regras aplicada em todos os ramos visitados, o número de
expansões, o número de ramos fechados e o tempo de execução.
