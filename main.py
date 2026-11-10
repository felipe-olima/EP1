from parser import *



print(parse_formula("(p>>q)"))
print(parse_sequente("p,(p>>q) ⊢ q"))
print(ler_arquivo("file.txt"))