# Input model and extension contract

Each fixture is a JSON object with `id`, `template`, `condition`, `synthetic`,
`nodes`, `edges`, `focus`, `pair`, `incomplete`, `snapshot`. `template` and
`condition` are reporting metadata only; the evaluator does not read them.

## Nodes

```json
{"id":"o1","kind":"observation","label":"Synthetic observation A",
 "active":true,"purposes":["research","public"]}
```

Supported kinds: observation, document, claim, tool. Identifiers must be unique.
Observations are provisional grounds only by the chosen benchmark policy.

## Relations

```json
{"id":"e1","src":"s1","dst":"o1","kind":"derivedFrom",
 "mode":"observed","accepted":true,"active":true,
 "purposes":["research","public"]}
```

`derivedFrom`: child → parent. `supports` and `challenges`: source → claim.
`processedWith`: artifact → tool. Each edge has a stable ID, acquisition mode,
acceptance flag and permitted purposes. Rejected, inactive or inadmissible
records do not participate in assessment. Unsupported kinds or dangling IDs
are rejected by validation. Annotation provenance may be added as extra JSON
metadata; recursively contestable edge attestations are outside this version.

`incomplete` contains identifiers whose upstream ancestry may be missing.
No hidden edge or hidden ground-truth label is supplied to the evaluator.
The example hidden case has two disjoint visible roots and an explicit gap
at s2; the oracle considers absence/presence of a copying edge s2 → s1.

## Assessment

`claims` maps claim IDs to status, support origins, challenge origins,
coverage, gap descriptors and witness edges. Pair-level independence and
shared observational roots are returned separately. Policy, purpose and
snapshot identify the assessment context.

## Controlled revisions

Each revision starts from v0, not from the preceding update. Retraction
deactivates o1. Permission withdrawal keeps o1 available to research but
removes public admissibility. Addition inserts new_o and a challenges edge
to the focus claim. Affected nodes are discovered through old and new
downstream dependency relations, including challenge edges.

## Extension to annotated external material

Do not infer a support or challenge relation merely from a citation or an RDF
edge. First create an explicit claim and context, identify the relevant
source passage or observation, and independently annotate whether and how
it supports that claim. Record who annotated it, the method, purpose and
uncertainty. Reconcile competing annotations without treating an institutional
description as universal ground truth. Use only authorised material. The
current package deliberately starts with synthetic graphs and no model calls.
