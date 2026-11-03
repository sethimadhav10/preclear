#!/usr/bin/env python3
"""Make a one-click resume link for a /preclear'd session and print it.

usage: python3 resume_link.py <session_id>

  <session_id> = the name of the workset file the SessionStart hook printed
                 (~/.claude/workset/<session_id>.md).

Writes ~/.claude/workset/<session_id>.resume.command (macOS: Cmd-click the file:// link or
double-click it in Finder) or <session_id>.resume.sh (Linux: run it). It starts a FRESH Claude
Code window in the session's own folder, and the workset hook loads the curated workset into it
(WORKSET_FROM). It also prints the command that reopens the WHOLE old chat instead.
Touches nothing outside the workset directory. Standard library only.
"""
import json, os, re, shlex, shutil, sys

CONFIG = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude")
DIR = os.environ.get("WORKSET_DIR") or os.path.join(CONFIG, "workset")


def session_cwd(sid):
    """The folder the session was launched from. --resume only finds a session from there."""
    tp = ""
    try:
        tp = open(os.path.join(DIR, f".{sid}.transcript")).read().strip()
    except Exception:
        pass
    if not tp or not os.path.exists(tp):
        root = os.path.join(CONFIG, "projects")
        for d in (os.listdir(root) if os.path.isdir(root) else []):
            cand = os.path.join(root, d, f"{sid}.jsonl")
            if os.path.exists(cand):
                tp = cand
                break
    if tp and os.path.exists(tp):
        with open(tp, encoding="utf-8", errors="ignore") as f:
            for _, line in zip(range(200), f):
                try:
                    cwd = json.loads(line).get("cwd")
                except Exception:
                    continue
                if cwd:
                    return cwd, tp
    return None, tp


def main():
    if len(sys.argv) != 2 or "/" in sys.argv[1]:
        sys.exit("usage: resume_link.py <session_id>")
    sid = sys.argv[1]
    ws = os.path.join(DIR, f"{sid}.md")
    if not os.path.exists(ws):
        sys.exit(f"no workset at {ws} — run the /preclear steps first")
    cwd, tp = session_cwd(sid)
    if not cwd:
        sys.exit(f"could not find the launch folder for {sid} (transcript: {tp or 'not found'})")
    claude = shutil.which("claude") or "claude"
    q = shlex.quote
    mac = sys.platform == "darwin"
    path = os.path.join(DIR, f"{sid}.resume.{'command' if mac else 'sh'}")
    prompt = (f"Resuming after /preclear. Workset: {ws} — if it was not injected above, read it now; "
              "it is authoritative. Confirm where we stand in two lines, then wait for me.")
    with open(path, "w") as f:
        f.write("#!/bin/bash -l\n"
                f"# /preclear resume link for session {sid}\n"
                f"cd {q(cwd)} || exit 1\n"
                f"WORKSET_FROM={q(sid)} exec {q(claude)} {q(prompt)}\n")
    os.chmod(path, 0o755)
    if mac:
        print(f"Fresh window, workset loaded:  file://{path}")
    else:
        print(f"Fresh window, workset loaded:  bash {q(path)}")
    print(f"Whole old chat instead:        cd {q(cwd)} && claude --resume {sid}")
    # After a /clear this session holds only the post-clear part; walk back to the chats before it.
    seen, cur = {sid}, tp
    while cur and os.path.exists(cur):
        try:
            m = re.search(r'conversation is still on disk: (\S+?)\.jsonl',
                          open(cur, errors="ignore").read(2_000_000))
        except Exception:
            m = None
        if not m or os.path.basename(m.group(1)) in seen:
            break
        prev = os.path.basename(m.group(1))
        seen.add(prev)
        print(f"Chat before that /clear:       cd {q(cwd)} && claude --resume {prev}")
        cur = m.group(1) + ".jsonl"


if __name__ == "__main__":
    main()
