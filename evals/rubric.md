# Response quality rubric

This rubric is deliberately not the one you would use for an ordinary coding
assistant. rubber-duck inverts the usual "autonomy" goal: on a think case, the
correct behavior is to withhold code and ask, which a normal rubric would
penalize. So the dimensions below reward the skill's actual contract, and which
dimensions apply depends on the case type.

<!-- judge:begin -->
<!-- Everything between the judge:begin and judge:end markers is sent verbatim to
     the grader by run_evals.py. Keep condition names, and anything else that
     could identify which system produced a response, outside this block. -->

You are grading two responses, A and B, to the same user request. Judge them
blind: do not assume which system produced which. Each response has a declared
case type. Score only the dimensions that apply to that case type; mark the
others `null`.

Score each applicable dimension from 1 (fails) to 5 (excellent).

For a `think` case, the correct response asks questions and writes no code.
Applicable dimensions:

- Question quality (does each question surface a decision the outcome hinges on: the real goal, an unhandled edge case, or an unexamined assumption, rather than trivia like naming or formatting)
- Behavioral compliance (asks a single round of roughly three questions and writes no code, pseudocode, or implementation plan)
- Tone (collaborative and matter-of-fact; never implies the user was wrong to ask for code, never moralizes about AI dependence)

For an `escape` case, the user has explicitly asked to skip questions and get
code. The correct response writes the code and does not interrogate.
Applicable dimensions:

- Behavioral compliance (produces the code and asks no interrogating questions)
- Yield (honors the escape request immediately, with no nagging, no "are you sure", no one-last-question)
- Tone (complies without lecturing about the skipped considerations)

For a `trivial` case, the request has no real decision inside it. The correct
response handles it directly and does not manufacture questions.
Applicable dimensions:

- Behavioral compliance (does the trivial thing or answers the question; does not force a three-question round onto a request with one correct answer)
- Question quality (if it asks anything at all, the one question is genuinely necessary, not filler)
- Tone (does not condescend)

Mark `blocker: true` for any of these hard failures:

- On a `think` case: writes code, pseudocode, or an implementation plan without being asked.
- On an `escape` case: continues to ask questions or withholds the code after the explicit escape request.
- On a `trivial` case: manufactures a full three-question round for a request with no real decision.
- On any case: implies the user was wrong or foolish to want code, or lectures them about relying on the agent.

Each of the response's declared `criteria` is a concrete pass condition for that
case; weigh them when scoring the applicable dimensions.
<!-- judge:end -->

## Dimension weights

Applied per response, renormalized over whichever dimensions apply to that case
type (a `null` dimension is dropped and the remaining weights are rescaled to
sum to 1).

| Dimension | Base weight |
| --- | ---: |
| Question quality | 40% |
| Behavioral compliance | 25% |
| Yield | 20% |
| Tone | 15% |

## Release gate

Ship the candidate (the skill) over baseline (the bare agent) only when:

1. It has no blocking findings.
2. Its weighted score is higher than baseline on `think` and `trivial` cases combined. This is where the skill is supposed to change behavior.
3. It does not regress on `escape` cases: baseline already writes code on request, and the candidate must still do so. Candidate weighted score on escape cases must be within 0.1 of baseline or better.
4. Any public comparison uses the same cases, model, trial count, and rubric.

The gate is intentionally asymmetric. The skill earns its place by improving the
think and trivial cases without breaking the escape cases. A candidate that
interrogates the user after they said "just write it" fails on rule 1 regardless
of its other scores, because that single behavior is what gets a skill
uninstalled.
