#!/usr/bin/env python3
"""Evidence provenance pilot. Python 3.9+, standard library only.

Frozen policy: observational origins are provisional positive grounds;
supports and recorded derivation propagate positive grounds; an explicitly
challenging, positively grounded source gives negative evidence. Negative
evidence does not propagate through support in this deliberately small fragment.
"""
from __future__ import annotations
import argparse
import copy
import csv
import hashlib
import json
import platform
import random
import sqlite3
import statistics
import sys
import time
from collections import defaultdict, deque
from itertools import product
from pathlib import Path

VERSION = '1.0.0'
CONDITIONS = ('independent', 'repeated', 'circular', 'shared_tool', 'hidden', 'conflict')
METHODS = ('citation_count', 'untyped_ancestry', 'typed', 'without_types', 'without_coverage')
EVIDENTIAL = {'derivedFrom', 'supports'}
STATUSES = ('supported', 'refuted', 'undetermined', 'conflicting')
SCHEMA = '''
CREATE TABLE IF NOT EXISTS cases (id TEXT PRIMARY KEY, template INTEGER, condition TEXT, payload TEXT);
CREATE TABLE IF NOT EXISTS nodes (case_id TEXT, id TEXT, kind TEXT, payload TEXT, PRIMARY KEY(case_id,id));
CREATE TABLE IF NOT EXISTS edges (case_id TEXT, id TEXT, src TEXT, dst TEXT, kind TEXT, mode TEXT, payload TEXT, PRIMARY KEY(case_id,id));
CREATE TABLE IF NOT EXISTS assessments (case_id TEXT, method TEXT, snapshot TEXT, payload TEXT);
CREATE INDEX IF NOT EXISTS edge_dst ON edges(case_id,dst);
CREATE INDEX IF NOT EXISTS edge_src ON edges(case_id,src);
'''

def dump(path, value):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def node(i, kind, label=None, **kw):
    return dict(id=i, kind=kind, label=label or i, active=True, purposes=['research', 'public'], **kw)

def edge(i, src, dst, kind, **kw):
    return dict(id=i, src=src, dst=dst, kind=kind, mode='observed', accepted=True,
                active=True, purposes=['research', 'public'], **kw)

def validate(g):
    ids = [n['id'] for n in g['nodes']]
    if len(ids) != len(set(ids)): raise ValueError('Duplicate node identifier')
    eid = [e['id'] for e in g['edges']]
    if len(eid) != len(set(eid)): raise ValueError('Duplicate edge identifier')
    for n in g['nodes']:
        if n['kind'] not in {'observation','document','claim','tool'}:
            raise ValueError('Unknown node type: ' + n['kind'])
    for e in g['edges']:
        if e['src'] not in ids or e['dst'] not in ids: raise ValueError('Dangling edge ' + e['id'])
        if e['kind'] not in {'derivedFrom','supports','challenges','processedWith'}:
            raise ValueError('Unknown relation type')
        if e['mode'] not in {'observed','declared','inferred'}: raise ValueError('Unknown acquisition mode')
    for i in g.get('incomplete', []):
        if i not in ids: raise ValueError('Unknown coverage boundary')
    if any(i not in ids for i in g['pair']): raise ValueError('Unknown pair member')

def generate(templates=20, seed=20261107):
    """Paired templates vary copy depth, branch width, and distractor topology."""
    rng = random.Random(seed)
    cases = []
    for t in range(templates):
        depth = 1 + t % 3
        branches = 1 + (t // 3) % 3
        for cond in CONDITIONS:
            ns = [node('c','claim','Synthetic claim about a ritual event'),
                  node('d','claim','Downstream catalogue description'),
                  node('o1','observation','Synthetic observation A'),
                  node('s1','document','Source account A'),
                  node('s2','document','Source account B'),
                  node('u','claim','Unrelated documented claim'),
                  node('ou','observation','Unrelated observation')]
            es = [edge('s1c','s1','c','supports'),edge('s2c','s2','c','supports'),
                  edge('cd','c','d','supports'),edge('ouu','ou','u','supports')]
            def chain(leaf, root, name):
                prev = leaf
                for k in range(depth):
                    mid = f'{name}{k}'
                    ns.append(node(mid,'document',f'Synthetic intermediate {name} {k+1}'))
                    es.append(edge(f'{name}e{k}',prev,mid,'derivedFrom')); prev = mid
                es.append(edge(name+'root',prev,root,'derivedFrom'))
            incomplete, hidden_edges = [], []
            if cond == 'circular':
                es += [edge('cy1','s1','s2','supports'),edge('cy2','s2','s1','supports')]
                # The disconnected observation is deliberately not evidence for c.
            else:
                chain('s1','o1','a')
                if cond in {'independent','shared_tool','conflict','hidden'}:
                    ns.append(node('o2','observation','Synthetic observation B'))
                    chain('s2','o2','b')
                else:
                    chain('s2','s1','b')
                if cond == 'hidden':
                    hidden_edges = [edge('hidden_copy','s2','s1','derivedFrom')]
                    incomplete = ['s2']
                if cond == 'shared_tool':
                    ns.append(node('tool','tool','Shared analysis tool'))
                    es += [edge('tool1','s1','tool','processedWith'),edge('tool2','s2','tool','processedWith')]
                if cond == 'conflict':
                    ns += [node('ox','observation','Synthetic challenging observation'),node('sx','document','Challenging account')]
                    es += [edge('xroot','sx','ox','derivedFrom'),edge('xc','sx','c','challenges')]
            for k in range(branches):
                i = f'n{k}'; ns.append(node(i,'document',f'Unrelated catalogue item {k+1}'))
                es.append(edge(f'noise{k}',i,'ou','derivedFrom'))
            # Vary insertion order without making iteration order part of semantics.
            rng.shuffle(ns); rng.shuffle(es)
            g = dict(id=f't{t:02d}_{cond}', template=t, condition=cond,
                     domain='synthetic cultural repository', synthetic=True, nodes=ns, edges=es,
                     focus='c', pair=['s1','s2'], incomplete=incomplete, snapshot='v0')
            validate(g)
            complete = copy.deepcopy(g)
            complete['edges'] += hidden_edges; complete['incomplete'] = []
            # The engine never receives latent truth or oracle completions.
            oracle_completions = [copy.deepcopy(g)]
            oracle_completions[0]['incomplete'] = []
            if hidden_edges:
                alternative = copy.deepcopy(complete)
                oracle_completions.append(alternative)
            cases.append(dict(graph=g, latent=complete, completions=oracle_completions))
    return cases

def view(g, purpose='research'):
    h = copy.deepcopy(g)
    visible = {n['id'] for n in h['nodes'] if n.get('active',True) and purpose in n.get('purposes',[])}
    h['nodes'] = [n for n in h['nodes'] if n['id'] in visible]
    h['edges'] = [e for e in h['edges'] if e.get('active',True) and e.get('accepted',True)
                  and purpose in e.get('purposes',[]) and e['src'] in visible and e['dst'] in visible]
    # This prototype authorises disclosure of the existence of a gap, but no protected content.
    affected = {e['src'] if e['kind'] == 'derivedFrom' else e['dst'] for e in g['edges']
                if e.get('active',True) and purpose not in e.get('purposes',[])}
    for e in g['edges']:
        if e.get('active',True) and ((e['src'] not in visible) != (e['dst'] not in visible)):
            affected.add(e['src'] if e['src'] in visible else e['dst'])
    h['incomplete'] = sorted((set(g.get('incomplete',[])) | affected) & visible)
    return h

def dependencies(g, untyped=False):
    """Return evidence parent -> dependent; computational-tool edges are optional."""
    pairs = []
    for e in g['edges']:
        if e['kind'] == 'derivedFrom' or (untyped and e['kind'] == 'processedWith'):
            pairs.append((e['dst'],e['src'],e['id']))
        elif e['kind'] == 'supports': pairs.append((e['src'],e['dst'],e['id']))
    return pairs

def fixed_point(g, untyped=False):
    grounds = {n['id']:{n['id']} if n['kind']=='observation' else set() for n in g['nodes']}
    pairs = dependencies(g, untyped)
    changed = True
    while changed:
        changed = False
        for parent, child, _ in pairs:
            delta = grounds[parent] - grounds[child]
            if delta: grounds[child].update(delta); changed = True
    return grounds

def ancestors(g, start, untyped=False):
    parents = defaultdict(set)
    for a,b,_ in dependencies(g, untyped): parents[b].add(a)
    seen, todo = set(), [start]
    while todo:
        x = todo.pop()
        if x in seen: continue
        seen.add(x); todo.extend(parents[x] - seen)
    return seen

def classify(t,f):
    return 'conflicting' if t and f else 'supported' if t else 'refuted' if f else 'undetermined'

def evaluate(g, method='typed', purpose='research', selected=None):
    """No oracle metadata or condition labels are read by this evaluator."""
    h = view(g,purpose); ns = {n['id']:n for n in h['nodes']}
    untyped = method in {'untyped_ancestry','without_types'}
    roots = fixed_point(h)
    rows = {}
    for n in h['nodes']:
        if n['kind'] != 'claim' or (selected is not None and n['id'] not in selected): continue
        i=n['id']; incoming=[e for e in h['edges'] if e['dst']==i]
        plus = sorted(roots[i])
        minus = sorted({r for e in incoming if e['kind']=='challenges' for r in roots[e['src']]})
        if method == 'citation_count':
            t=any(e['kind']=='supports' for e in incoming)
            f=any(e['kind']=='challenges' for e in incoming)
        else: t,f=bool(plus),bool(minus)
        relevant = ancestors(h,i)
        relevant |= {a for e in incoming if e['kind']=='challenges' for a in ancestors(h,e['src'])}
        gaps = sorted(relevant & set(h['incomplete']))
        witness=[]
        for e in h['edges']:
            if e['src'] not in relevant or e['dst'] not in relevant:continue
            parent=e['dst'] if e['kind']=='derivedFrom' else e['src']
            if e['kind'] in EVIDENTIAL | {'challenges'} and roots[parent]:witness.append(e['id'])
        rows[i]=dict(status=classify(t,f),support_origins=plus,challenge_origins=minus,
                     coverage='incomplete' if gaps else 'complete',gaps=gaps,
                     witness_edges=sorted(witness))
    a,b = h['pair']
    if a not in ns or b not in ns:
        independence='undetermined'; shared=[]
    elif method=='citation_count': independence='established' if a!=b else 'dependent'; shared=[]
    else:
        aa,bb=ancestors(h,a,untyped),ancestors(h,b,untyped)
        shared=sorted((aa & bb) if untyped else (roots[a] & roots[b]))
        gap=bool((aa|bb) & set(h['incomplete'])) and method!='without_coverage'
        if shared: independence='dependent'
        elif gap or not roots[a] or not roots[b]: independence='undetermined'
        else: independence='established'
    return dict(claims=rows,independence=independence,shared=shared,
                policy='observational-origins-v1',purpose=purpose,snapshot=g.get('snapshot','v0'))

def oracle(worlds, purpose='research'):
    """Independent exhaustive simple-path implementation for small finite worlds.

    No production fixed-point, ancestor, or evaluate functions are called.
    Completion worlds are declared by the benchmark, never inferred by the engine.
    """
    answers=[]
    for world in worlds:
        ns={n['id']:n for n in world['nodes'] if n.get('active',True) and purpose in n['purposes']}
        es=[e for e in world['edges'] if e.get('active',True) and e.get('accepted',True)
            and purpose in e['purposes'] and e['src'] in ns and e['dst'] in ns]
        backward=defaultdict(list)
        for e in es:
            if e['kind']=='derivedFrom': backward[e['src']].append(e['dst'])
            if e['kind']=='supports': backward[e['dst']].append(e['src'])
        def walks(x,seen):
            if x in seen:return set()
            result={x} if ns[x]['kind']=='observation' else set()
            for y in backward[x]:result |= walks(y,seen|{x})
            return result
        rr={x:walks(x,set()) for x in ns}
        states={}
        for x,n in ns.items():
            if n['kind']=='claim':
                pos=bool(rr[x]); neg=any(rr[e['src']] for e in es if e['kind']=='challenges' and e['dst']==x)
                states[x]=('conflicting' if pos and neg else 'supported' if pos else 'refuted' if neg else 'undetermined')
        a,b=world['pair']; ar,br=rr.get(a,set()),rr.get(b,set())
        ind='dependent' if ar&br else 'established' if ar and br else 'undetermined'
        answers.append(dict(statuses=states,independence=ind,
                            support_origins={x:sorted(rr[x]) for x in states},
                            challenge_origins={x:sorted({r for e in es if e['kind']=='challenges' and e['dst']==x for r in rr[e['src']]}) for x in states}))
    # A completion disagreement is a legitimate unknown, not an engine error.
    inds={a['independence'] for a in answers}
    claims={i:(next(iter(v)) if len(v:= {a['statuses'][i] for a in answers})==1 else 'undetermined')
            for i in answers[0]['statuses']}
    return dict(statuses=claims,independence=next(iter(inds)) if len(inds)==1 else 'undetermined',
                support_origins={x:sorted({r for a in answers for r in a['support_origins'][x]}) for x in claims},
                challenge_origins={x:sorted({r for a in answers for r in a['challenge_origins'][x]}) for x in claims})

def update(g, operation):
    h=copy.deepcopy(g); touched=set()
    if operation=='retract_observation':
        for n in h['nodes']:
            if n['id']=='o1':n['active']=False;touched.add('o1')
    elif operation=='add_challenge':
        h['nodes'].append(node('new_o','observation','New synthetic counter-observation'))
        h['edges'].append(edge('new_attack','new_o',h['focus'],'challenges'));touched|={'new_o',h['focus']}
    elif operation=='withdraw_public_permission':
        for n in h['nodes']:
            if n['id']=='o1':n['purposes']=['research'];touched.add('o1')
    else:raise ValueError('Unknown operation')
    h['snapshot']=operation
    return h,touched

def impacted(g, touched):
    downstream=defaultdict(set)
    for a,b,_ in dependencies(g):downstream[a].add(b)
    for e in g['edges']:
        if e['kind']=='challenges':downstream[e['src']].add(e['dst'])
    seen=set(touched); todo=list(touched)
    while todo:
        for x in downstream[todo.pop()] - seen:seen.add(x);todo.append(x)
    return seen

def revisions(g):
    """Invalidate affected claim assessments; recompute roots globally (no speed claim)."""
    rows=[]
    for operation,purpose in [('retract_observation','research'),('add_challenge','research'),
                              ('withdraw_public_permission','public')]:
        base=evaluate(g,purpose=purpose)
        new,touched=update(g,operation)
        affected=impacted(g,touched)|impacted(new,touched)
        start=time.perf_counter_ns()
        delta=evaluate(new,purpose=purpose,selected=affected)
        merged=copy.deepcopy(base);merged['claims'].update(delta['claims'])
        merged.update({k:v for k,v in delta.items() if k!='claims'})
        incremental_ns=time.perf_counter_ns()-start
        start=time.perf_counter_ns(); full=evaluate(new,purpose=purpose); full_ns=time.perf_counter_ns()-start
        rows.append(dict(case_id=g['id'],operation=operation,purpose=purpose,
                         affected_claims=sorted(set(base['claims'])&affected),
                         equal_to_full=merged==full,
                         preserved_unrelated=base['claims']['u']==full['claims']['u'],
                         incremental_ns=incremental_ns,full_ns=full_ns,
                         before=base,after=full,graph=new))
    return rows

def write_csv(path, rows):
    if not rows:return
    with Path(path).open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def run(out, templates=20, seed=20261107, repeats=5):
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    cases=generate(templates,seed);predictions=[];details=[];updates=[]
    db=sqlite3.connect(out/'evidence.sqlite');db.executescript(SCHEMA)
    for table in ('cases','nodes','edges','assessments'):db.execute('DELETE FROM '+table)
    for case in cases:
        g=case['graph'];gold=oracle(case['completions']);latent=oracle([case['latent']]);visible=oracle([g])
        dump(out/'dataset'/(g['id']+'.json'),g)
        dump(out/'oracle'/(g['id']+'.json'),dict(expected=gold,latent=latent,completions=case['completions']))
        db.execute('INSERT INTO cases VALUES (?,?,?,?)',(g['id'],g['template'],g['condition'],json.dumps(g)))
        db.executemany('INSERT INTO nodes VALUES (?,?,?,?)',[(g['id'],n['id'],n['kind'],json.dumps(n)) for n in g['nodes']])
        db.executemany('INSERT INTO edges VALUES (?,?,?,?,?,?,?)',[(g['id'],e['id'],e['src'],e['dst'],e['kind'],e['mode'],json.dumps(e)) for e in g['edges']])
        method_details={}
        for method in METHODS:
            timings=[]
            for _ in range(repeats):
                start=time.perf_counter_ns();result=evaluate(g,method);timings.append(time.perf_counter_ns()-start)
            ind=result['independence']; expected=gold['independence']; status=result['claims'][g['focus']]['status']
            predictions.append(dict(case_id=g['id'],template=g['template'],condition=g['condition'],method=method,
                                    expected_independence=expected,predicted_independence=ind,
                                    latent_independence=latent['independence'],expected_status=gold['statuses'][g['focus']],
                                    predicted_status=status,independence_correct=int(ind==expected),
                                    status_correct=int(status==gold['statuses'][g['focus']]),
                                    false_independence=int(ind=='established' and expected!='established'),
                                    incorrect_dependence=int(ind=='dependent' and expected=='established'),
                                    abstention=int(ind=='undetermined'),
                                    witness_origin_match=int(all(w['support_origins']==visible['support_origins'][i]
                                         and w['challenge_origins']==visible['challenge_origins'][i] for i,w in result['claims'].items())),
                                    median_query_us=statistics.median(timings)/1000))
            method_details[method]=result
            db.execute('INSERT INTO assessments VALUES (?,?,?,?)',(g['id'],method,'v0',json.dumps(result)))
        rev=revisions(g);updates.extend(rev)
        details.append(dict(graph=g,expected=gold,methods=method_details,
                            updates=[{k:v for k,v in r.items() if k not in {'before'}} for r in rev]))
    db.commit();db.close()
    write_csv(out/'predictions.csv',predictions)
    flat=[{k:v for k,v in r.items() if k not in {'before','after','graph'}} for r in updates]
    write_csv(out/'revisions.csv',flat)
    summary=[]
    for method in METHODS:
        rs=[r for r in predictions if r['method']==method];n=len(rs)
        eligible=sum(r['expected_independence']!='established' for r in rs)
        independent=sum(r['expected_independence']=='established' for r in rs)
        summary.append(dict(method=method,n=n,
            independence_accuracy=sum(r['independence_correct'] for r in rs)/n,
            claim_status_accuracy=sum(r['status_correct'] for r in rs)/n,
            false_independence_rate=sum(r['false_independence'] for r in rs)/eligible if eligible else None,
            incorrect_dependence_rate=sum(r['incorrect_dependence'] for r in rs)/independent if independent else None,
            abstention_rate=sum(r['abstention'] for r in rs)/n,
            witness_origin_match_rate=sum(r['witness_origin_match'] for r in rs)/n,
            median_query_us=statistics.median(r['median_query_us'] for r in rs)))
    write_csv(out/'summary.csv',summary)
    # Paired bootstrap resamples whole templates, preserving all six variants.
    rng=random.Random(seed);paired=[]
    for baseline in ('citation_count','untyped_ancestry'):
        diffs=[]
        for t in range(templates):
            typed=[r['independence_correct'] for r in predictions if r['template']==t and r['method']=='typed']
            other=[r['independence_correct'] for r in predictions if r['template']==t and r['method']==baseline]
            diffs.append(statistics.mean(typed)-statistics.mean(other))
        boot=sorted(statistics.mean(rng.choices(diffs,k=len(diffs))) for _ in range(2000))
        paired.append(dict(comparison='typed minus '+baseline,metric='independence accuracy',
                           mean_difference=statistics.mean(diffs),ci95=[boot[49],boot[1949]],unit='template'))
    hashes={p.relative_to(out).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((out/'dataset').glob('*.json'))}
    manifest=dict(artifact_version=VERSION,seed=seed,templates=templates,cases=len(cases),methods=METHODS,
                  timing_repetitions=repeats,python=sys.version,platform=platform.platform(),dataset_sha256=hashes,
                  policy='observational-origins-v1',all_revision_checks_pass=all(r['equal_to_full'] and r['preserved_unrelated'] for r in updates),
                  note='Controlled synthetic validation. Timings include Python view construction; no scalability or human-study claim.')
    dump(out/'manifest.json',manifest);dump(out/'paired_comparisons.json',paired)
    dump(out/'explorer_data.json',dict(cases=details,summary=summary,manifest=manifest))
    template=Path(__file__).with_name('explorer_template.html').read_text(encoding='utf-8')
    data=json.dumps(dict(cases=details,summary=summary,manifest=manifest),ensure_ascii=False).replace('<','\\u003c')
    (out/'explorer.html').write_text(template.replace('__EMBEDDED_DATA__',data),encoding='utf-8')
    report=['# Controlled synthetic pilot results','',f'{len(cases)} graphs; {len(updates)} independent revision checks; seed {seed}.',
            '', '| Method | Independence accuracy | Claim status accuracy | Abstention |', '|---|---:|---:|---:|']
    for r in summary:report.append(f"| {r['method']} | {r['independence_accuracy']:.1%} | {r['claim_status_accuracy']:.1%} | {r['abstention_rate']:.1%} |")
    report+=['',f"Revision equivalence and unrelated-claim preservation: {manifest['all_revision_checks_pass']}.",
             '', 'The oracle uses an independent path enumerator and a declared finite completion set. Perfect performance on this constructed suite is a semantic conformance result, not empirical evidence of real-world reliability.',
             'The partial invalidation implementation still recomputes grounding globally. Timing results do not demonstrate an incremental speed-up.',
             'Bootstrap intervals resample templates; repeated deterministic condition effects may produce degenerate intervals. Broader graph families and real annotation are needed.']
    (out/'REPORT.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
    print(json.dumps(dict(cases=len(cases),revision_checks=len(updates),all_revision_checks_pass=manifest['all_revision_checks_pass'],summary=summary),indent=2))

def main():
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest='command',required=True)
    r=sub.add_parser('run');r.add_argument('--out',type=Path,default=Path('results'))
    r.add_argument('--templates',type=int,default=20);r.add_argument('--seed',type=int,default=20261107)
    r.add_argument('--repeats',type=int,default=5)
    a=sub.add_parser('assess');a.add_argument('graph',type=Path);a.add_argument('--purpose',default='research')
    a.add_argument('--method',choices=METHODS,default='typed')
    args=p.parse_args()
    if args.command=='run':
        if args.templates<1 or args.repeats<1:p.error('templates and repeats must be positive')
        run(args.out,args.templates,args.seed,args.repeats)
    else:
        graph=json.loads(args.graph.read_text(encoding='utf-8'));validate(graph)
        print(json.dumps(evaluate(graph,args.method,args.purpose),indent=2))

if __name__=='__main__':main()
