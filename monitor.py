"""
Path: monitor.py
Simple psutil-based monitor for CPU, memory, and disk.
Triggers incidents when thresholds are exceeded.
"""
import psutil
import time
import os
from typing import Callable, Dict, Any
from configs.defaults import Defaults
class Monitor:
    def __init__(self, config: Defaults, on_incident: Callable[[Dict[str, Any]], None]):
        self.config = config
        self.on_incident = on_incident
        self._running = False

    def _check(self):
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory().percent
        disk = psutil.disk_usage("/").percent

        if cpu >= self.config.CPU_THRESHOLD_PERCENT:
            self.on_incident({"type": "cpu_high", "value": cpu})

        if mem >= self.config.MEM_THRESHOLD_PERCENT:
            self.on_incident({"type": "memory_high", "value": mem})

        if disk >= self.config.DISK_THRESHOLD_PERCENT:
            self.on_incident({"type": "disk_high", "value": disk})

        # Check AWS EC2 CPU metrics
        try:
            aws = AWSTool(region=os.getenv("AWS_REGION", "us-east-1"))
            instances = aws.list_instances().get("instances", [])

            for i in instances:
                metrics = aws.get_cpu_metrics(i["id"])
                if metrics.get("metrics"):
                    avg = metrics["metrics"][-1].get("Average", 0)
                    if avg > 80:
                        self.on_incident({
                            "type": "ec2_cpu_high",
                            "instance_id": i["id"],
                            "value": avg,
                            "description": f"High CPU ({avg}%) on instance {i['id']}"
                        })
        except Exception as e:
            print(f"[AWS Monitor Error] {e}")

    def run_forever(self, poll_interval: int = None):
        if poll_interval is None:
            poll_interval = self.config.POLL_INTERVAL_SECONDS
        self._running = True
        try:
            while self._running:
                self._check()
                time.sleep(poll_interval)
        except KeyboardInterrupt:
            self._running = False

    def stop(self):
        self._running = False
# Note: AWSTool is imported here to avoid circular dependencies
from tools.aws_tool import AWSTool 
