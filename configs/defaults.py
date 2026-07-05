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
