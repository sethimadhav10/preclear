#!/usr/bin/env python3
"""preclear / workset hook — Claude's own curated context survives /compact and /clear.

Inspired by "Context Language Models" (Shao et al., arXiv:2609.37725): let the model manage its
own context as a file, instead of a harness summary deciding what survives. Claude Code doesn't
let the model rewrite its live window, so this is the closest buildable version:

  - the model keeps ~/.claude/workset/<session_id>.md, rewritten IN PLACE (workset skill)
  - PostToolUse / UserPromptSubmit: a context-size readout at 50% and 80% (models are bad at
    knowing how full their window is, so they get told)
  - SessionStart compact|clear: re-inject the workset as authoritative state
  - PreCompact: snapshot the workset · PostCompact: keep the harness summary for comparison

Contract: fast, silent on failure, ALWAYS exits 0. Writes only inside the workset directory.
Standard library only.

Environment knobs:
  WORKSET_DIR     where files live            (default $CLAUDE_CONFIG_DIR/workset or ~/.claude/workset)
  WORKSET_WINDOW  context window in tokens    (default 200000; auto-bumps to 1000000 once a
                                               session is seen above 200K)
"""
import json, os, shutil, subprocess, sys, time

CONFIG = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.join(os.path.expanduser("~"), ".claude")
DIR = os.environ.get("WORKSET_DIR") or os.path.join(CONFIG, "workset")
PIDDIR = os.path.join(DIR, ".pid")
WINDOW = int(os.environ.get("WORKSET_WINDOW", "200000"))
BIG_WINDOW = 1_000_000
BANDS = (50, 80)                     # % of window
MAX_INJECT = 9000                    # hook output is capped at 10,000 chars


def claude_pid():
    """Nearest ancestor process that is Claude Code. Stable across /clear, unlike session_id."""
    p = os.getppid()
    for _ in range(10):
        try:
            out = subprocess.run(["ps", "-o", "ppid=", "-o", "args=", "-p", str(p)],
                                 capture_output=True, text=True, timeout=1).stdout.strip()
        except Exception:
            return None
        if not out:
            return None
        parts = out.split()
        ppid, args = parts[0], parts[1:]
        exe = os.path.basename(args[0]) if args else ""
        if exe == "claude" or (exe.startswith("node") and any("claude" in a for a in args[1:3])):
            return p
        try:
            p = int(ppid)
        except ValueError:
            return None
        if p <= 1:
            return None
    return None


def context_tokens(transcript):
    """Input-side tokens of the last assistant turn, read from the transcript tail."""
    try:
        with open(transcript, "rb") as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - 400_000))
            tail = f.read().decode("utf-8", "ignore").splitlines()
    except Exception:
        return None
    for line in reversed(tail):
        if '"usage"' not in line:
            continue
        try:
            u = json.loads(line)["message"]["usage"]
            return (u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
                    + u.get("cache_read_input_tokens", 0))
        except Exception:
            continue
    return None


def emit(event, text):
    print(json.dumps({"hookSpecificOutput": {"hookEventName": event, "additionalContext": text}}))


def read(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


def write(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def session_start(d, sid, ws):
    pid = claude_pid()                   # the ps walk happens only here; PostToolUse stays cheap
    pidfile = os.path.join(PIDDIR, str(pid)) if pid else None
    source = d.get("source", "")
    prev = read(pidfile).strip() if pidfile else ""
    linked = False
    # The /preclear resume link starts a NEW window with WORKSET_FROM=<old session id>.
    # Carry that workset over exactly as a /clear would — only if the named file exists.
    wf = os.environ.get("WORKSET_FROM", "").strip()
    if source == "startup" and wf and wf != sid and "/" not in wf \
            and os.path.exists(os.path.join(DIR, f"{wf}.md")):
        prev, source, linked = wf, "clear", True
    if source in ("clear", "compact") and prev and prev != sid:    # /clear gives a new session_id
        old = os.path.join(DIR, f"{prev}.md")
        if os.path.exists(old) and not os.path.exists(ws):
            shutil.copyfile(old, ws)                               # copy, never move
    if pidfile:
        write(pidfile, sid)
    tp = d.get("transcript_path", "")
    if tp:                               # so a cleared session can find the old transcript
        write(os.path.join(DIR, f".{sid}.transcript"), tp)
    old_tp = read(os.path.join(DIR, f".{prev}.transcript")).strip() if prev and prev != sid else ""
    if not old_tp and source == "compact":
        old_tp = tp                      # same session: the pre-compact turns are in its own file
    body = read(ws)
    if source in ("compact", "clear") and body.strip():
        how = ("a compaction" if source == "compact" else
               "the previous window (opened from the /preclear resume link)" if linked else "/clear")
        emit("SessionStart", (
            f"WORKSET — your own curated context from before {how}, reloaded from {ws}.\n"
            "Treat it as the authoritative state: where it disagrees with a compaction summary, "
            "the workset wins. Keep rewriting it in place (workset skill).\n\n"
            + body[:MAX_INJECT]
            + (f"\n\nThe full {'previous' if linked else 'pre-' + source} conversation is still on disk: "
               f"{old_tp} — grep it for a detail the workset dropped; never read it whole."
               if old_tp else "")))
    else:
        emit("SessionStart",
             f"Workset file for this session: {ws} (workset skill: keep it current, rewrite in place).")


def context_readout(d, sid, ws, event):
    tp = d.get("transcript_path", "")
    if os.path.basename(tp) != f"{sid}.jsonl":     # subagent call: not the parent's window
        return
    tok = context_tokens(tp)
    if not tok:
        return
    window = WINDOW
    if tok > window and window < BIG_WINDOW:       # can only happen on a 1M-token window
        window = BIG_WINDOW
    pct = 100 * tok // window
    bandfile = os.path.join(DIR, f".{sid}.band")
    try:
        last = int(read(bandfile) or 0)
    except ValueError:
        last = 0
    band = max([b for b in BANDS if pct >= b], default=0)
    if band < last:                      # context shrank (a compaction) — re-arm
        write(bandfile, str(band))
        return
    if band <= last:
        return
    write(bandfile, str(band))
    have = os.path.exists(ws) and read(ws).strip()
    msg = f"[context: ~{tok // 1000}K / {window // 1000}K tokens, {pct}%] "
    if band >= 80:
        msg += (f"Auto-compact is near. Rewrite {ws} NOW so it carries every open decision, verified "
                "number and next action. Then, at a natural pause, tell the user in one line that the "
                "workset is current and that /preclear then /clear will carry it over.")
    else:
        msg += (f"{'Rewrite' if have else 'Start'} your workset at {ws} now — in place, under ~3 KB, "
                "per the workset skill. Drop what is finished; keep what a fresh you would need.")
    emit(event, msg)


def main():
    try:
        d = json.load(sys.stdin)
    except Exception:
        return
    event = d.get("hook_event_name", "")
    sid = d.get("session_id") or ""
    if not sid or "/" in sid:
        return
    os.makedirs(PIDDIR, exist_ok=True)
    ws = os.path.join(DIR, f"{sid}.md")

    if event == "SessionStart":
        session_start(d, sid, ws)
    elif event in ("PostToolUse", "UserPromptSubmit"):
        context_readout(d, sid, ws, event)
    elif event == "PreCompact":
        if os.path.exists(ws):
            shutil.copyfile(ws, os.path.join(DIR, f"{sid}.precompact-{int(time.time())}.md"))
    elif event == "PostCompact":
        summary = d.get("compact_summary") or ""
        if summary:
            write(os.path.join(DIR, f"{sid}.summary-{int(time.time())}.md"), summary)
        try:
            os.remove(os.path.join(DIR, f".{sid}.band"))
        except Exception:
            pass


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
