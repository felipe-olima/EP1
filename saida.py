from code_base_EP1 import Constant, Variable, Not, And, Or, Implies
from tipos import Resultado

def _simples(f):
    #se a fórmula for simples o suficiente para não precisar de parênteses, como variáveis, constantes e a negação
    return isinstance(f, (Variable, Constant, Not))

#converte um filho e, caso não seja simples, coloca entre parênteses
def _filho(f):
    s = para_linguagem(f)
    return s if _simples(f) else '(' + s + ')'

#olha o tipo da fórmula e escreve de acordo
def para_linguagem(f):
    #caso base 1
    if isinstance(f, Constant):
        return 'T' if f.value else 'F'
    #caso base 2 
    if isinstance(f, Variable):
        return f.name
    if isinstance(f, Not): 
        return '~' + _filho(f.children[0]) #escreve ~ e cola o texto desse filho. O filho chama a função de novo e põe o parênteses caso necessário
    if isinstance(f, And):
        return ' & '.join(_filho(c) for c in f.children) #junta uma lista de texto usando & no meio 
    if isinstance(f, Or):
        return ' | '.join(_filho(c) for c in f.children)
    if isinstance(f, Implies):
        return _filho(f.children[0]) + ' >> ' + _filho(f.children[1]) #escreve antecedente >> consequente
    return str(f) # se nao caiu em nenhum caso acima (Iff e ImpliedBy) usa o padrão do code_base

#recebe a lista de premissas, conclusao e resultado e devolve o texto completo da resposta
def formatar(premissas, conclusao, r: Resultado) -> str: 
    prem = ', '.join(para_linguagem(p) for p in premissas) #converte cada premissa para texto e junta com vírgula
    linhas = ['Sequente: ' + prem + ' |- ' + para_linguagem(conclusao)] 
    linhas.append('Resultado: ' + ('VÁLIDO' if r.valido else 'INVÁLIDO'))
    if not r.valido: #só sequente inválido tem contraexemplo
        todos = set() #todas as variáveis do sequente
        for f in premissas + [conclusao]:
            todos |= set(f.variables())
        partes = [f'{a} = {"V" if v else "F"}'
                  for a, v in sorted(r.contraexemplo.items())]
        livres = sorted(todos - set(r.contraexemplo)) #variaveis do sequente menos as que estão no contraexemplo, restando as que o ramo não mencionou
        partes += [f'{a} = F (livre)' for a in livres]
        linhas.append('Contraexemplo: ' + ', '.join(partes))
    linhas.append('Regras: ' + str(r.regras))
    return '\n'.join(linhas)
