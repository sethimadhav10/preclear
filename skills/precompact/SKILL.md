---
name: precompact
description: Write the paste-back prompt that carries a long session across a context compaction without losing what was expensive to learn. Use when the user says they are about to compact, asks for a handover, says "give me something to paste back", or invokes /precompact. Also use unprompted when a session has run long and holds findings that would be costly to re-derive.
---

# Precompact

The next session wakes up with your files and none of your memory. It will re-derive whatever you do
not hand it, and it will re-derive it WRONG in exactly the places you got it wrong the first time.

Write for a competent stranger who has your disk and none of your context.

## Before writing the prompt, make the work durable

A paste-back prompt is a pointer, not a store. First confirm the substance is on disk:
- the state/plan document is current, including today's reversals
- every measured number that cost real time is written down with what it describes
- sealed or hashed artefacts are in a durable location, not a session-temporary scratch directory
- memory files updated for anything that outlives this project

Then the prompt can be short, because it points rather than carries.

## The shape

**1. What this is, in two lines.** System, stakes, current posture (running? stopped? holding money?).

**2. READ THESE FIRST, in order.** Absolute paths. Three files maximum, ranked. Say what each is for.
The single most common failure is a fresh session reading the wrong document and confidently acting on
a superseded plan.

**3. THE NUMBERS THAT MUST NOT BE RE-DERIVED.** The handful of measurements that cost hours, each with
the object it describes. Not "IC 0.0768" but "0.0768 is the certified metric OF THE OLD TRAINING FILE".
A number without its object is how the next session measures the wrong thing.

**4. DIRECTION-OF-FIX TRAPS.** For every asymmetric repair, state which side is correct and which is
stale, in capitals. "For X the SERVING side is right and TRAINING is stale. Move training. NEVER the
reverse." Getting this backwards undoes real work and looks like progress while doing it.

**5. WHAT WILL BITE TODAY.** Environment facts that are invisible from the files: blackout windows,
hosts that must stay read-only, commands that must never be run and why, scheduling that constrains
the work, anything currently broken.

**6. HOW THE OPERATOR WORKS.** Review discipline, what they approve personally, communication style,
what they have already ruled on so it is not re-litigated.

**7. THE RETRACTION RECORD.** Count the times you were wrong and name the SHAPE, not the instances.
"Wrong sixteen times, every one the same shape: trusting a document or a number without asking what
object it describes." This is the highest-value line in the whole prompt. It calibrates the next
session's confidence, and without it that session starts fresh and overconfident on the same ground.

**8. THE NEXT CONCRETE ACTION.** One instruction. Not a menu.

## Rules

- **Point, don't summarise.** If it is on disk, give the path. Prose in a prompt goes stale; a path
  stays true.
- **Every claim keeps its tag** — verified / reported / assumed. An untagged claim reads as verified,
  and a fresh session has no way to tell.
- **Include what you got wrong**, especially recent reversals. A prompt that carries only conclusions
  hands the next session your errors dressed as findings.
- **Name the traps in capitals.** They will be skimmed. Make the dangerous ones survive skimming.
- **Do not carry the narrative.** No "we then investigated". The next session does not need the story,
  it needs the state.
- **Keep it inside a screen or two.** Length competes with the files it points at, and loses.

## Never

- Never let the prompt become the record. The files are the record.
- Never carry a conclusion without the measurement or the path behind it.
- Never omit the open decisions, or the next session will make them silently.
- Never leave out what is currently broken because it is embarrassing. That is the part that costs
  most to rediscover.
