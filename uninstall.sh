#!/usr/bin/env bash
# Removes the hook wiring from settings.json (backup first) and the skills install.sh added.
# Leaves ~/.claude/workset/ (your worksets) in place.
set -euo pipefail
C="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
cp -p "$C/settings.json" "$C/settings.json.bak-preclear-uninstall-$(date +%Y%m%d-%H%M%S)"
python3 - "$C/settings.json" <<'PY'
import json, sys
p = sys.argv[1]; s = json.load(open(p)); h = s.get("hooks", {})
for ev in list(h):
    h[ev] = [m for m in h[ev] if not any("workset.py" in x.get("command", "") for x in m.get("hooks", []))]
    if not h[ev]: del h[ev]
json.dump(s, open(p, "w"), indent=2)
PY
rm -f "$C/hooks/workset.py"
for s in workset preclear precompact; do
  if [ -f "$C/skills/$s/.preclear" ]; then rm -rf "$C/skills/$s"; fi
done
echo "✔ uninstalled (worksets kept in $C/workset/)"
