# Evidence provenance experiment

A runnable research prototype for the VLDB vision on recursive evidence,
dependency-aware corroboration, and contestable situated provenance.

## Quick start

Requires Python 3.9 or newer. The experiment uses only the Python standard
library: no installation, GPU, network connection, API key, or model subscription.

```sh
cd evidence_experiment
python3 -m unittest discover -s tests -v
python3 experiment.py run --out results --templates 20 --seed 20261107 --repeats 5
```

Open `results/explorer.html` directly in a browser. A precomputed copy is
included in the release. The explorer works offline and embeds its dataset.
It is an inspection tool, not a second independent implementation of the reasoner.

To assess one JSON graph:

```sh
python3 experiment.py assess results/dataset/t00_hidden.json
python3 experiment.py assess results/dataset/t00_repeated.json --method citation_count
python3 experiment.py assess examples/withdrawn_public_permission.json --purpose public
```

## What is implemented

- 20 paired graph templates × 6 evidence conditions = 120 graphs. Templates vary
  path depth (1–3 intermediate documents), distractor branches (1–3), and insertion
  order. Conditions share the same template structure.
- Three comparators: distinct citation counting, untyped common ancestry, and
  typed observational-origin assessment. Two ablations remove type distinctions
  or coverage handling. `without_types` intentionally duplicates the untyped
  baseline; it is not another independent algorithm.
- A positive grounding fixed point, four evidence states, claim-relative
  observational-origin independence, explicit incomplete-ancestry boundaries,
  support/challenge origins, and witness edge identifiers.
- An independent exhaustive simple-path oracle. Hidden ancestry uses two
  explicitly declared possible worlds, one with a hidden copying dependency
  and one without it. The evaluator receives neither worlds nor expected labels.
- Three **separate** updates from v0 for every graph: retract observation A, add
  a challenging observation, withdraw permission for public use. 360 comparisons
  check partial invalidation against full recomputation and preserve an unrelated claim.
- Purpose filtering of nodes and relations. Withdrawal changes admissibility,
  not truth. The existence of a coverage gap is explicitly disclosable under
  this synthetic policy.
- SQLite persistence of fixtures, nodes, relations and v0 assessments; JSON and
  CSV exports; dataset SHA-256 hashes, software/environment manifest; paired
  template bootstrap differences; an offline interactive graph explorer.

## Frozen semantics

The policy identifier is `observational-origins-v1`. All observations are
provisional positive grounds under the policy, not certified facts. Accepted
`supports` edges propagate positive grounding from source to target. Accepted
`derivedFrom` edges propagate positive grounding from parent source to child
artifact (the stored edge points child → parent). `processedWith` is recorded
but does not propagate evidential grounding. `challenges` contributes negative
evidence when its source has positive observational grounding.

Evidence states use two indicators: support present / challenge present.
They are supported (1,0), refuted (0,1), undetermined (0,0), conflicting (1,1).
Negative evidence does not propagate through support in this small fragment;
there are no defeat priorities, probabilistic weights or automatic truth labels.
Pure positive cycles do not bootstrap grounding. Conflict does not entail
unrelated claims. Accepted annotations are assumed to have been adjudicated;
acquisition modes (`observed`, `declared`, `inferred`) are retained but are not
used as credibility scores.

For a pair of sources, any common observational root gives `dependent`;
disjoint nonempty roots with complete ancestry give `established`; remaining
cases give `undetermined`. This is observational-origin separation relative
to a frozen policy. It does **not** establish statistical independence or
independent interpretation errors in real models. A shared tool appears in
the graph but does not automatically merge observational origins.

Incomplete coverage is not negative evidence. A claim can be supported by
visible evidence while the independence of its sources remains undetermined.
The finite oracle completion set is part of the benchmark's assumptions;
it does not enumerate arbitrary real-world missing dependencies.

## Comparators

`citation_count` treats different source IDs as corroborating sources and
classifies a claim from direct incoming support/challenge records, without
requiring grounded ancestry. This is a deliberately simple citation baseline,
not a claim about every provenance system. `untyped_ancestry` retains positive
grounding for status queries but checks common ancestry using both evidence
and processing-tool dependencies. `typed` distinguishes those dependencies
and handles declared coverage. `without_coverage` keeps types but ignores gaps.
Every method receives the same graph and purpose filter. Grounded witness
origins are computed by a shared component for all methods; witness agreement
therefore measures that component's conformance, not a comparative advantage.

## Outputs

| File | Content |
| --- | --- |
| `results/REPORT.md` | Measured pilot results and interpretation limits |
| `results/summary.csv` | Aggregate accuracy, abstention and error rates |
| `results/predictions.csv` | One row per graph and method, including expected and latent answers |
| `results/revisions.csv` | 360 update checks and illustrative microtimings |
| `results/paired_comparisons.json` | Paired differences and template bootstrap intervals |
| `results/evidence.sqlite` | Queryable records and v0 assessments |
| `results/dataset/` | Evaluator input JSON graphs, without oracle labels |
| `results/oracle/` | Declared completion worlds and expected answers |
| `results/manifest.json` | Seed, software/environment metadata and dataset hashes |
| `results/explorer.html` | Standalone graph explorer with embedded synthetic data |
| `MODEL.md` | Input schema and extension boundaries |

False independence rate = predicted established among cases expected dependent
or undetermined, divided by the number of such cases. Incorrect dependence rate
= predicted dependent among expected established cases, divided by the number
of expected established cases. Abstention is predicted undetermined over all cases.
Claim accuracy is measured on focus claim c, independently of pair independence.
Witness origin match checks every claim's reported origin sets against the
separate path oracle on visible data. No timing threshold is asserted.

## Inspect stored records

```sql
SELECT condition, COUNT(*) FROM cases GROUP BY condition;
SELECT case_id,src,kind,dst,mode FROM edges WHERE kind='processedWith';
SELECT case_id,method,snapshot,payload FROM assessments WHERE case_id='t00_hidden';
```

## Scope and interpretation

This is a controlled semantic conformance experiment. Perfect performance on
graphs built for this policy is not evidence of real-world annotation quality,
reliable extraction, general argumentation semantics, security, or scalability.
The engine and oracle use different algorithms, but share the declared policy;
tests cannot validate the appropriateness of that policy for every context.

Partial invalidation recomputes the grounding fixed point globally and only
replaces affected claim assessments. Consequently, **no incremental speed-up
is claimed**. Timings include view construction and Python overhead. Use a
larger workload and maintained grounding indexes before testing systems efficiency.
Bootstrap intervals can be degenerate because condition effects recur across
templates; report this limitation rather than treating zero-width intervals as
population certainty.

The explorer embeds synthetic records, including records used in other
purposes. It is a researcher inspector, not a secure disclosure interface.
Do not load protected evidence into this offline HTML file expecting client-side
filtering to enforce secrecy. General policy noninterference and collective
mandates are not implemented. The package performs no human-subject study.

## Reference graph

Visual inspiration: Javier's public Qoyllur Rit’i relational atlas at
https://javier-vz.github.io/kg-llm/grafo_interactivo.html?lang=es
(inspected 7 November 2026). The prototype adopts category colours, search,
selectable entities and an adjacent relation detail panel. It does not copy
the atlas code or import its records. All benchmark labels are synthetic;
none asserts a substantive community interpretation or cultural authority.
An optional extension can map authorised RDF records into source artifacts
and separately annotate evidence relations; RDF relationships alone do not
constitute independent supporting evidence.
