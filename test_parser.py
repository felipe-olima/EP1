"""Testes de leitura e integração parser -> motor -> saída."""

from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest

from code_base_EP1 import And, ArgumentForm, Constant, Implies, Not, Or, Variable
from estrategias import ESTRATEGIAS
from motor import provar
from parser import ler_arquivo, parse_formula, parse_sequente
from saida import para_linguagem


class TestParser(unittest.TestCase):
    def setUp(self):
        self.p, self.q, self.r, self.s = map(Variable, 'pqrs')

    def conferir_formula(self, texto, esperada):
        recebida = parse_formula(texto)
        self.assertTrue(recebida.is_identical(esperada), texto)
        return recebida

    def test_atomos_e_constantes(self):
        for texto in ('p', 'Q', 'a', 'z'):
            self.conferir_formula(texto, Variable(texto))
        for texto, valor in [('T', True), ('True', True), ('F', False), ('False', False)]:
            self.conferir_formula(texto, Constant(valor))

    def test_tres_simbolos_de_negacao(self):
        for simbolo in ('~', '∼', '¬'):
            self.conferir_formula(simbolo + 'p', Not(self.p))
            self.conferir_formula(simbolo * 2 + 'p', Not(Not(self.p)))

    def test_precedencia(self):
        p, q, r, s = self.p, self.q, self.r, self.s
        self.conferir_formula('~p & q | r >> s', Implies(Or(And(Not(p), q), r), s))
        self.conferir_formula('p >> q & r', Implies(p, And(q, r)))

    def test_implicacao_associa_a_direita(self):
        p, q, r = self.p, self.q, self.r
        self.conferir_formula('p >> q >> r', Implies(p, Implies(q, r)))
        self.conferir_formula('(p >> q) >> r', Implies(Implies(p, q), r))

    def test_conjuncoes_e_disjuncoes_criam_nos_binarios(self):
        p, q, r = self.p, self.q, self.r
        self.conferir_formula('p & q & r', And(And(p, q), r))
        self.conferir_formula('p | q | r', Or(Or(p, q), r))

    def test_parenteses_e_espacos(self):
        self.conferir_formula(' \t p & (q | r)\n', And(self.p, Or(self.q, self.r)))
        self.conferir_formula('(((p)))', self.p)

    def test_formulas_invalidas(self):
        for texto in ('', ' ', 'pq', 'p > q', 'p && q', 'p |', '(p', 'p)',
                      'p q', '1', 'p <=> q', '~', 'p & & q', 'true',
                      "__import__('os')"):
            with self.subTest(texto=texto):
                with self.assertRaisesRegex(ValueError, 'posição'):
                    parse_formula(texto)

    def test_erro_indica_posicao(self):
        for texto, posicao in [('p & @', 5), ('(p | q', 7), ('p q', 3)]:
            with self.subTest(texto=texto):
                with self.assertRaisesRegex(ValueError, f'posição {posicao}\\.'):
                    parse_formula(texto)
        with self.assertRaisesRegex(ValueError, 'posição 13\\.'):
            parse_sequente('p, q |- r & @')

    def test_dois_separadores_de_sequente(self):
        for separador in ('|-', '⊢'):
            resultado = parse_sequente(f'p, p >> q {separador} q')
            self.assertIs(type(resultado), tuple)
            premissas, conclusao = resultado
            self.assertEqual(len(premissas), 2)
            self.assertTrue(premissas[0].is_identical(self.p))
            self.assertTrue(premissas[1].is_identical(Implies(self.p, self.q)))
            self.assertTrue(conclusao.is_identical(self.q))

    def test_sequente_sem_premissas(self):
        for texto in ('|- p | ~p', '  ⊢ p | ~p'):
            premissas, conclusao = parse_sequente(texto)
            self.assertEqual(premissas, [])
            self.assertTrue(conclusao.is_identical(Or(self.p, Not(self.p))))

    def test_sequentes_invalidos(self):
        for texto in ('p', 'p |- q |- r', 'p ⊢ q |- r', 'p |-',
                      'p, |- q', ',p |- q', 'p,,q |- r'):
            with self.subTest(texto=texto):
                with self.assertRaises(ValueError):
                    parse_sequente(texto)

    def test_arquivo_ignora_comentarios_e_linhas_vazias(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / 'sequentes.txt'
            caminho.write_text('# comentário\n\n p,p>>q|-q\n  # outro\n|-p|~p\n',
                               encoding='utf-8')
            sequentes = ler_arquivo(caminho)
        self.assertEqual(len(sequentes), 2)
        self.assertTrue(all(provar(p, c).valido for p, c in sequentes))

    def test_erro_de_arquivo_indica_linha(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / 'sequentes.txt'
            caminho.write_text('# comentário\n\np|-q\np|-@\n', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'linha 4:.*posição 4'):
                ler_arquivo(caminho)

    def test_sequentes_lidos_integram_com_todas_as_estrategias(self):
        casos = [
            ('p, p >> q |- q', True),
            ('p >> q, ~q |- ~p', True),
            ('p | q, ~p |- q', True),
            ('p >> q, q >> r |- p >> r', True),
            ('|- p | ~p', True),
            ('~~p |- p', True),
            ('~(p | q) |- ~p & ~q', True),
            ('p & (q | r) |- (p & q) | (p & r)', True),
            ('((a | b) >> q) & (∼s), a |- q', True),
            ('p |- T', True),
            ('F |- p', True),
            ('p |- q', False),
            ('p >> q, q |- p', False),
            ('p >> q, q >> r |- r', False),
            ('|- False', False),
        ]
        for texto, esperado in casos:
            premissas, conclusao = parse_sequente(texto)
            oraculo = ArgumentForm(*premissas, conclusion=conclusao).is_valid_truth_table()
            self.assertEqual(oraculo, esperado)
            for estrategia in ESTRATEGIAS:
                with self.subTest(texto=texto, estrategia=estrategia):
                    resultado = provar(premissas, conclusao, estrategia)
                    self.assertEqual(resultado.valido, esperado)
                    if not resultado.valido:
                        self.assertTrue(all(p.evaluate(**resultado.contraexemplo)
                                            for p in premissas))
                        self.assertFalse(conclusao.evaluate(**resultado.contraexemplo))

    def test_impressao_e_leitura_preservam_150_arvores_aleatorias(self):
        gerador = random.Random(239)

        def gerar(profundidade):
            if profundidade == 0 or gerador.random() < 0.3:
                return gerador.choice([Variable('p'), Variable('q'), Constant(True), Constant(False)])
            conectivo = gerador.choice([Not, And, Or, Implies])
            if conectivo is Not:
                return Not(gerar(profundidade - 1))
            return conectivo(gerar(profundidade - 1), gerar(profundidade - 1))

        for _ in range(150):
            formula = gerar(4)
            self.conferir_formula(para_linguagem(formula), formula)

    def test_script_de_terminal_com_argumentos_e_arquivo(self):
        def executar(*argumentos):
            return subprocess.run(
                [sys.executable, '-B', 'usar_tableaux.py', *argumentos],
                cwd=Path(__file__).resolve().parent,
                capture_output=True, text=True, check=True,
            ).stdout

        self.assertIn('Resultado: VÁLIDO', executar('p, p >> q |- q'))
        self.assertIn('Resultado: INVÁLIDO', executar('p |- q'))
        self.assertIn('p >> (q & r)', executar('p >> q & r'))
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / 'sequentes.txt'
            caminho.write_text('# testes\np,p>>q|-q\np|-q\n', encoding='utf-8')
            saida = executar('--arquivo', str(caminho), '--estrategia', 'menor')
        self.assertIn('Resultado: VÁLIDO', saida)
        self.assertIn('Resultado: INVÁLIDO', saida)
        self.assertNotIn('ERRO', saida)


if __name__ == '__main__':
    unittest.main()
