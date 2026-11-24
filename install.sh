#!/usr/bin/env bash
# Manual install (no plugin system): copies the hook + skills into ~/.claude and wires the hook
# into ~/.claude/settings.json. Backs up settings.json first. Idempotent. Undo with ./uninstall.sh.
set -euo pipefail
SRC="$(cd "$(dirname "$0")" && pwd)"
C="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
command -v python3 >/dev/null || { echo "python3 is required"; exit 1; }
mkdir -p "$C/hooks" "$C/skills" "$C/workset/.pid"
[ -f "$C/settings.json" ] || echo '{}' > "$C/settings.json"
BK="$C/settings.json.bak-preclear-$(date +%Y%m%d-%H%M%S)"
cp -p "$C/settings.json" "$BK"
cp "$SRC/hooks/workset.py" "$C/hooks/workset.py"; chmod +x "$C/hooks/workset.py"
for s in workset preclear postclear precompact; do
  if [ -e "$C/skills/$s" ] && [ ! -f "$C/skills/$s/.preclear" ]; then
    echo "skip skill $s: $C/skills/$s already exists and isn't ours"; continue
  fi
  mkdir -p "$C/skills/$s"; cp -R "$SRC/skills/$s/." "$C/skills/$s/"; touch "$C/skills/$s/.preclear"
done
python3 - "$C/settings.json" "$C/hooks/workset.py" <<'PY'
import json, sys
path, hook = sys.argv[1], sys.argv[2]
s = json.load(open(path))
cmd = f'python3 "{hook}"'
h = s.setdefault("hooks", {})
for ev in ("SessionStart", "UserPromptSubmit", "PostToolUse", "PreCompact", "PostCompact"):
    lst = h.setdefault(ev, [])
    if not any("workset.py" in x.get("command", "") for m in lst for x in m.get("hooks", [])):
        lst.append({"hooks": [{"type": "command", "command": cmd, "timeout": 5}]})
json.dump(s, open(path, "w"), indent=2)
PY
python3 -c "import json,sys;json.load(open(sys.argv[1]))" "$C/settings.json"
echo '{"hook_event_name":"SessionStart","session_id":"install-probe","source":"startup"}' \
  | WORKSET_DIR="$(mktemp -d)" python3 "$C/hooks/workset.py" | grep -q "install-probe.md" \
  && echo "✔ hook answers" || { echo "✘ hook did not answer — restoring settings"; cp -p "$BK" "$C/settings.json"; exit 1; }
echo "✔ installed. settings backup: $BK"
echo "  Open a NEW Claude Code session; it should print 'Workset file for this session: …'."
echo "  On a 1M-token context window: export WORKSET_WINDOW=1000000"
