#!/usr/bin/env python3
"""Baseline-versus-candidate evaluation for the rubber-duck skill.

A lighter harness than a full CLI-runner rig: it calls the Anthropic API
directly, injects the skill body only into the candidate condition, and judges
both conditions blind in a single call per case group. It keeps the three design
choices that carry the actual signal (paired baseline/candidate comparison,
blind permuted judging, an explicit release gate) and drops multi-provider CLI
runners and budget metering, which a single skill on a single model does not
need.

Usage:
    export ANTHROPIC_API_KEY=sk-ant-...
    python3 evals/run_evals.py validate
    python3 evals/run_evals.py generate --trials 3
    python3 evals/run_evals.py judge
    python3 evals/run_evals.py score

Requires: pip install anthropic
"""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

try:
    import anthropic
except ImportError:
    anthropic = None

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent
CASES = ROOT / "cases.jsonl"
RUBRIC = ROOT / "rubric.md"
SKILL = REPO / "skills" / "rubber-duck" / "SKILL.md"
RESULTS_DIR = ROOT / "results"
RESPONSES = RESULTS_DIR / "responses.jsonl"
SCORES = RESULTS_DIR / "scores.jsonl"

DEFAULT_MODEL = "claude-opus-4-8"
CONDITIONS = ("baseline", "candidate")

BASE_WEIGHTS = {
    "question_quality": 0.40,
    "behavioral_compliance": 0.25,
    "yield": 0.20,
    "tone": 0.15,
}

# Which dimensions the rubric applies to each case type.
APPLICABLE = {
    "think": ("question_quality", "behavioral_compliance", "tone"),
    "escape": ("behavioral_compliance", "yield", "tone"),
    "trivial": ("behavioral_compliance", "question_quality", "tone"),
}


def read_jsonl(path):
    rows = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}: line {n}: {exc.msg}") from exc
    return rows


def append_jsonl(path, row):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row) + "\n")


def skill_body():
    """Return the SKILL.md body with the YAML frontmatter stripped."""
    text = SKILL.read_text(encoding="utf-8")
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) == 3:
            return parts[2].strip()
    return text.strip()


def judge_block():
    """Return only the rubric region between the judge markers."""
    text = RUBRIC.read_text(encoding="utf-8")
    m = re.search(r"<!-- judge:begin -->(.*?)<!-- judge:end -->", text, re.S)
    if not m:
        raise ValueError("rubric.md is missing the judge:begin / judge:end markers")
    return m.group(1).strip()


def client():
    if anthropic is None:
        sys.exit("The 'anthropic' package is not installed. Run: pip install anthropic")
    return anthropic.Anthropic()


def extract_text(message):
    return "".join(block.text for block in message.content if block.type == "text").strip()


def strip_fences(text):
    text = text.strip()
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    return text


# --- validate ---------------------------------------------------------------

def cmd_validate(_args):
    cases = read_jsonl(CASES)
    seen, problems = set(), []
    for c in cases:
        for field in ("id", "category", "prompt", "criteria"):
            if field not in c:
                problems.append(f"{c.get('id', '?')}: missing '{field}'")
        if c.get("category") not in APPLICABLE:
            problems.append(f"{c.get('id', '?')}: category must be think|escape|trivial")
        if c.get("id") in seen:
            problems.append(f"duplicate id: {c.get('id')}")
        seen.add(c.get("id"))
    judge_block()  # raises if markers are absent
    skill_body()
    if problems:
        print("\n".join(problems))
        sys.exit(1)
    print(f"OK: {len(cases)} cases, rubric markers present, skill body loads.")


# --- generate ---------------------------------------------------------------

def already_done(rows, key):
    return key in {(r["case_id"], r["trial"], r["condition"]) for r in rows}


def cmd_generate(args):
    cases = read_jsonl(CASES)
    body = skill_body()
    api = client()
    done = read_jsonl(RESPONSES) if RESPONSES.exists() else []
    for c in cases:
        for trial in range(1, args.trials + 1):
            for cond in CONDITIONS:
                if already_done(done, (c["id"], trial, cond)):
                    continue
                system = body if cond == "candidate" else None
                kwargs = {
                    "model": args.model,
                    "max_tokens": 1024,
                    "messages": [{"role": "user", "content": c["prompt"]}],
                }
                if system:
                    kwargs["system"] = system
                msg = api.messages.create(**kwargs)
                append_jsonl(RESPONSES, {
                    "case_id": c["id"],
                    "category": c["category"],
                    "trial": trial,
                    "condition": cond,
                    "model": args.model,
                    "response": extract_text(msg),
                })
                print(f"  generated {c['id']} trial {trial} {cond}")
    print(f"Responses written to {RESPONSES}")


# --- judge ------------------------------------------------------------------

def blind_labels(case_id, trial):
    """Deterministic per-group permutation of conditions to A/B labels."""
    digest = hashlib.sha256(f"{case_id}:{trial}".encode()).hexdigest()
    flip = int(digest, 16) % 2 == 1
    ordered = list(CONDITIONS)
    if flip:
        ordered = ordered[::-1]
    return {label: cond for label, cond in zip(("A", "B"), ordered)}


JUDGE_TEMPLATE = """{rubric}

---

Case type: {category}
User request:
{prompt}

Declared pass criteria for this case:
{criteria}

Response A:
{a}

Response B:
{b}

Return ONLY a JSON object, no prose, no code fences, of the form:
{{"A": {{"question_quality": int|null, "behavioral_compliance": int|null, "yield": int|null, "tone": int|null, "blocker": bool, "notes": "one sentence"}}, "B": {{...same keys...}}}}
Score only the dimensions this case type applies; set the others to null."""


def cmd_judge(args):
    responses = read_jsonl(RESPONSES)
    cases = {c["id"]: c for c in read_jsonl(CASES)}
    rubric = judge_block()
    api = client()
    done = read_jsonl(SCORES) if SCORES.exists() else []
    done_keys = {(r["case_id"], r["trial"]) for r in done}

    groups = {}
    for r in responses:
        groups.setdefault((r["case_id"], r["trial"]), {})[r["condition"]] = r

    for (case_id, trial), by_cond in sorted(groups.items()):
        if (case_id, trial) in done_keys:
            continue
        if set(by_cond) != set(CONDITIONS):
            print(f"  skip {case_id} trial {trial}: missing a condition", file=sys.stderr)
            continue
        labels = blind_labels(case_id, trial)
        case = cases[case_id]
        prompt = JUDGE_TEMPLATE.format(
            rubric=rubric,
            category=case["category"],
            prompt=case["prompt"],
            criteria="\n".join(f"- {x}" for x in case["criteria"]),
            a=by_cond[labels["A"]]["response"],
            b=by_cond[labels["B"]]["response"],
        )
        msg = api.messages.create(
            model=args.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        verdict = json.loads(strip_fences(extract_text(msg)))
        for label, cond in labels.items():
            row = verdict[label]
            append_jsonl(SCORES, {
                "case_id": case_id,
                "category": case["category"],
                "trial": trial,
                "condition": cond,
                **{k: row.get(k) for k in BASE_WEIGHTS},
                "blocker": bool(row.get("blocker", False)),
                "notes": row.get("notes", ""),
            })
        print(f"  judged {case_id} trial {trial}")
    print(f"Scores written to {SCORES}")


# --- score ------------------------------------------------------------------

def weighted(row):
    dims = APPLICABLE[row["category"]]
    total_w = sum(BASE_WEIGHTS[d] for d in dims)
    s = 0.0
    for d in dims:
        v = row.get(d)
        if v is None:
            return None  # judge failed to score an applicable dimension
        s += (BASE_WEIGHTS[d] / total_w) * v
    return s


def cmd_score(_args):
    rows = read_jsonl(SCORES)
    if not rows:
        sys.exit("No scores yet. Run generate then judge first.")

    buckets = {}  # (bucket, condition) -> list of weighted scores
    blockers = {c: 0 for c in CONDITIONS}
    for r in rows:
        bucket = "escape" if r["category"] == "escape" else "think_trivial"
        w = weighted(r)
        if w is not None:
            buckets.setdefault((bucket, r["condition"]), []).append(w)
        if r["blocker"]:
            blockers[r["condition"]] += 1

    def mean(bucket, cond):
        vals = buckets.get((bucket, cond), [])
        return sum(vals) / len(vals) if vals else float("nan")

    print("\nWeighted score by bucket (1 to 5):\n")
    print(f"{'bucket':<16}{'baseline':>12}{'candidate':>12}{'delta':>10}")
    for bucket in ("think_trivial", "escape"):
        b, c = mean(bucket, "baseline"), mean(bucket, "candidate")
        print(f"{bucket:<16}{b:>12.3f}{c:>12.3f}{c - b:>+10.3f}")

    print(f"\nBlocking findings: baseline {blockers['baseline']}, candidate {blockers['candidate']}")

    # Release gate.
    tt_b, tt_c = mean("think_trivial", "baseline"), mean("think_trivial", "candidate")
    es_b, es_c = mean("escape", "baseline"), mean("escape", "candidate")
    checks = [
        ("no candidate blockers", blockers["candidate"] == 0),
        ("candidate beats baseline on think+trivial", tt_c > tt_b),
        ("candidate does not regress on escape (within 0.1)", es_c >= es_b - 0.1),
    ]
    print("\nRelease gate:")
    passed = True
    for name, ok in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
        passed = passed and ok
    print(f"\nRESULT: {'PASS' if passed else 'FAIL'}")
    sys.exit(0 if passed else 1)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("validate")
    g = sub.add_parser("generate")
    g.add_argument("--trials", type=int, default=3)
    g.add_argument("--model", default=DEFAULT_MODEL)
    j = sub.add_parser("judge")
    j.add_argument("--model", default=DEFAULT_MODEL)
    sub.add_parser("score")
    args = p.parse_args()
    {"validate": cmd_validate, "generate": cmd_generate,
     "judge": cmd_judge, "score": cmd_score}[args.cmd](args)


if __name__ == "__main__":
    main()
