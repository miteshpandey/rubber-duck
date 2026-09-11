# How to install

## Claude Code

### Install

```bash
claude plugin marketplace add miteshpandey/rubber-duck
claude plugin install rubber-duck@rubber-duck
```

Restart Claude Code, then invoke it before any request you want to think through:

```
/rubber-duck
```

### Verify

```bash
claude plugin list
```

You should see `rubber-duck` listed and enabled.

### Use

Invoke `/rubber-duck`, then describe what you want to build. The agent asks three
questions and waits. Answer them, or say "just write it" at any point to skip
straight to code.

### Update

```bash
claude plugin uninstall rubber-duck
claude plugin marketplace remove rubber-duck
claude plugin marketplace add miteshpandey/rubber-duck
claude plugin install rubber-duck@rubber-duck
```

### Uninstall

```bash
claude plugin uninstall rubber-duck
```

## Manual (any tool that imports a Markdown skill)

The whole skill is one file: [skills/rubber-duck/SKILL.md](skills/rubber-duck/SKILL.md).
Any assistant that accepts a Markdown skill or a system-prompt snippet can use it.
Download that file and import it however your tool supports, or paste its body in
as a manual instruction and trigger it yourself when you want it.

Note: this skill is intentionally manual. It does not auto-trigger. It shapes a
response only when you invoke it.
