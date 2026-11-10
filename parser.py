from code_base_EP1 import Proposition

def parse_formula(texto: str) -> Proposition:
    return Proposition(texto.strip())

def parse_sequente(texto: str) -> tuple[list[Proposition], Proposition]:
    str_premises, str_consequente = texto.split("⊢")
    str_premises = str_premises.split(",")

    premises = [parse_formula(i.strip()) for i in str_premises]
    return tuple[premises,parse_formula(str_consequente.strip())]
         
    

def ler_arquivo(caminho: str) -> list[tuple[list[Proposition], Proposition]]:
        f = open(caminho,"r",encoding="utf-8")
        linhas = [parse_sequente(i) for i in f]
        f.close()
        return linhas
