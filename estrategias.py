from regras import expandir 


def tamanho(f):
    #conta os nós da fórmula: ela mesma  (1) + o tamanho dos filhos
    return 1 + sum(tamanho(c) for c in f.children)

def pontos_subformula(ramo, i):
    #quantas subfórmulas da beta na posição i já tem a polaridade oposta no ramo
    vistos = {(fm.chave(), fm.sinal) for fm in ramo.formulas} #guarda o que já está no ramo, como pares (fórmula, sinal)
    _, filhos = expandir(ramo.formulas[i])      
    pontos = 0
    for lado in filhos: #para cada lado, olha se o oposto dele já esta no ramo. Se estiver, esse lado vai fechar logo, então ganha 1 ponto
        for sub in lado:
            if (sub.chave(), not sub.sinal) in vistos:
                pontos += 1
    return pontos
    #se beta é T p >> q, vira F p e T q. Se o ramo já tem T p o lado F p fecha na hora: nota 1 

#pega a primeira fórmula beta da lista que ocorre no ramo para expansão
def direta(ramo, candidatos): 
    return candidatos[0]

#seleciona a última fórmula beta que ocorre no ramo para expansão
def reversa(ramo, candidatos):
    return candidatos[-1]

#seleciona a menor das fórmulas beta, já que, quanto menor a fórmula, mais fácil fechar o ramo
def menor(ramo, candidatos):
    return min(candidatos, key=lambda i: tamanho(ramo.formulas[i].formula))

#da a preferência para uma fórmula se houver subfórmulas suas presentes no ramo
def subformula(ramo, candidatos):
    # max pontos; empate fica com o primeiro (min escolhe o primeiro menor)
    return min(candidatos, key=lambda i: -pontos_subformula(ramo, i))

def combinada(ramo, candidatos):
    #Inicialmente, encontramos as fórmulas que contém fórmulas de polaridade oposta. Em caso se empate, selecionamos a de menor tamanho. Se ainda houver empate, selecionamos a ordem direta 
    return min(candidatos,
               key=lambda i: (-pontos_subformula(ramo, i), #troca o sinal já que, embora o min pegue o menor, queremos a beta com mais pontos
                              tamanho(ramo.formulas[i].formula))) #desempate: escolhe o menor tamanho

ESTRATEGIAS = {'direta': direta, 'reversa': reversa, 'menor': menor,
               'subformula': subformula, 'combinada': combinada}

def escolher_beta(ramo, candidatos, nome='combinada'):
    return ESTRATEGIAS[nome](ramo, candidatos)
