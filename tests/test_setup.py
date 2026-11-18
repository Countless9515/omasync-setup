import os
import subprocess
import tempfile
import unittest
from pathlib import Path

SETUP = Path(__file__).resolve().parents[1] / "setup.sh"
REPO = "https://github.com/Countless9515/omarchy-profile.git"


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home = self.root / "home"
        self.bin = self.root / "bin"
        self.home.mkdir()
        self.bin.mkdir()
        self.log = self.root / "log"
        self.cmd("mise", 'if [[ "$1" == which ]]; then command -v gh; fi')
        self.cmd("gh", '''
if [[ "$1" == auth && "$2" == status ]]; then
  [[ -f "$HOME/authorized" ]]
elif [[ "$1" == auth && "$2" == login ]]; then
  touch "$HOME/authorized"
elif [[ "$1" == repo && "$2" == clone ]]; then
  mkdir -p "$4/.git"
  printf '%s\\n' '#!/bin/sh' 'echo "restore:$*" >> "$TEST_LOG"' > "$4/install.sh"
fi
''')
        self.cmd("git", '''
if [[ "$*" == *"remote get-url origin"* ]]; then printf '%s\\n' 'https://github.com/Countless9515/omarchy-profile.git'; fi
''')

    def cmd(self, name, body):
        path = self.bin / name
        path.write_text(f'#!/usr/bin/env bash\nset -euo pipefail\nprintf "%s\\n" "{name}:$*" >> "$TEST_LOG"\n{body}\n')
        path.chmod(0o755)

    def run_setup(self):
        env = os.environ.copy()
        env.update(HOME=str(self.home), XDG_CACHE_HOME=str(self.home / ".cache"), PATH=f"{self.bin}:{env['PATH']}", TEST_LOG=str(self.log))
        return subprocess.run(["bash", str(SETUP)], env=env, text=True, capture_output=True)

    def test_new_laptop_authenticates_clones_and_launches_restore(self):
        result = self.run_setup()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        commands = self.log.read_text()
        self.assertIn("mise:use -g gh", commands)
        self.assertIn("gh:auth login --hostname github.com --git-protocol https --web", commands)
        self.assertIn("gh:auth setup-git --hostname github.com", commands)
        self.assertIn("gh:repo clone https://github.com/Countless9515/omarchy-profile.git", commands)
        self.assertIn("restore:laptop", commands)
        self.assertNotIn("oauth_token", commands)

    def test_retry_fetches_existing_clone_instead_of_cloning_again(self):
        first = self.run_setup()
        self.assertEqual(first.returncode, 0, first.stderr)
        self.log.write_text("")
        second = self.run_setup()
        self.assertEqual(second.returncode, 0, second.stderr)
        commands = self.log.read_text()
        self.assertNotIn("gh:repo clone", commands)
        self.assertIn("git:-C", commands)
        self.assertIn("fetch", commands)
        self.assertIn("restore:laptop", commands)

    def test_private_clone_is_not_world_readable(self):
        result = self.run_setup()
        self.assertEqual(result.returncode, 0, result.stderr)
        cache = self.home / ".cache/omasync-setup"
        self.assertEqual(cache.stat().st_mode & 0o077, 0)
        self.assertEqual((cache / "install.sh").stat().st_mode & 0o077, 0)

    def test_interrupted_clone_can_be_retried(self):
        self.cmd("gh", '''
if [[ "$1" == auth && "$2" == status ]]; then [[ -f "$HOME/authorized" ]];
elif [[ "$1" == auth && "$2" == login ]]; then touch "$HOME/authorized";
elif [[ "$1" == repo && "$2" == clone ]]; then
  if [[ -f "$HOME/fail-once" ]]; then
    rm "$HOME/fail-once"
    mkdir -p "$4"
    printf 'partial' > "$4/unfinished"
    exit 1
  fi
  mkdir -p "$4/.git"
  printf '%s\\n' '#!/bin/sh' 'echo "restore:$*" >> "$TEST_LOG"' > "$4/install.sh"
fi
''')
        (self.home / "fail-once").touch()
        first = self.run_setup()
        self.assertNotEqual(first.returncode, 0)
        self.assertFalse((self.home / ".cache/omasync-setup").exists())
        second = self.run_setup()
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertIn("restore:laptop", self.log.read_text())

    def test_different_cached_repo_is_never_overwritten(self):
        first = self.run_setup()
        self.assertEqual(first.returncode, 0, first.stderr)
        self.cmd("git", '''
if [[ "$*" == *"remote get-url origin"* ]]; then printf '%s\\n' 'https://example.org/other.git'; fi
''')
        self.log.write_text("")
        second = self.run_setup()
        self.assertNotEqual(second.returncode, 0)
        self.assertNotIn("restore:laptop", self.log.read_text())


if __name__ == "__main__":
    unittest.main()
