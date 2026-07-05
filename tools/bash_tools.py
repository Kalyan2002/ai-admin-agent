"""
Executes bash commands with dry-run and whitelist checks.
"""
import shlex
import subprocess
from typing import List, Dict, Any, Optional

class BashTool:
    def __init__(self, whitelist: List[str], dry_run: bool = True):
        self.whitelist = whitelist
        self.dry_run = dry_run

    def _is_allowed(self, command: str) -> bool:
        # minimal check: command starts with a whitelisted binary path or name
        parts = shlex.split(command)
        if not parts:
            return False
        cmd = parts[0]
        for allowed in self.whitelist:
            if cmd == allowed or cmd.startswith(allowed):
                return True
        return False

    def execute(self, command: str, timeout: int = 30) -> Dict[str, Any]:
        action = {"command": command, "dry_run": self.dry_run}
        if not self._is_allowed(command):
            return {"error": "command_not_whitelisted", "action": action}

        if self.dry_run:
            return {"simulated": True, "action": action}

        try:
            completed = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=timeout)
            return {
                "stdout": completed.stdout,
                "stderr": completed.stderr,
                "returncode": completed.returncode,
                "action": action
            }
        except Exception as e:
            return {"error": str(e), "action": action}
