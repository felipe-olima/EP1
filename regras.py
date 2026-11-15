from code_base_EP1 import Variable, Constant, Not, And, Or, Implies
from tipos import FormulaMarcada

def tipo(fm: FormulaMarcada) -> str:
    f = fm.formula
    sinal= fm.sinal

    if isinstance(f, Variable):
        return 'literal'

    if isinstance(f, Constant):
        return 'constante'  

    if isinstance(f, And):
        if sinal:   
            return 'alfa'
        else:
            return 'beta'

    if isinstance(f, Or):
            if sinal:   
                return 'beta'
            else:
                return 'alfa'

    if isinstance(f, Implies):
            if sinal:   
                return 'beta'
            else:
                return 'alfa'

    if isinstance(f, Not):
            if sinal:   
                return 'alfa'
            else:
                return 'beta'

def expandir(fm: FormulaMarcada) -> tuple[str, list[list[FormulaMarcada]]]:

    f = fm.formula

    if isinstance(f, And):

        filhos = f.children

        if tipo(fm) == 'alfa':
            return ('α∧', [[FormulaMarcada(True, filho)for filho in filhos]])   
        else:
            return ('β∧', [[FormulaMarcada(False, filho)] for filho in filhos])

    if isinstance(f, Or):

        filhos = f.children

        if tipo(fm) == 'alfa':
            return ('α∨', [[FormulaMarcada(False, filho) for filho in filhos]])   
        else:
            return ('β∨', [[FormulaMarcada(True, filho)] for filho in filhos])

    if isinstance(f, Implies):
            
            if tipo(fm) == 'alfa':
                return ('α→', [[FormulaMarcada(True, f.children[0] ), FormulaMarcada(False, f.children[1])]])   
            else: 
                return ('β→', [[FormulaMarcada(False, f.children[0])], [FormulaMarcada(True, f.children[1])]])

    if isinstance(f, Not):
                
                if tipo(fm) == 'alfa':
                    return ('α¬', [[FormulaMarcada(False, f.children[0])]])   
                else:
                    return ('β¬', [[FormulaMarcada(True, f.children[0])]])

    raise ValueError( "Não é possível expandir uma fórmula literal ou constante" )