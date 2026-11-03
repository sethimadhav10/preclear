---
name: workset
description: Keep this session's own curated context in a small file, rewritten in place, so a /compact or /clear reloads what YOU chose to keep instead of what a harness summary guessed. Use in every session that does real work — the hook prints the file's path at session start and nudges at 50% and 80% context. Also use when the user says compact, clear, handover, "save context", or "you're getting long".
---

# Workset

Your context will be cut. A compaction summary is written by something that doesn't know which
detail matters next. The fix (from *Context Language Models*, Shao et al., arXiv:2609.37725) is to
curate your own working context continuously, not to summarise it at the end.

Claude Code won't let you rewrite your live window, so you keep a file instead, and the hook
reloads it:

- **SessionStart** prints the path: `~/.claude/workset/<session_id>.md`.
- **At 50% and 80% context** the hook tells you the size. Models are bad at knowing how full they
  are, so trust the readout.
- **After a compaction or /clear** the hook re-injects the file as authoritative state. Where it
  disagrees with the compaction summary, the workset wins.

## What goes in it — state, not story

```
# Goal       — one line: what we're doing and for whom
# Decisions  — the user's decisions, in their words, dated. Undecided = OPEN — say so.
# Verified   — numbers/facts that cost time, each WITH ITS OBJECT and a tag (✔ verified · ◐ reported · ? assumed)
# Ruled out  — what was tried and failed; retractions ("said X, actually Y")
# Open       — threads in flight, running agents, what each is waiting on
# Traps      — direction-of-fix, never-run commands, live systems to keep read-only
# Next       — the single next action
# Pointers   — paths to the real records (STATE.md, plans, logs). Point, don't copy.
```

## Rules

- **Rewrite in place. Never append.** Delete what's finished. Under ~3 KB. A growing file is just a
  second, worse summary.
- **Write through.** Update it the moment a decision, a verified number, or a retraction lands, not at
  the 50% nudge. The nudge is a backstop.
- **It is a pointer, not the record.** Project state still lives in its own files. The workset says
  where to look.
- **Don't edit it on every tool call.** Rewrite at milestones. Each rewrite costs a turn.
- **Never put credentials, API keys, tokens, or customer data in it.**
- **You cannot type /clear or /compact.** At the 80% nudge, make the file current, then tell the user
  in one line that `/preclear` → `/clear` will carry it over. If they don't, auto-compact fires and
  the file is re-injected anyway.

## Related

- `/preclear` makes the workset complete and tells the user to type /clear. That is the preferred
  reset: only the workset survives, and nothing is pasted.
- `/precompact` writes a paste-back prompt for a *different* session or a teammate. The workset
  carries the *same* session across a compaction or a clear.
