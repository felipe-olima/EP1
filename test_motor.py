"""Testes do motor independentes do parser, usando o oráculo da professora."""

import random
import unittest
from unittest.mock import patch

from code_base_EP1 import (
    And, ArgumentForm, Constant, Implies, Not, Or, Proposition, Variable,
)
from estrategias import ESTRATEGIAS
from motor import provar
from ramo import Ramo
from saida import formatar


class TestMotor(unittest.TestCase):
    def setUp(self):
        self.p, self.q, self.r, self.s = map(Variable, 'pqrs')

    def conferir(self, premissas, conclusao, estrategia, esperado=None):
        oraculo = ArgumentForm(
            *premissas, conclusion=conclusao
        ).is_valid_truth_table()
        if esperado is not None:
            self.assertEqual(oraculo, esperado)
        resultado = provar(premissas, conclusao, estrategia)
        self.assertIs(resultado.valido, oraculo)
        self.assertEqual(resultado.estatisticas['expansoes'], len(resultado.regras))
        self.assertGreaterEqual(resultado.estatisticas['tempo'], 0)
        for regra, formula in resultado.regras:
            self.assertIsInstance(regra, str)
            self.assertTrue(formula.startswith(('T ', 'F ')))
        if resultado.valido:
            self.assertIsNone(resultado.contraexemplo)
            self.assertGreaterEqual(resultado.estatisticas['ramos_fechados'], 1)
        else:
            valores = resultado.contraexemplo
            atomos = set(conclusao.variables())
            for premissa in premissas:
                atomos.update(premissa.variables())
                self.assertTrue(premissa.evaluate(**valores))
            self.assertEqual(set(valores), atomos)
            self.assertTrue(all(type(v) is bool for v in valores.values()))
            self.assertFalse(conclusao.evaluate(**valores))
        return resultado

    def test_sequentes_fixos_em_todas_as_estrategias(self):
        p, q, r, s = self.p, self.q, self.r, self.s
        a, b = map(Variable, 'ab')
        casos = [
            ('modus ponens', [p, Implies(p, q)], q, True),
            ('modus tollens', [Implies(p, q), Not(q)], Not(p), True),
            ('silogismo disjuntivo', [Or(p, q), Not(p)], q, True),
            ('silogismo hipotético', [Implies(p, q), Implies(q, r)],
             Implies(p, r), True),
            ('terceiro excluído', [], Or(p, Not(p)), True),
            ('contradição nas premissas', [p, Not(p)], q, True),
            ('exemplo do enunciado', [And(Implies(Or(a, b), q), Not(s)), a],
             q, True),
            ('constante verdadeira', [p], Constant(True), True),
            ('constante falsa', [Constant(False)], p, True),
            ('conjunção longa', [And(And(And(p, q), r), s)], s, True),
            ('non sequitur', [p], q, False),
            ('afirmar consequente', [Implies(p, q), q], p, False),
            ('negar antecedente', [Implies(p, q), Not(p)], Not(q), False),
            ('falácia do demo', [Or(p, q), p], Not(q), False),
            ('silogismo incorreto do demo', [Implies(p, q), Implies(q, r)],
             r, False),
            ('sem premissas inválido', [], p, False),
            ('só constantes válido', [], Constant(True), True),
            ('só constantes inválido', [], Constant(False), False),
            ('constante em disjunção', [Or(Constant(False), p)], p, True),
            ('constante em conjunção', [], And(Constant(True), p), False),
        ]
        equivalencias = [
            ('dupla negação', Not(Not(p)), p),
            ('De Morgan 1', Not(Or(p, q)), And(Not(p), Not(q))),
            ('De Morgan 2', Not(And(p, q)), Or(Not(p), Not(q))),
            ('distributividade de conjunção', And(p, Or(q, r)),
             Or(And(p, q), And(p, r))),
            ('distributividade de disjunção', Or(p, And(q, r)),
             And(Or(p, q), Or(p, r))),
            ('definição de implicação', Implies(p, q), Or(Not(p), q)),
        ]
        for nome, esquerda, direita in equivalencias:
            casos.append((nome, [esquerda], direita, True))
            casos.append((nome + ' (volta)', [direita], esquerda, True))
        for estrategia in ESTRATEGIAS:
            for nome, premissas, conclusao, esperado in casos:
                with self.subTest(estrategia=estrategia, sequente=nome):
                    self.conferir(premissas, conclusao, estrategia, esperado)

    def test_retorna_primeiro_ramo_aberto_apos_fechar_um_ramo(self):
        p, q, r = self.p, self.q, self.r
        resultado = self.conferir([Or(p, q), Not(p)], r, 'direta', False)
        self.assertEqual(resultado.estatisticas['ramos_fechados'], 1)
        self.assertEqual(resultado.contraexemplo, {'p': False, 'q': True, 'r': False})

    def test_restaura_bifurcacoes_aninhadas_e_preserva_historico(self):
        p, q, r, s = self.p, self.q, self.r, self.s
        resultado = self.conferir(
            [Or(p, q), Or(r, s), Implies(p, Not(r)), Implies(p, Not(s))],
            p, 'direta', False,
        )
        self.assertTrue(resultado.contraexemplo['q'])
        # O ramo p fecha imediatamente; o ramo q continua até saturar.
        self.assertEqual(resultado.regras[0][0], 'β∨')
        self.assertGreaterEqual(resultado.estatisticas['ramos_fechados'], 1)

        # Aqui a disjunção externa produz uma α diferente em cada alternativa.
        resultado = self.conferir(
            [Or(And(p, q), And(r, s)), Not(p), Not(r)],
            Variable('x'), 'direta', True,
        )
        self.assertEqual(
            [regra for regra, _ in resultado.regras],
            ['α¬', 'α¬', 'β∨', 'α∧', 'α∧'],
        )
        self.assertEqual(resultado.estatisticas['ramos_fechados'], 2)

    def test_retorna_da_bifurcacao_interna_antes_da_externa(self):
        p, q, r, s = self.p, self.q, self.r, self.s
        resultado = self.conferir(
            [Or(Or(p, q), r), Not(p), Not(q), Not(r)],
            s, 'direta', True,
        )
        # Todas as alternativas, inclusive r após os dois ramos internos, fecham.
        self.assertEqual(resultado.estatisticas['ramos_fechados'], 3)
        disjuncoes = [f for regra, f in resultado.regras if regra == 'β∨']
        self.assertEqual(disjuncoes, ['T (p v q) v r', 'T p v q'])

    def test_prioriza_alfas_inclusive_as_produzidas_por_beta(self):
        p, q, r, s = self.p, self.q, self.r, self.s
        chamadas = []

        def escolher(ramo, candidatos):
            self.assertEqual(ramo.pendentes_alfa(), [])
            chamadas.append(len(ramo.formulas))
            return candidatos[0]

        resultado = self.conferir(
            [Or(And(p, Not(Not(q))), r), Or(s, p)],
            Variable('x'), escolher, False,
        )
        self.assertGreaterEqual(len(chamadas), 2)
        nomes = [regra for regra, _ in resultado.regras]
        self.assertEqual(nomes[:3], ['β∨', 'α∧', 'α¬'])
        self.assertIn('β¬', nomes)
        self.assertTrue(resultado.contraexemplo['q'])

    def test_negacao_com_uma_alternativa_nao_empilha_estado(self):
        with patch.object(Ramo, 'estado', side_effect=AssertionError('Bifurcou')):
            resultado = self.conferir([], Not(self.p), 'direta', False)
        self.assertEqual(resultado.regras, [('β¬', 'F ¬p')])
        self.assertEqual(resultado.estatisticas['ramos_fechados'], 0)

    def test_alternativas_repetidas_nao_bifurcam(self):
        with patch.object(Ramo, 'estado', side_effect=AssertionError('Bifurcou')):
            resultado = self.conferir(
                [Or(Variable('p'), Variable('p'))], self.p, 'direta', True
            )
        self.assertEqual(resultado.estatisticas['ramos_fechados'], 1)

    def test_nao_compara_formulas_por_equivalencia_logica(self):
        with patch.object(
            Proposition, '__eq__', side_effect=AssertionError('Usou == em fórmula')
        ):
            resultado = provar(
                [Or(Or(self.p, Not(self.p)), Or(self.q, Not(self.q)))],
                Constant(False), 'direta',
            )
        self.assertFalse(resultado.valido)

    def test_conectivos_n_arios_exploram_inclusive_terceira_alternativa(self):
        p, q, r = self.p, self.q, self.r
        for estrategia in ESTRATEGIAS:
            with self.subTest(estrategia=estrategia):
                resultado = self.conferir(
                    [Or(p, q, r), Not(p), Not(q)],
                    Constant(False), estrategia, False,
                )
                self.assertTrue(resultado.contraexemplo['r'])
                self.assertEqual(resultado.estatisticas['ramos_fechados'], 2)
                self.conferir([Or(p, q, r)], Or(r, q, p), estrategia, True)
                self.conferir([And(p, q, r)], r, estrategia, True)
                resultado = self.conferir([p, q], And(p, q, r), estrategia, False)
                self.assertFalse(resultado.contraexemplo['r'])
                self.assertEqual(resultado.estatisticas['ramos_fechados'], 2)

    def test_completa_atomos_livres_e_integra_com_saida(self):
        p, q, r = self.p, self.q, self.r
        premissas = [Or(p, q)]
        resultado = self.conferir(premissas, r, 'direta', False)
        self.assertEqual(resultado.contraexemplo, {'p': True, 'q': False, 'r': False})
        self.assertEqual(resultado.estatisticas['atomos_livres'], ['q'])
        texto = formatar(premissas, r, resultado)
        self.assertIn('INVÁLIDO', texto)
        self.assertIn('q = F', texto)
        self.assertIn('Regras:', texto)

    def test_fechamento_inicial_nao_expande(self):
        for premissas, conclusao in [
            ([self.p], self.p),
            ([Constant(False)], self.q),
            ([], Constant(True)),
        ]:
            with self.subTest(conclusao=str(conclusao)):
                resultado = provar(premissas, conclusao)
                self.assertTrue(resultado.valido)
                self.assertEqual(resultado.regras, [])
                self.assertEqual(resultado.estatisticas['ramos_fechados'], 1)

    def test_interrompe_adicoes_assim_que_fecha(self):
        adicionadas = []
        adicionar_original = Ramo.adicionar

        def observar(ramo, fm):
            adicionadas.append(str(fm))
            return adicionar_original(ramo, fm)

        with patch.object(Ramo, 'adicionar', observar):
            resultado = provar([Not(self.p), And(self.p, self.q)], self.r)
        self.assertTrue(resultado.valido)
        self.assertNotIn('T q', adicionadas)

    def test_nome_desconhecido_e_escolha_invalida(self):
        with self.assertRaisesRegex(ValueError, 'desconhecida'):
            provar([], self.p, 'inexistente')
        with self.assertRaisesRegex(TypeError, 'estratégia'):
            provar([], self.p, 42)
        for indice in [-1, 999, True, '0']:
            with self.subTest(indice=indice):
                with self.assertRaisesRegex(ValueError, 'β pendente'):
                    provar([Or(self.p, self.q)], self.r,
                           lambda ramo, candidatos: indice)

    def test_recusa_formulas_fora_da_linguagem(self):
        for formula in [Proposition('p'), And(), Or()]:
            with self.subTest(formula=type(formula).__name__):
                with self.assertRaises(ValueError):
                    provar([], formula)

    def test_detecta_contraexemplo_inconsistente(self):
        with patch.object(Ramo, 'valoracao', return_value={'p': False}):
            with self.assertRaisesRegex(RuntimeError, 'contraexemplo válido'):
                provar([self.p], self.q)

    def test_chamadas_independentes_e_premissas_preservadas(self):
        premissas = [Or(self.p, self.q)]
        antes = str(premissas[0])
        primeiro = provar(premissas, self.r)
        segundo = provar(iter(premissas), self.r)
        self.assertEqual(len(premissas), 1)
        self.assertEqual(str(premissas[0]), antes)
        self.assertEqual(primeiro.contraexemplo, segundo.contraexemplo)
        self.assertEqual(primeiro.regras, segundo.regras)
        self.assertIsNot(primeiro.regras, segundo.regras)

    def test_500_sequentes_aleatorios_em_todas_as_estrategias(self):
        gerador = random.Random(239)

        def formula(atomos, profundidade):
            if profundidade == 0 or gerador.random() < 0.3:
                if gerador.random() < 0.15:
                    return Constant(gerador.choice([True, False]))
                return Variable(gerador.choice(atomos))
            conectivo = gerador.choice([Not, And, Or, Implies])
            if conectivo is Not:
                return Not(formula(atomos, profundidade - 1))
            return conectivo(
                formula(atomos, profundidade - 1),
                formula(atomos, profundidade - 1),
            )

        for numero in range(500):
            atomos = 'pqrst'[:gerador.randint(1, 5)]
            premissas = [formula(atomos, 4) for _ in range(gerador.randint(0, 3))]
            conclusao = formula(atomos, 4)
            for estrategia in ESTRATEGIAS:
                with self.subTest(sequente=numero, estrategia=estrategia):
                    self.conferir(premissas, conclusao, estrategia)


if __name__ == '__main__':
    unittest.main()
