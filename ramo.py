
from dataclasses import dataclass
from code_base_EP1 import Variable, Constant
from tipos import FormulaMarcada
from regras import tipo


@dataclass
class Estado:

    tamanho: int
    expandida: list[bool]


class Ramo:

    def __init__(self):
        self.formulas = []
        self.expandida = []
        self.vistos = {}
        self._fechado = False

    def adicionar(self, fm: FormulaMarcada) -> bool:

        chave = fm.chave()
        sinal = fm.sinal

        self.formulas.append(fm)
        self.expandida.append(False)

        # Verifica se a fórmula já apareceu com sinal oposto
        if chave in self.vistos:
            if (not sinal) in self.vistos[chave]:
                self._fechado = True
        else:
            self.vistos[chave] = set()

        # Registra o sinal da fórmula
        self.vistos[chave].add(sinal)

        # Verifica se uma constante provoca fechamento
        if isinstance(fm.formula, Constant):
            if fm.formula.value != sinal:
                self._fechado = True

        return self._fechado

    def fechado(self) -> bool:
        return self._fechado

    def pendentes_alfa(self) -> list[int]:

        if self._fechado:
            return []

        return [
            i for i, fm in enumerate(self.formulas)
            if not self.expandida[i] and tipo(fm) == 'alfa'
        ]

    def pendentes_beta(self) -> list[int]:

        if self._fechado:
            return []

        return [
            i for i, fm in enumerate(self.formulas)
            if not self.expandida[i] and tipo(fm) == 'beta'
        ]

    def marcar(self, i: int) -> None:

        self.expandida[i] = True

    def estado(self) -> Estado:

        return Estado(
            tamanho=len(self.formulas),
            expandida=self.expandida.copy()
        )

    def restaurar(self, e: Estado) -> None:
       
        self.formulas = self.formulas[:e.tamanho]
        self.expandida = e.expandida.copy()

        self.vistos = {}
        self._fechado = False

        for fm in self.formulas:
            chave = fm.chave()
            sinal = fm.sinal

            if chave not in self.vistos:
                self.vistos[chave] = set()

            if (not sinal) in self.vistos[chave]:
                self._fechado = True

            self.vistos[chave].add(sinal)

            if isinstance(fm.formula, Constant):
                if fm.formula.value != sinal:
                    self._fechado = True

    def valoracao(self) -> dict[str, bool]:
        
        valores = {}

        for fm in self.formulas:
            if isinstance(fm.formula, Variable):
                valores[fm.formula.name] = fm.sinal

        return valores
