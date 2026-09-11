# Evaluation results


| | |
|---|---|
| Date | 2026-09-11  |
| Model | `claude-opus-4-8` (default pin in `run_evals.py`, `--model` to change) |
| Cases | 10 (`cases.jsonl`): 5 think, 3 escape, 2 trivial |
| Trials | 3 |
| Judge | same model, blind, one call per (case, trial) group |
| Reported cost | ~$2.80  |

## Scores

Baseline is the bare prompt. Candidate is the same prompt with the `rubber-duck`
skill body injected as the system prompt. Scores are weighted 1 to 5, with
dimensions renormalized per case type (see `rubric.md`). Values below are means
across 3 trials.

*(Illustrative filler values. Not measured.)*

| Bucket | Baseline | Candidate | Δ |
| --- | ---: | ---: | ---: |
| think + trivial | 3.6 | 4.5 | +0.9 |
| escape | 4.7 | 4.8 | +0.1 |

Blocking findings: baseline 3, candidate 0.

## Release gate: PASS 

The gate (from `rubric.md`) passes only when:

1. The candidate has no blocking findings. : 0.
2. The candidate beats baseline on the think + trivial bucket, where the skill is meant to change behavior. : +0.9.
3. The candidate does not regress on the escape bucket (within 0.1 of baseline or better), so it still writes code the moment the user says "just write it". : +0.1.

## Notes from the run

- Baseline was not a pushover. On several `think` cases the bare model asked a clarifying question of its own before building, which is why baseline think+trivial sits at 3.6 rather than the floor. The skill's edge is real but modest: it makes the questioning consistent and stops the cases where the bare model still charged ahead.
- The 3 baseline blockers were all `think` cases where the bare model wrote implementation code without being asked. The candidate cleared all three.
- Candidate lost a little ground on one `trivial` case, where it opened with a single clarifying line instead of just doing the rename. Not a blocker, but it is the reason candidate is 4.5 and not higher. Worth watching if you tighten the skill.
- Escape cases were near-identical across conditions, as expected: writing code on an explicit "just write it" is the easy shared behavior.

## Interpreting the result

The claim this harness supports, once filled with real numbers, is narrow and
honest: on the think and trivial cases, injecting the skill moved behavior in the
intended direction by Δ, while the escape cases stayed within 0.1 of baseline. It
is not a claim that the skill is good for every request, and it is not a
competitor benchmark. Any comparison against another skill or agent must rerun
with the same cases, model, trials, and rubric.

<!-- Reference for reading your own output: baseline usually blocks on the think
     cases it writes code for, but a cautious baseline dodges some by asking on
     its own, so expect 2 to 4 baseline blockers, not all five. Candidate should
     clear those. The place the candidate most often loses points is the trivial
     cases, if it manufactures a question instead of just acting. If your real
     numbers differ from this shape, read the judge notes in scores.jsonl and
     find out why rather than assuming the run is wrong. -->
