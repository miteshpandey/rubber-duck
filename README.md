<div align="center">

# rubber-duck

**A skill that makes your coding agent ask before it builds.**

No AI slop. No 200 lines built on a wrong assumption. Three questions first, code second.

[![License](https://img.shields.io/github/license/miteshpandey/rubber-duck?style=flat)](LICENSE)

</div>

## Install

Copy/paste into your Claude Code CLI:

```
claude plugin marketplace add miteshpandey/rubber-duck
claude plugin install rubber-duck@rubber-duck
```

Then invoke it with `/rubber-duck` before a request you want to think through. Full instructions in [INSTALL.md](INSTALL.md).

## What it does

You invoke `/rubber-duck`, then describe what you want to build. Instead of writing code, the agent asks you exactly three questions: the ones that surface what you have not decided yet. The real goal. The edge case you skipped. The assumption you did not examine. One round, then it waits. It writes code only after you ask it to, or the instant you say "just write it".

It is the rubber duck from rubber-duck debugging, except the duck asks the questions.

## What changes

| Without | With |
| --- | --- |
| **You:** Add login to my app.<br><br>**Agent:** Here's a complete auth setup. I've added email/password login with bcrypt hashing, express-session for session management, a `users` table, login and logout routes, and middleware to protect your routes. *(60 lines of code assuming a stack, a flow, and a threat model you never specified.)* | **You:** `/rubber-duck` Add login to my app.<br><br>**Agent:**<br>1. Who logs in, and what are they logging into: is this a handful of internal users or public signups at scale?<br>2. What should happen on a failed or repeated login attempt: lockout, rate limit, nothing?<br>3. You have not said session or token. Is there a reason this needs to be stateless (mobile clients, multiple services), or is a session cookie fine?<br><br>*Answer these and I'll build the version that fits, or say "just write it" and I'll pick sensible defaults.* |

The point is not to slow you down forever. It is to spend ninety seconds deciding the three things that would otherwise cost you an afternoon of rewrites.

## The rules

Full text in [skills/rubber-duck/SKILL.md](skills/rubber-duck/SKILL.md).

1. On invocation, questions only. No code on the first turn.
2. Exactly three questions.
3. Aim them at the goal, the edge case, and the assumption. Never at trivia.
4. One round, then stop and wait.
5. After answers, reflect the decision in one line, then offer to build.
6. Never imply the user was wrong to want code.
7. No preamble, no closers.
8. Escape hatch: "just write it" drops the mode instantly, no nagging.
9. Trivial request with no real decision: say so, do not manufacture three questions.

## Does it actually work?

There is an evaluation harness in [evals/](evals/) that measures whether the skill changes behavior, using a blind, baseline-versus-candidate comparison on an Anthropic model. Results and methodology live in [evals/RESULTS.md](evals/RESULTS.md).

## Tune it

Fork, edit `skills/rubber-duck/SKILL.md`, then swap your copy in:

```
claude plugin uninstall rubber-duck
claude plugin marketplace remove rubber-duck
claude plugin marketplace add <your-username>/rubber-duck
claude plugin install rubber-duck@rubber-duck
```

## Credits

Built by [Mitesh Pandey](https://github.com/miteshpandey). Structure and eval methodology inspired by [ayghri/i-have-adhd](https://github.com/ayghri/i-have-adhd).

## License

MIT.
