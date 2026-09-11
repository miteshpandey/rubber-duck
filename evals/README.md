# Evaluations

This harness measures whether the rubber-duck skill actually changes behavior,
rather than whether the responses look nice. It compares two conditions on the
same prompts:

- **baseline**: the bare model, no skill.
- **candidate**: the same model with the skill body injected as its system prompt.

Cases live in [cases.jsonl](cases.jsonl). The scoring contract lives in
[rubric.md](rubric.md). Recorded results live in [RESULTS.md](RESULTS.md).

## Why the rubric is not a generic one

Most coding-assistant rubrics reward autonomy: the agent doing the work and not
pushing it back to the user. rubber-duck deliberately inverts that on `think`
cases, where the correct behavior is to withhold code and ask. A generic rubric
would score the skill as a regression. So the rubric scores each response only on
the dimensions that apply to its case type, and the release gate is asymmetric:
the skill has to improve the `think` and `trivial` cases without breaking the
`escape` cases.

## Setup

```bash
pip install anthropic
export ANTHROPIC_API_KEY=sk-ant-...
```

The harness calls an Anthropic model directly, because rubber-duck is a Claude
skill and a result measured on the model it targets is the honest one. A full run
is small (10 cases, a few trials, one judge call per case group), on the order of
a few dollars.

## Run

```bash
# 1. Sanity-check the cases and rubric before spending anything.
python3 evals/run_evals.py validate

# 2. Generate both conditions. Resumable: rerun to fill any gaps.
python3 evals/run_evals.py generate --trials 3

# 3. Judge blind. Both conditions for a case are graded in one call,
#    relabeled A/B with the order permuted per case so position carries no signal.
python3 evals/run_evals.py judge

# 4. Apply the release gate.
python3 evals/run_evals.py score
```

Intermediate files land in `evals/results/` (git-ignored): `responses.jsonl`
from generate, `scores.jsonl` from judge.

## Design choices worth naming

These are the parts that make the result trustworthy, and the parts you should be
able to defend if someone asks:

- **Paired, not absolute.** The number that matters is candidate minus baseline on identical prompts. Absolute scores drift with the model and the judge; the delta is what isolates the skill.
- **Blind judging.** The judge never sees which response came from which condition. Labels are permuted per case group by a digest of the group key, so the permutation is reproducible across reruns but carries no positional signal.
- **Marker-gated rubric.** Only the region of `rubric.md` between the `judge:begin` and `judge:end` markers reaches the grader. The release-gate wording below the markers names the conditions, and leaking that to a blind grader would defeat the blinding.
- **Model pinned.** The model is recorded with the results. A skill result on an unpinned model is not reproducible, because per-response behavior and cost both move with the model version.

## Deliberately not here

No multi-provider CLI runner and no budget-metering layer. Those matter when you
are benchmarking several agent CLIs against each other; for one skill on one
model they are scaffolding, not signal. If this skill is ever ported to other
agents, that is when a runner abstraction earns its place.
