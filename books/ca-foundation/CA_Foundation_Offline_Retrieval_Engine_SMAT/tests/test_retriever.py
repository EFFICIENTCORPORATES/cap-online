from pathlib import Path
import unittest
from ca_retrieval import RetrievalEngine, parse_natural_query, spec_from_preset

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data' / 'parsed_md'

class RetrievalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = RetrievalEngine(DATA)

    def test_corpus_loaded(self):
        self.assertEqual(len(self.engine.documents), 37)
        self.assertGreater(len(self.engine.blocks), 2000)

    def test_source_item_counts(self):
        s=self.engine.stats()['source_item_counts']
        self.assertEqual(s['examples'],53)
        self.assertEqual(s['illustrations'],235)
        self.assertEqual(s['illustration_solutions'],235)
        self.assertEqual(s['mcqs'],269)
        self.assertEqual(s['practical_questions'],79)
        self.assertEqual(s['true_false_statements'],307)

    def test_all_examples_are_source_items(self):
        blocks=self.engine.query(spec_from_preset('examples'))
        self.assertEqual(len(blocks),53)
        self.assertTrue(all(b.type=='example' and b.meta.get('source_verified_registry') for b in blocks))

    def test_previously_missed_example_units(self):
        cases=[
            ('Give me all Examples from Chapter 3',8),
            ('Give me all Examples from Chapter 11 Unit 4',5),
            ('Give me all Examples from Chapter 2 Unit 6',5),
            ('Give me all Examples from Chapter 1 Unit 1',1),
            ('Give me all Examples from Chapter 1 Unit 2',4),
        ]
        for q,n in cases:
            _,blocks=self.engine.query_text(q)
            self.assertEqual(len(blocks),n,q)

    def test_mcq_count(self):
        self.assertEqual(len(self.engine.query(spec_from_preset('mcq'))),269)

    def test_illustration_questions(self):
        self.assertEqual(len(self.engine.query(spec_from_preset('illustration_questions'))),235)

    def test_all_illustrations_have_solution(self):
        blocks=self.engine.query(spec_from_preset('illustrations'))
        self.assertEqual(sum(b.type=='illustration_question' for b in blocks),235)
        self.assertEqual(sum(b.type=='illustration_solution' for b in blocks),235)

    def test_brs_illustration_1_boundary(self):
        bs=[b for b in self.engine.blocks if b.source_pdf.endswith('BankReconciliationStatement.pdf') and str(b.number)=='1' and b.type in {'illustration_question','illustration_solution'}]
        q=next(b for b in bs if b.type=='illustration_question')
        s=next(b for b in bs if b.type=='illustration_solution')
        self.assertNotIn('It will be seen that whereas',q.content)
        self.assertNotIn('(x)    Errors:',q.content)
        self.assertIn('It will be seen that whereas',s.content)
        self.assertNotIn('(x)    Errors:',s.content)
        err=next(b for b in self.engine.blocks if b.id=='P01-M01-C03-UNA-SOURCE-ERRORS-001')
        self.assertIn('(x)    Errors:',err.content)

    def test_rectification_theory_shared_source_answer_relation(self):
        q=next(b for b in self.engine.blocks if b.id=='P01-M01-C02-U06-TYK-THEORY-QUESTION-3')
        self.assertEqual(q.pair_key,'tyk:theory:3')
        self.assertEqual(q.meta.get('answer_ref_pair_key'),'tyk:theory:2')
        spec=parse_natural_query('Give me theoretical questions from Chapter 2 Unit 6 with answers')
        blocks=self.engine.query(spec)
        q3pos=next(i for i,b in enumerate(blocks) if b.id==q.id)
        self.assertLess(q3pos+1,len(blocks))
        self.assertEqual(blocks[q3pos+1].id,'P01-M01-C02-U06-ANSWER-THEORY-2')

    def test_chapter_filter(self):
        spec=parse_natural_query('Give me all MCQs from Chapter 3')
        blocks=self.engine.query(spec)
        self.assertTrue(blocks)
        self.assertTrue(all(b.chapter==3 and b.type=='tyk_mcq_question' for b in blocks))

    def test_render_has_source(self):
        spec=parse_natural_query('Give me all Examples from Chapter 3')
        md=self.engine.compile(spec)
        self.assertIn('**Source:**',md)
        self.assertIn('PDF page',md)
        self.assertIn('Source items matched: 8',md)

    def test_validator(self):
        r=self.engine.validate()
        self.assertTrue(r['ok'])
        self.assertEqual(r['errors'],0)
        self.assertEqual(r['warnings'],0)

if __name__=='__main__': unittest.main()
