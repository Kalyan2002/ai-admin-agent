"""
PowerShell execution wrapper. On Windows, uses 'powershell' or 'pwsh' if available.
"""
import subprocess
from typing import Dict, Any, List

class PowerShellTool:
    def __init__(self, whitelist: List[str], dry_run: bool = True):
        self.whitelist = whitelist
        self.dry_run = dry_run

    def _is_allowed(self, script: str) -> bool:
        # Placeholder: basic allow if it contains whitelisted cmdlets / startswith allowed tokens
        for w in self.whitelist:
            if script.strip().startswith(w):
                return True
        return False

    def execute(self, script: str, timeout: int = 60) -> Dict[str, Any]:
        action = {"script": script, "dry_run": self.dry_run}
        if not self._is_allowed(script):
            return {"error": "script_not_whitelisted", "action": action}

        if self.dry_run:
            return {"simulated": True, "action": action}

        try:
            # Use pwsh if installed, fallback to powershell
            for shell in ("pwsh", "powershell"):
                try:
                    completed = subprocess.run([shell, "-Command", script], capture_output=True, text=True, timeout=timeout)
                    return {"stdout": completed.stdout, "stderr": completed.stderr, "returncode": completed.returncode, "action": action}
                except FileNotFoundError:
                    continue
            return {"error": "no_powershell_found", "action": action}
        except Exception as e:
            return {"error": str(e), "action": action}
