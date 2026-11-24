---
name: postclear
description: Right after a /clear (or a compaction or resume), brief the user on what this session was working on and what's next, from the reloaded workset. Use when the user invokes /postclear, or asks "brief - what were you working on and what's next?", "where were we", or "what was I doing" at the start of a cleared window. Partner of /preclear.
---

# Postclear

The prompt it answers: **"brief — what were you working on and what's next?"**

`/preclear` writes the workset before a /clear. `/postclear` reads it back after the clear and turns
it into a short brief. The workset outranks any compaction summary.

## Steps

1. **Read the clock.** Run `date`. Never state a time you didn't read.
2. **Run the workset's "check first" items before writing anything.** If it says to check a process,
   a scheduled job, a tab or a file after a reload, do that first. If a job the workset expects is
   missing, recreate it from what the workset names, and never make two copies. Report what you
   found, tagged ✔ if you checked it just now.
3. **Pull the numbers from the workset, with their dates.** Say "read on <date/time>" for anything you
   didn't re-check this turn. Don't re-derive what's settled, and don't re-check everything live; the
   check-first items are enough.
4. **Do the last mile.** If a small, reversible job is only waiting on someone doing it, do it or say
   when it will get done. Don't turn it into a question.
5. **Write the brief.** Plain English, under ~250 words, in this shape:
   - one-line lead: what the session was doing, and whether anything needs the user today
   - **Where it stands**: 3–5 bullets, numbers with their source and time
   - **What's next**: what runs next and when, plus known traps coming up
   - **One decision for you** (only if one is genuinely open): the highest-leverage one, with a
     recommendation and the reason. Say the others are open in one line. Never a queue.
   - end with when the next result lands
6. **Don't change the workset** unless a check in step 2 changed the state (e.g. you recreated a job).
   If it did, rewrite the workset in place.

## Don'ts

- Don't read the old transcript whole. Grep it only for a detail the workset dropped.
- Don't turn a quiet thread into a status report. Keep it a brief.
- Don't start new work beyond the check-first items and the last mile. The user asked for a brief.
