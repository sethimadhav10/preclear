---
name: preclear
description: Get a long session ready for /clear by writing everything worth keeping into this session's workset file, so the cleared window reloads Claude's own curated context instead of a lossy /compact summary. Nothing to copy or paste. Use when the user invokes /preclear, says they're about to clear, says "get ready to clear", "context is getting long", or when the workset hook's 80% context nudge fires and the work is at a natural pause.
---

# Preclear

`/compact` hands your context to a summariser that doesn't know which detail matters next.
`/preclear` has **you** decide. You write the handover into this session's **workset file**
(`~/.claude/workset/<session_id>.md`; the hook printed the path at session start). The user types
`/clear`, the hook reloads the file into the fresh window, and points at the old transcript in case
a dropped detail is needed later. Nothing to paste.

This is the closest Claude Code gets to a *Context Language Model* (Shao et al., arXiv:2609.37725):
the model alone decides what survives. That makes the file the **only** thing that survives, so it
has to be complete.

## Steps

1. **Make the work durable first.** The workset points to files; it doesn't replace them.
   - state / plan documents are current, including today's reversals
   - every number that cost real time is written down **with what it measures**
   - artefacts that matter are out of temp / scratch directories
   - anything that outlives this project is in memory or CLAUDE.md
2. **Rewrite the workset in place**, in this order, under ~4 KB:
   - **What this is**: two lines — the system, the stakes, the posture (running? live? read-only?)
   - **Read these first**: up to 3 absolute paths, ranked, with what each is for
   - **Numbers that must not be re-derived**: each with its object, tagged ✔ verified · ◐ reported · ? assumed
   - **Direction-of-fix traps**, in CAPITALS ("SERVING is right, TRAINING is stale — never the reverse")
   - **What will bite**: blackout windows, hosts that must stay read-only, commands never to run
   - **Decisions**: the user's own words, dated. Anything they haven't decided is OPEN — say so.
   - **Retractions**: how many times this session was wrong, and the shape those errors shared
   - **Running agents / open threads**: what each is waiting on
   - **Next action**: one instruction, not a menu
3. **Read it the way it will be read.** Re-read the file cold. Could a competent stranger with only
   this file and the disk take the next action correctly? If something lives only in your head,
   it is gone after /clear.
4. **Background agents and jobs may not survive /clear.** Wait for them, or write in the workset
   which ones need relaunching and how to check whether they are still running.
5. **Make the resume link.** Run `python3 <this skill's base directory>/resume_link.py <session_id>`.
   `<session_id>` is the workset file's name (after an earlier /clear, it's the file the hook said
   it reloaded from). It prints:
   - a **fresh-window link** (macOS `file://…resume.command`, Linux `bash …resume.sh`): opens a new
     Claude Code window in the session's folder with this workset loaded. This is the default —
     curated context, not the whole old transcript.
   - `cd <folder> && claude --resume <id>`: reopens the whole old chat instead.
   If the script errors, say so. Never hand over a link it didn't print.
6. **Tell the user in two lines:** "Workset is current (N KB) — type /clear, or close this window and
   use the link." Then paste the printed lines verbatim. You cannot type /clear yourself.

## After the clear

The hook injects the workset plus the old transcript's path. Trust the workset. If a needed detail is
missing, **grep** the old transcript for it — never read it whole; transcripts run to megabytes.

## Never

- Never append to the workset. Rewrite it.
- Never put credentials, API keys, tokens or customer data in it.
- Never say "ready to clear" before step 3 passes.
