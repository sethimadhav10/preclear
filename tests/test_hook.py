"""End-to-end tests for hooks/workset.py and skills/preclear/resume_link.py.

Each test feeds the hook the same JSON Claude Code sends on stdin, in a throwaway WORKSET_DIR,
and checks what comes back. Standard library only:  python3 -m unittest discover tests -v
"""
import json, os, shutil, subprocess, sys, tempfile, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOK = os.path.join(ROOT, "hooks", "workset.py")
RESUME = os.path.join(ROOT, "skills", "preclear", "resume_link.py")


def put(path, text):
    with open(path, "w") as f:
        f.write(text)


class Hook(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = os.path.join(self.tmp.name, "workset")
        self.env = dict(os.environ, WORKSET_DIR=self.dir)
        self.env.pop("WORKSET_WINDOW", None)
        self.env.pop("WORKSET_FROM", None)

    def tearDown(self):
        self.tmp.cleanup()

    def run_hook(self, payload, env=None, via=None):
        cmd = [sys.executable, HOOK] if via is None else via
        r = subprocess.run(cmd, input=payload if isinstance(payload, str) else json.dumps(payload),
                           capture_output=True, text=True, env=env or self.env, timeout=20)
        self.assertEqual(r.returncode, 0, r.stderr)
        if not r.stdout.strip():
            return None
        return json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"]

    def transcript(self, sid, tokens, cwd="/tmp"):
        path = os.path.join(self.tmp.name, f"{sid}.jsonl")
        with open(path, "w") as f:
            f.write(json.dumps({"type": "user", "cwd": cwd}) + "\n")
            f.write(json.dumps({"type": "assistant", "message": {"usage": {
                "input_tokens": 10, "cache_creation_input_tokens": tokens - 10,
                "cache_read_input_tokens": 0}}}) + "\n")
        return path

    def workset(self, sid, body):
        os.makedirs(self.dir, exist_ok=True)
        with open(os.path.join(self.dir, f"{sid}.md"), "w") as f:
            f.write(body)

    # --- SessionStart -----------------------------------------------------------------------

    def test_startup_prints_path(self):
        out = self.run_hook({"hook_event_name": "SessionStart", "session_id": "s1", "source": "startup"})
        self.assertIn(os.path.join(self.dir, "s1.md"), out)

    def test_compact_reinjects_workset_as_authoritative(self):
        self.workset("s1", "# Next\nNONCE-7f3a run the migration")
        out = self.run_hook({"hook_event_name": "SessionStart", "session_id": "s1", "source": "compact",
                             "transcript_path": self.transcript("s1", 1000)})
        self.assertIn("NONCE-7f3a", out)
        self.assertIn("the workset wins", out)
        self.assertIn("s1.jsonl", out)          # points at the pre-compact transcript

    def test_clear_carries_workset_to_new_session_id(self):
        # /clear gives a new session_id inside the SAME Claude process. Fake that process: one
        # long-lived bash started under the name "claude" (exec -a) runs the hook for both events,
        # the way Claude Code does. (A python symlink won't do: macOS framework Python re-execs
        # and loses argv[0]; a copied /bin/bash gets killed by macOS.)
        p1, p2 = (os.path.join(self.tmp.name, f"p{i}.json") for i in (1, 2))
        o1, o2 = (os.path.join(self.tmp.name, f"o{i}.txt") for i in (1, 2))
        put(p1, json.dumps({"hook_event_name": "SessionStart", "session_id": "old", "source": "startup",
                            "transcript_path": self.transcript("old", 1000)}))
        put(p2, json.dumps({"hook_event_name": "SessionStart", "session_id": "new", "source": "clear"}))
        inner = ('"$0" "$1" < "$2" > "$3"; printf "# Next\\nNONCE-c1ea" > "$4"; '
                 '"$0" "$1" < "$5" > "$6"; echo $$')
        bash = shutil.which("bash") or "/bin/bash"
        r = subprocess.run([bash, "-c", 'exec -a claude "$0" -c "$@"', bash, inner, sys.executable, HOOK,
                            p1, o1, os.path.join(self.dir, "old.md"), p2, o2],
                           capture_output=True, text=True, env=self.env, timeout=30)
        self.assertEqual(r.returncode, 0, r.stderr)
        fake_pid = r.stdout.strip()
        # Key the check on the FAKE's pid, so a real Claude Code ancestor (when the tests run
        # inside a Claude session) can't make this pass by accident.
        self.assertEqual(os.listdir(os.path.join(self.dir, ".pid")), [fake_pid],
                         "hook did not map the session to the fake claude process")
        with open(o2) as f:
            out = json.loads(f.read())["hookSpecificOutput"]["additionalContext"]
        self.assertIn("NONCE-c1ea", out)
        self.assertIn("old.jsonl", out)
        self.assertTrue(os.path.exists(os.path.join(self.dir, "old.md")), "old workset must be copied, not moved")

    def test_resume_link_env_loads_old_workset_into_fresh_window(self):
        self.workset("old", "# Next\nNONCE-11nk")
        env = dict(self.env, WORKSET_FROM="old")
        out = self.run_hook({"hook_event_name": "SessionStart", "session_id": "fresh", "source": "startup"}, env=env)
        self.assertIn("NONCE-11nk", out)
        self.assertIn("resume link", out)

    def test_resume_env_with_missing_or_unsafe_id_is_ignored(self):
        for bad in ("nope", "../etc"):
            env = dict(self.env, WORKSET_FROM=bad)
            out = self.run_hook({"hook_event_name": "SessionStart", "session_id": "fresh", "source": "startup"}, env=env)
            self.assertIn("Workset file for this session", out)

    # --- context readout --------------------------------------------------------------------

    def readout(self, sid, tokens, env=None):
        return self.run_hook({"hook_event_name": "PostToolUse", "session_id": sid,
                              "transcript_path": self.transcript(sid, tokens)}, env=env)

    def test_quiet_below_half(self):
        self.assertIsNone(self.readout("s1", 90_000))

    def test_fifty_percent_nudge_fires_once(self):
        out = self.readout("s1", 110_000)
        self.assertIn("~110K / 200K tokens, 55%", out)
        self.assertIn("Start your workset", out)
        self.assertIsNone(self.readout("s1", 120_000), "must not repeat inside the same band")

    def test_eighty_percent_nudge(self):
        self.readout("s1", 110_000)
        out = self.readout("s1", 170_000)
        self.assertIn("Auto-compact is near", out)
        self.assertIn("/preclear", out)

    def test_big_window_auto_detected(self):
        out = self.readout("s1", 600_000)
        self.assertIn("/ 1000K tokens, 60%", out)

    def test_window_env_knob(self):
        out = self.readout("s1", 510_000, env=dict(self.env, WORKSET_WINDOW="1000000"))
        self.assertIn("/ 1000K tokens, 51%", out)

    def test_subagent_transcript_is_ignored(self):
        tp = self.transcript("agent-xyz", 190_000)
        out = self.run_hook({"hook_event_name": "PostToolUse", "session_id": "s1", "transcript_path": tp})
        self.assertIsNone(out)

    # --- compaction bookkeeping -------------------------------------------------------------

    def test_precompact_snapshots_and_postcompact_keeps_summary(self):
        self.workset("s1", "body")
        self.run_hook({"hook_event_name": "PreCompact", "session_id": "s1"})
        self.run_hook({"hook_event_name": "PostCompact", "session_id": "s1", "compact_summary": "SUMMARY-X"})
        files = os.listdir(self.dir)
        self.assertTrue(any(f.startswith("s1.precompact-") for f in files), files)
        self.assertTrue(any(f.startswith("s1.summary-") for f in files), files)

    # --- must never fail loudly -------------------------------------------------------------

    def test_garbage_input_exits_zero_silently(self):
        for payload in ("", "not json", "{}", json.dumps({"hook_event_name": "SessionStart", "session_id": "a/b"})):
            self.assertIsNone(self.run_hook(payload))


class ResumeLink(unittest.TestCase):
    def test_writes_link_and_resume_command(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = os.path.join(tmp, "workset")
            os.makedirs(d)
            put(os.path.join(d, "s1.md"), "x")
            tp = os.path.join(tmp, "s1.jsonl")
            put(tp, json.dumps({"cwd": tmp}) + "\n")
            put(os.path.join(d, ".s1.transcript"), tp)
            r = subprocess.run([sys.executable, RESUME, "s1"], capture_output=True, text=True,
                               env=dict(os.environ, WORKSET_DIR=d), timeout=20)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("claude --resume s1", r.stdout)
            script = [f for f in os.listdir(d) if f.startswith("s1.resume.")]
            self.assertEqual(len(script), 1, os.listdir(d))
            with open(os.path.join(d, script[0])) as f:
                body = f.read()
            self.assertIn("WORKSET_FROM=s1", body)
            self.assertIn(f"cd {tmp}", body)

    def test_refuses_without_workset(self):
        with tempfile.TemporaryDirectory() as d:
            r = subprocess.run([sys.executable, RESUME, "missing"], capture_output=True, text=True,
                               env=dict(os.environ, WORKSET_DIR=d), timeout=20)
            self.assertNotEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
