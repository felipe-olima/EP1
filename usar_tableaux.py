import argparse

from parser import parse_sequente, parse_formula
from motor import provar
from saida import formatar, para_linguagem

from estrategias import ESTRATEGIAS as _ESTRATEGIAS
ESTRATEGIAS = list(_ESTRATEGIAS)

def processar(texto, estrategia): #faz o trabalho de uma linha de sequente 
    texto = texto.replace('|-', '⊢')
    if '⊢' not in texto: #lê a fórmula e mostra como o parser entendeu usando o para_linguagem
        f = parse_formula(texto)
        print('Fórmula lida como: ' + para_linguagem(f))
        return
    premissas, conclusao = parse_sequente(texto) #o parser separa o texto em lista de premissas e conclusão
    r = provar(premissas, conclusao, estrategia) 
    print(formatar(premissas, conclusao, r))

def rodar_arquivo(caminho,estrategia):
    with open(caminho, encoding='utf-8') as f: 
        for linha in f:
            linha = linha.strip() #tira espaços e quebra de linha das pontas
            if linha == '' or linha.startswith('#'): #pula linhas vazias e comentários
                continue
            print('-' * 40) #desenha uma linha de 40 traços entre os sequentes
            try: #se uma linha der erro, o script mostra qual foi e continua nas próximas
                processar(linha, estrategia)
            except Exception as erro:
                print('ERRO em "' + linha + '": ' + str(erro))

def modo_interativo(estrategia):
    prem = input('Premissas (separadas por vírgula. Caso não houver, vazio): ')
    concl = input('Conclusão: ')
    processar(prem + ' |- ' + concl, estrategia)

def main():
    ap = argparse.ArgumentParser(description='Provador por tableaux') #cria o leitor de argumentos
    ap.add_argument('sequente', nargs='?') #o argumento é opcional, isto é, se o usuário digitar o sequente, args.sequente guarda o texto. Caso contrário, args.sequente vale None, que vale para os casos em que o usuário entra com um arquivo ou entra no modo interativo 
    ap.add_argument('--arquivo', help='arquivo com um sequente por linha') 
    ap.add_argument('--estrategia', default='combinada', choices=ESTRATEGIAS) #a estratégia padrão é a combinada e choices=ESTRATEGIAS recusa qualquer nome fora da lista 
    args = ap.parse_args() #lê o que foi digitado

    if args.arquivo: #se veio --arquivo
        rodar_arquivo(args.arquivo, args.estrategia)
    elif args.sequente: #se veio sequente
        processar(args.sequente, args.estrategia)
    else: #caso contrário, entra no modo interativo 
        modo_interativo(args.estrategia)

if __name__ == '__main__': #apenas quando roda esse arquivo direto 
    main()
