from dataclasses import dataclass 
from code_base_EP1 import Proposition 

@dataclass(eq=False)   
class FormulaMarcada: 
    sinal: bool   
    formula: Proposition     
    def chave(self) -> str:      
        return str(self.formula) 
    def __str__(self) -> str: 
        return ('T ' if self.sinal else 'F ') + str(self.formula) 

@dataclass 
class Resultado: 
    valido: bool 
    contraexemplo: dict[str, bool] | None  
    regras: list[tuple[str, str]]         
    estatisticas: dict 