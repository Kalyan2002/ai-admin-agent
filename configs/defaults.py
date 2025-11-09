# File: configs/defaults.py
"""
Default configuration values for ai-admin-agent.
Edit configs/.env or override via environment variables.
"""
from dataclasses import dataclass

@dataclass
class Defaults:
    DB_PATH: str = "logs/ai_admin.db"
    POLL_INTERVAL_SECONDS: int = 30
    CPU_THRESHOLD_PERCENT: float = 90.0
    MEM_THRESHOLD_PERCENT: float = 90.0
    DISK_THRESHOLD_PERCENT: float = 90.0
    DRY_RUN_BY_DEFAULT: bool = True
    COMMAND_WHITELIST: tuple = ("/bin/ls", "/bin/rm", "/usr/bin/du", "/usr/bin/systemctl")
# File: tools/azure_tool.py
COMMAND_WHITELIST: tuple = (
    "/bin/ls", "/bin/rm",
    "/usr/bin/du", "/usr/bin/find", "/usr/bin/awk", "/usr/bin/sort",
    "/usr/bin/head", "/usr/bin/tail", "/usr/bin/df", "/usr/bin/xargs",
    "/usr/bin/systemctl", "/usr/bin/journalctl", "/usr/sbin/logrotate",
    "/usr/bin/apt-get", "/usr/bin/docker", "/usr/bin/sudo"
)
