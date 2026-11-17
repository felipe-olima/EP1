"""Leitura de fórmulas e sequentes na linguagem do enunciado, sem eval."""

import re

from code_base_EP1 import And, Constant, Implies, Not, Or, Proposition, Variable


_TOKEN = re.compile(r'>>|True|False|[A-Za-z~∼¬&|()]')


class _Parser:
    def __init__(self, texto: str, deslocamento: int = 0):
        self.tokens = []
        posicao = 0
        while posicao < len(texto):
            if texto[posicao].isspace():
                posicao += 1
                continue
            token = _TOKEN.match(texto, posicao)
            if token is None:
                raise ValueError(
                    f"Símbolo inválido {texto[posicao]!r} "
                    f"na posição {deslocamento + posicao + 1}."
                )
            self.tokens.append((token.group(), deslocamento + posicao))
            posicao = token.end()
        self.tokens.append(('', deslocamento + len(texto)))
        self.indice = 0

    def _atual(self) -> str:
        return self.tokens[self.indice][0]

    def _aceitar(self, token: str) -> bool:
        if self._atual() == token:
            self.indice += 1
            return True
        return False

    def _erro(self, mensagem: str) -> ValueError:
        return ValueError(
            f"{mensagem} na posição {self.tokens[self.indice][1] + 1}."
        )

    def analisar(self) -> Proposition:
        formula = self._implicacao()
        if self._atual():
            raise self._erro(f"Token inesperado {self._atual()!r}")
        return formula

    def _implicacao(self) -> Proposition:
        esquerda = self._disjuncao()
        if self._aceitar('>>'):
            # A recursão à direita lê p >> q >> r como p >> (q >> r).
            return Implies(esquerda, self._implicacao())
        return esquerda

    def _disjuncao(self) -> Proposition:
        formula = self._conjuncao()
        while self._aceitar('|'):
            formula = Or(formula, self._conjuncao())
        return formula

    def _conjuncao(self) -> Proposition:
        formula = self._unario()
        while self._aceitar('&'):
            formula = And(formula, self._unario())
        return formula

    def _unario(self) -> Proposition:
        token = self._atual()
        if token in ('~', '∼', '¬'):
            self.indice += 1
            return Not(self._unario())
        if self._aceitar('('):
            formula = self._implicacao()
            if not self._aceitar(')'):
                raise self._erro("Esperado ')'")
            return formula
        if token in ('T', 'True', 'F', 'False'):
            self.indice += 1
            return Constant(token in ('T', 'True'))
        if len(token) == 1 and token.isalpha():
            self.indice += 1
            return Variable(token)
        raise self._erro("Esperada uma fórmula: átomo, constante, negação ou '('")


def parse_formula(texto: str) -> Proposition:
    """Lê uma fórmula: negação > & > | > >>; posições de erro começam em 1."""
    return _Parser(texto).analisar()


def parse_sequente(texto: str) -> tuple[list[Proposition], Proposition]:
    """Lê premissas separadas por vírgula e uma conclusão após |- ou ⊢."""
    separadores = list(re.finditer(r'\|-|⊢', texto))
    if not separadores:
        raise ValueError("Sequente sem separador: use '|-' ou '⊢'.")
    if len(separadores) != 1:
        raise ValueError(
            f"Separador de sequente repetido na posição {separadores[1].start() + 1}."
        )
    separador = separadores[0]
    esquerda = texto[:separador.start()]
    direita = texto[separador.end():]
    premissas = []
    if esquerda.strip():
        deslocamento = 0
        for parte in esquerda.split(','):
            premissas.append(_Parser(parte, deslocamento).analisar())
            deslocamento += len(parte) + 1
    conclusao = _Parser(direita, separador.end()).analisar()
    return premissas, conclusao


def ler_arquivo(caminho: str) -> list[tuple[list[Proposition], Proposition]]:
    """Lê um sequente por linha, ignorando linhas vazias e comentários com #."""
    sequentes = []
    with open(caminho, encoding='utf-8') as arquivo:
        for numero, linha in enumerate(arquivo, start=1):
            if not linha.strip() or linha.lstrip().startswith('#'):
                continue
            try:
                sequentes.append(parse_sequente(linha))
            except ValueError as erro:
                raise ValueError(f"{caminho}: linha {numero}: {erro}") from erro
    return sequentes
