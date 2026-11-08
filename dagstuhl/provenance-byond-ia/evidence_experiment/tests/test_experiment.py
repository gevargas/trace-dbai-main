import copy
import random
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from experiment import generate, evaluate, oracle, revisions, update, validate, METHODS

class EvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.cases=generate()

    def test_fixture_count_and_graph_sizes(self):
        self.assertEqual(len(self.cases),120)
        self.assertGreater(len({len(c['graph']['nodes']) for c in self.cases}),2)

    def test_typed_against_independent_completion_oracle(self):
        for c in self.cases:
            with self.subTest(case=c['graph']['id']):
                out=evaluate(c['graph']);expected=oracle(c['completions'])
                self.assertEqual(out['independence'],expected['independence'])
                self.assertEqual({k:v['status'] for k,v in out['claims'].items()},expected['statuses'])

    def test_baselines_fail_on_distinct_failure_modes(self):
        by={c['graph']['condition']:c['graph'] for c in self.cases}
        self.assertEqual(evaluate(by['repeated'],'citation_count')['independence'],'established')
        self.assertEqual(evaluate(by['shared_tool'],'untyped_ancestry')['independence'],'dependent')
        self.assertEqual(evaluate(by['shared_tool'])['independence'],'established')
        self.assertEqual(evaluate(by['hidden'],'without_coverage')['independence'],'established')
        self.assertEqual(evaluate(by['hidden'])['independence'],'undetermined')

    def test_ungrounded_cycle_and_nonexplosive_conflict(self):
        for c in self.cases:
            g=c['graph'];r=evaluate(g)
            if g['condition']=='circular':
                self.assertEqual(r['claims']['c']['status'],'undetermined')
            if g['condition']=='conflict':
                self.assertEqual(r['claims']['c']['status'],'conflicting')
                self.assertEqual(r['claims']['u']['status'],'supported')

    def test_all_revision_equivalences_and_unrelated_preservation(self):
        for c in self.cases:
            for r in revisions(c['graph']):
                self.assertTrue(r['equal_to_full'],(c['graph']['id'],r['operation']))
                self.assertTrue(r['preserved_unrelated'])

    def test_permission_withdrawal_is_purpose_specific(self):
        g=next(c['graph'] for c in self.cases if c['graph']['condition']=='repeated')
        h,_=update(g,'withdraw_public_permission')
        self.assertEqual(evaluate(h,purpose='research')['claims']['c']['status'],'supported')
        pub=evaluate(h,purpose='public')['claims']['c']
        self.assertEqual(pub['status'],'undetermined')
        self.assertEqual(pub['coverage'],'incomplete')
        self.assertEqual(pub['challenge_origins'],[])
        self.assertNotIn('o1',pub['support_origins'])

    def test_retraction_with_alternative_support(self):
        g=next(c['graph'] for c in self.cases if c['graph']['condition']=='independent')
        h,_=update(g,'retract_observation')
        r=evaluate(h)['claims']['c']
        self.assertEqual(r['status'],'supported')
        self.assertEqual(r['support_origins'],['o2'])

    def test_oracle_metadata_cannot_affect_engine(self):
        for c in self.cases[:6]:
            g=c['graph'];h=copy.deepcopy(g);h['condition']='fabricated';h['template']=-999
            h['oracle']={'answer':'arbitrary'}
            self.assertEqual(evaluate(g),evaluate(h))

    def test_permutation_and_identifier_invariance(self):
        rng=random.Random(23)
        for c in self.cases[:6]:
            g=c['graph'];h=copy.deepcopy(g)
            rename={n['id']:'random_'+str(i) for i,n in enumerate(h['nodes'])}
            for n in h['nodes']:n['id']=rename[n['id']]
            for e in h['edges']:e['src']=rename[e['src']];e['dst']=rename[e['dst']]
            h['pair']=[rename[x] for x in h['pair']];h['incomplete']=[rename[x] for x in h['incomplete']]
            h['focus']=rename[h['focus']];rng.shuffle(h['nodes']);rng.shuffle(h['edges'])
            a,b=evaluate(g),evaluate(h)
            self.assertEqual(a['independence'],b['independence'])
            self.assertEqual(a['claims']['c']['status'],b['claims'][rename['c']]['status'])

    def test_unaccepted_annotation_cannot_ground_claim(self):
        g=copy.deepcopy(self.cases[0]['graph'])
        for e in g['edges']:
            if e['kind']=='supports' and e['dst']=='c':e['accepted']=False
        self.assertEqual(evaluate(g)['claims']['c']['status'],'undetermined')

    def test_witness_edges_are_admissible_and_origin_reachable(self):
        # Independent per-origin reachability on reversed derivation / forward support.
        for c in self.cases:
            g=c['graph'];r=evaluate(g);known={e['id'] for e in g['edges']}
            adjacency={n['id']:set() for n in g['nodes']}
            for e in g['edges']:
                if e['kind']=='supports':adjacency[e['src']].add(e['dst'])
                if e['kind']=='derivedFrom':adjacency[e['dst']].add(e['src'])
            for claim,w in r['claims'].items():
                self.assertTrue(set(w['witness_edges'])<=known)
                for origin in w['support_origins']:
                    seen=set();todo=[origin]
                    while todo:
                        x=todo.pop()
                        if x in seen:continue
                        seen.add(x);todo.extend(adjacency[x]-seen)
                    self.assertIn(claim,seen)

    def test_validation_rejects_dangling_edges(self):
        h=copy.deepcopy(self.cases[0]['graph']);h['edges'][0]['dst']='missing'
        with self.assertRaises(ValueError):validate(h)

    def test_random_graphs_against_path_oracle(self):
        from experiment import node,edge
        rng=random.Random(195)
        for k in range(60):
            ns=[node('o1','observation'),node('o2','observation')]+[node(f'c{i}','claim') for i in range(7)]
            es=[]
            for i in range(19):
                a=rng.choice(ns)['id'];b=rng.choice(ns[2:])['id']
                es.append(edge(f'e{i}',a,b,rng.choice(['supports','challenges'])))
            g=dict(nodes=ns,edges=es,pair=['c0','c1'],focus='c0',incomplete=[])
            out=evaluate(g);expected=oracle([g])
            self.assertEqual(out['independence'],expected['independence'])
            self.assertEqual({i:r['status'] for i,r in out['claims'].items()},expected['statuses'])

if __name__=='__main__':unittest.main()
