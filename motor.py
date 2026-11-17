"""Provador por tableaux: busca em profundidade com prioridade para regras α."""

from collections.abc import Callable, Iterable
from time import perf_counter

from code_base_EP1 import And, Constant, Implies, Not, Or, Proposition, Variable
from estrategias import ESTRATEGIAS
from ramo import Estado, Ramo
from regras import expandir
from tipos import FormulaMarcada, Resultado


EscolhaBeta = Callable[[Ramo, list[int]], int]


def _validar_formula(formula: Proposition) -> None:
    """recusa nós que não pertencem à linguagem de regras do grupo"""
    pendentes = [formula]
    while pendentes:
        atual = pendentes.pop()
        if not isinstance(atual, (Variable, Constant, Not, And, Or, Implies)):
            raise ValueError(
                "Fórmula não suportada pelo motor:" + type(atual).__name__
            )
        if isinstance(atual, (And, Or)) and not atual.children:
            raise ValueError("Conjunções e disjunções precisam de operandos.")
        pendentes.extend(atual.children)


def _adicionar(ramo: Ramo, formulas: Iterable[FormulaMarcada]) -> None:
    for fm in formulas:
        if ramo.adicionar(fm):
            break


def _alternativas_distintas(
    alternativas: list[list[FormulaMarcada]],
) -> list[list[FormulaMarcada]]:
    vistos = set()
    distintas = []
    for alternativa in alternativas:
        chave = tuple((fm.sinal, fm.chave()) for fm in alternativa)
        if chave not in vistos:
            vistos.add(chave)
            distintas.append(alternativa)
    return distintas


def provar(
    premissas: Iterable[Proposition],
    conclusao: Proposition,
    estrategia: str | EscolhaBeta = 'combinada',
) -> Resultado:
    
    inicio = perf_counter()
    if isinstance(estrategia, str):
        try:
            escolher = ESTRATEGIAS[estrategia]
        except KeyError:
            raise ValueError(f"Estratégia desconhecida: {estrategia!r}") from None
    elif callable(estrategia):
        escolher = estrategia
    else:
        raise TypeError("A estratégia deve ser um nome ou uma função de escolha.")

    premissas = list(premissas)
    atomos = set()
    for formula in [*premissas, conclusao]:
        _validar_formula(formula)
        atomos.update(formula.variables())

    ramo = Ramo()
    pilha: list[tuple[list[FormulaMarcada], Estado]] = []
    regras: list[tuple[str, str]] = []
    ramos_fechados = 0

    def finalizar(valido, contraexemplo=None, livres=None):
        return Resultado(
            valido=valido,
            contraexemplo=contraexemplo,
            regras=regras,
            estatisticas={
                'expansoes': len(regras),
                'ramos_fechados': ramos_fechados,
                'tempo': perf_counter() - inicio,
                'atomos_livres': [] if livres is None else livres,
            },
        )

    def aplicar(i):
        fm = ramo.formulas[i]
        nome, alternativas = expandir(fm)
        ramo.marcar(i)
        regras.append((nome, str(fm)))
        return _alternativas_distintas(alternativas)

    iniciais = [FormulaMarcada(True, p) for p in premissas]
    iniciais.append(FormulaMarcada(False, conclusao))
    _adicionar(ramo, iniciais)

    while True:
        if ramo.fechado():
            ramos_fechados += 1
            if not pilha:
                return finalizar(True)
            alternativa, estado = pilha.pop()
            ramo.restaurar(estado)
            _adicionar(ramo, alternativa)
            continue

        while not ramo.fechado():
            alfas = ramo.pendentes_alfa()
            if not alfas:
                break
            alternativas = aplicar(alfas[0])
            _adicionar(ramo, alternativas[0])

        if ramo.fechado():
            continue

        betas = ramo.pendentes_beta()
        if not betas:
            valores = ramo.valoracao()
            livres = sorted(atomos - valores.keys())
            valores.update((atomo, False) for atomo in livres)
            if not (
                all(p.evaluate(**valores) for p in premissas)
                and not conclusao.evaluate(**valores)
            ):
                raise RuntimeError(
                    "Erro interno: o ramo aberto não produziu um contraexemplo válido."
                )
            return finalizar(False, valores, livres)

        i = escolher(ramo, betas)
        if type(i) is not int or i not in betas:
            raise ValueError("A estratégia deve retornar o índice de uma β pendente.")
        alternativas = aplicar(i)
        if len(alternativas) > 1:
            estado = ramo.estado()
            for alternativa in reversed(alternativas[1:]):
                pilha.append((alternativa, estado))
        _adicionar(ramo, alternativas[0])
