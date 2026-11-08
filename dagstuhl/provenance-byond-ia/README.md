# Evidence Provenance Experiment

A reproducible research prototype for **recursive evidence, dependency-aware corroboration, and contestable provenance** in AI-mediated knowledge production.

The experiment asks whether a database can distinguish multiple documents from multiple independent evidential origins, preserve conflicting evidence, and revise assessments when a source is retracted or becomes inadmissible for a particular purpose.

This repository accompanies a VLDB vision-paper research effort. It contains a controlled synthetic benchmark, a Python implementation, baseline comparisons, an independent reference oracle, revision tests, and an offline interactive graph explorer. It is an initial validation of explicit computational semantics, not a completed system for determining the truth of real-world claims.

## At a glance

| Component | Included |
| --- | --- |
| Benchmark | 120 synthetic graphs from 20 paired templates and six evidence conditions |
| Comparisons | Citation counting, untyped ancestry, typed evidence assessment, and two ablations |
| Evidence states | Supported, refuted, undetermined, and conflicting |
| Revision evaluation | 360 checks covering source retraction, new challenges, and permission withdrawal |
| Reference oracle | Separate exhaustive simple-path implementation with declared completion worlds |
| Storage and reports | SQLite database, JSON fixtures, CSV results, and reproducibility manifest |
| Explorer | Standalone HTML with search, selectable nodes, method comparisons, and revision snapshots |
| Requirements | Python 3.9 or newer; standard library only |

No GPU, model API key, network connection, or additional Python packages are required to run the experiment.

## Quick start

After cloning the repository or extracting the software package, open a terminal in the directory containing `experiment.py`.

Run the tests:

```bash
python3 -m unittest discover -s tests -v
```

Generate the benchmark and evaluate all methods:

```bash
python3 experiment.py run \
  --out results \
  --templates 20 \
  --seed 20261107 \
  --repeats 5
```

On Windows, use `py -3` instead of `python3` if that is how Python is installed. For a single-line command:

```text
py -3 experiment.py run --out results --templates 20 --seed 20261107 --repeats 5
```

Open [results/explorer.html](results/explorer.html) in a browser to inspect the precomputed graphs and results. Download or clone the file first: viewing HTML source on GitHub does not execute the explorer. The supplied package already includes generated results, so the explorer can also be used before running Python.

Running the experiment again replaces generated result files in the selected output directory. Use a different `--out` directory to preserve a previous run.

## What the experiment tests

The benchmark separates the evidential status of a claim from the independence of the sources presented as corroboration.

| Condition | Construction | Intended typed response |
| --- | --- | --- |
| Independent observations | Two source accounts reach separately acquired observations | Established observational separation under complete coverage |
| Repeated evidence | Different documents descend from one observation | Dependent origins; repeated documents do not add independent observations |
| Circular justification | Accounts support each other without external grounding | Undetermined support; no established independent corroboration |
| Shared computational tool | Separate observations share a processing tool | Distinct observational origins, with shared processing recorded separately |
| Hidden ancestry | Visible roots differ, but an explicit gap permits a hidden copying dependency | Independence remains undetermined |
| Conflicting evidence | Grounded supporting and challenging accounts coexist | Conflict with both sets of origins retained |

The 20 templates vary intermediate document depth, unrelated branches, and insertion order. The six conditions are paired within each template. All claims and evidence labels are synthetic.

## Using the HTML explorer

1. Open `results/explorer.html` in a modern browser.
2. Select an **Evidence condition** and **Graph template** in the left panel.
3. Choose an **Assessment method** to compare the predictions for the same input graph.
4. Select a node in the graph or the node list to inspect its type, relations, permitted purposes, and assessment witnesses.
5. Use **Revision snapshot** to inspect a retraction, added challenge, or withdrawal of public-use permission. Revision snapshots use the typed method automatically.
6. Use search, category highlighting, zoom controls, and **Reset view** to navigate.

The assessment boxes mean:

| Display | Interpretation |
| --- | --- |
| Claim c | Whether admissible evidence supports, refutes, conflicts with, or leaves the claim undetermined |
| Source pair | Whether observational origins are established as separate, dependent, or undetermined |
| Coverage | Whether relevant ancestry is declared complete or incomplete |

A claim can have visible support while the independence of its sources remains undetermined. Node colours identify observations, documents, claims, and tools; they do not encode credibility or cultural importance.

For a short demonstration, select **Repeated evidence** and compare `typed` with `citation_count`. Then select **Hidden ancestry** and compare `typed` with `without_coverage`. Finally, return to **Repeated evidence** and choose **Withdraw public permission**.

The explorer displays precomputed assessments. It does not rerun the Python reasoner when a control changes. Its JSON export contains the selected synthetic fixture, including its purpose metadata; it is not a protected public-data export.

## Assessing a single graph

```bash
python3 experiment.py assess results/dataset/t00_hidden.json
```

Compare against citation counting:

```bash
python3 experiment.py assess results/dataset/t00_repeated.json \
  --method citation_count
```

Evaluate a purpose-specific view:

```bash
python3 experiment.py assess examples/withdrawn_public_permission.json \
  --purpose public
```

The output is JSON containing evidence states, supporting and challenging origins, coverage descriptors, witness relation identifiers, and pair-level independence.

## Assessment semantics

The policy identifier is `observational-origins-v1`.

- An admissible observation is a provisional positive ground under the benchmark policy.
- Accepted `supports` relations propagate positive grounding from source to target.
- Accepted `derivedFrom` relations propagate grounding from parent source to child artifact. The stored relation points from child to parent.
- `processedWith` records a computational dependency without propagating evidential grounding.
- A `challenges` relation contributes negative evidence when its source has positive grounding.

The two evidence indicators produce these states:

| Positive evidence | Negative evidence | State |
| --- | --- | --- |
| Present | Absent | Supported |
| Absent | Present | Refuted |
| Absent | Absent | Undetermined |
| Present | Present | Conflicting |

Negative evidence does not propagate through support in this initial fragment. Pure positive cycles cannot create their own grounding. Conflict does not entail unrelated claims. Accepted annotations are supplied rather than extracted automatically; acquisition modes are retained without treating them as credibility scores.

For a pair of sources, common observational roots establish dependence under this policy. Disjoint nonempty roots establish separation only when ancestry is declared complete. Otherwise, the answer is undetermined. This is **observational-origin separation**, not statistical independence or a guarantee of independent interpretation errors.

See [MODEL.md](MODEL.md) for the input format and extension boundaries.

## Methods and ablations

| Identifier | Behaviour |
| --- | --- |
| `citation_count` | Treats distinct source identifiers as corroboration and classifies claim status from direct support and challenge records |
| `untyped_ancestry` | Uses common ancestry across evidential and processing dependencies |
| `typed` | Distinguishes dependency types and respects declared incomplete ancestry |
| `without_types` | Removes type distinctions; intentionally duplicates the untyped baseline |
| `without_coverage` | Retains dependency types but ignores coverage gaps |

Every method receives the same visible graph and purpose filter. Grounded witness origins are computed by a shared component across methods and checked against the separate path oracle; witness agreement is not a comparative advantage attributed to the typed method.

## Revision tests

Each graph undergoes three separate updates, each starting from the original snapshot:

1. **Retract observation A:** remove its admissibility as active evidence and re-evaluate downstream claims.
2. **Add a challenge:** introduce a grounded challenging observation without deleting existing supporting evidence.
3. **Withdraw public-use permission:** retain research admissibility while excluding the observation from the public-purpose assessment.

For every update, partial invalidation is compared with full recomputation. An unrelated grounded claim checks that unaffected assessments remain stable. Permission withdrawal changes admissibility, not truth.

## Included pilot results

The supplied run uses 120 graphs, seed `20261107`, and five timing repetitions.

| Method | Independence accuracy | Claim status accuracy | Abstention |
| --- | ---: | ---: | ---: |
| Citation counting | 50.0% | 83.3% | 0.0% |
| Untyped ancestry | 66.7% | 100.0% | 16.7% |
| Typed assessment | 100.0% | 100.0% | 33.3% |
| Type ablation | 66.7% | 100.0% | 16.7% |
| Coverage ablation | 83.3% | 100.0% | 16.7% |

All **360 revision checks** agreed with full recomputation and preserved the unrelated claim. The supplied test log records **13 passing tests**, including comparisons on 60 additional random graphs, identifier and insertion-order invariance, purpose restrictions, witness reachability, and checks that oracle labels cannot influence the evaluator.

These are results on a deliberately constructed conformance suite. They do not establish real-world annotation quality or general reliability. The typed method's abstentions are intended responses to incomplete or ungrounded evidence, rather than unsuccessful attempts to maximise answer coverage.

### Evaluation measures

- **Independence accuracy:** agreement with the declared completion oracle.
- **False independence rate:** predictions of established independence among cases expected dependent or undetermined, divided by the number of those cases.
- **Incorrect dependence rate:** predictions of dependence among cases expected established, divided by the number of expected established cases.
- **Abstention:** undetermined predictions divided by all cases.
- **Claim status accuracy:** agreement on focus claim `c` with the separate path oracle.
- **Witness origin agreement:** reported supporting and challenging origin sets match the path oracle on visible records.
- **Revision correctness:** agreement with full recomputation and preservation of an unrelated claim.

Paired bootstrap comparisons resample complete templates with their six variants together. Repeated deterministic condition effects can produce degenerate intervals. Query and update microtimings include Python overhead and view construction; no performance threshold or scalability claim is asserted.

## Repository contents

Place the **contents** of the extracted `evidence_experiment` folder at the repository root, alongside this `README.md`.

| Path | Purpose |
| --- | --- |
| [experiment.py](experiment.py) | Generator, evaluator, reference oracle, runner, and CLI |
| [MODEL.md](MODEL.md) | Input schema and semantics |
| [explorer_template.html](explorer_template.html) | HTML template used to generate the standalone explorer |
| [tests/test_experiment.py](tests/test_experiment.py) | Semantic and regression tests |
| [examples/withdrawn_public_permission.json](examples/withdrawn_public_permission.json) | Purpose-specific assessment example |
| [TEST_RESULTS.txt](TEST_RESULTS.txt) | Supplied test log |
| [Evidence_Provenance_Experiment_Proposal.docx](Evidence_Provenance_Experiment_Proposal.docx) | Experiment proposal and implementation note |
| [results/REPORT.md](results/REPORT.md) | Pilot results and interpretation limits |
| [results/summary.csv](results/summary.csv) | Aggregate measures |
| [results/predictions.csv](results/predictions.csv) | Per-graph and per-method predictions |
| [results/revisions.csv](results/revisions.csv) | Revision checks and microtimings |
| [results/paired_comparisons.json](results/paired_comparisons.json) | Paired bootstrap comparisons |
| [results/evidence.sqlite](results/evidence.sqlite) | Stored cases, nodes, edges, and original assessments |
| [results/dataset/](results/dataset/) | Evaluator input graphs without oracle labels |
| [results/oracle/](results/oracle/) | Declared completion worlds and expected answers |
| [results/manifest.json](results/manifest.json) | Parameters, environment metadata, and dataset hashes |
| [results/explorer.html](results/explorer.html) | Offline graph explorer |

### Inspecting SQLite records

Using a SQLite client, open `results/evidence.sqlite` and run:

```sql
SELECT condition, COUNT(*)
FROM cases
GROUP BY condition;

SELECT case_id, src, kind, dst, mode
FROM edges
WHERE kind = 'processedWith';

SELECT case_id, method, snapshot, payload
FROM assessments
WHERE case_id = 't00_hidden';
```

## Limitations and next steps

The experiment assumes a frozen assessment policy, accepted annotations, and a small declared completion set. It does not enumerate arbitrary unknown dependencies, infer source credibility, or validate cultural interpretations. The engine and reference oracle use different algorithms but share the policy being tested.

Partial invalidation still recomputes grounding globally. **No incremental speed-up is claimed.** General argumentation semantics, recursively challenged relation attestations, statistical dependence, collective mandates, and automatic relation extraction remain future work.

The explorer embeds synthetic records and is a research inspection interface. Client-side filtering is not secure disclosure control. The current package contains no human-subject evaluation.

Useful extensions include broader random graph families, maintained grounding indexes, independently annotated authorised source passages, and user studies of whether people can identify repeated evidence and challenge a specific relation.

## Visual inspiration and attribution

The explorer's category colours, entity search, selectable nodes, and relation detail panel take inspiration from the [Qoyllur Rit’i relational atlas](https://javier-vz.github.io/kg-llm/grafo_interactivo.html?lang=es), inspected on 7 November 2026.

The implementation does not copy the atlas code or import its graph records. All benchmark labels are synthetic; none claims community endorsement, cultural authority, or an actual contested interpretation. Extending the experiment to external material requires separately justified evidence annotations and appropriate authorisation.

## Contributing and reporting problems

Report an issue with the command, Python version, seed, graph identifier, expected behaviour, and observed output. Include a small synthetic reproducer when possible. Proposed semantic changes should update the policy documentation and tests together, and should distinguish fixes to implementation from changes to the intended interpretation.
