"""
Path: monitor.py
System and AWS health monitor for AI-Admin-Agent.
Monitors CPU, memory, and disk usage in real-time, and triggers incidents when thresholds are exceeded.
"""

import psutil
import time
import os
from typing import Callable, Dict, Any
from configs.defaults import Defaults
from tools.aws_tool import AWSTool

class Monitor:
    def __init__(self, config: Defaults, on_incident: Callable[[Dict[str, Any]], None]):
        self.config = config
        self.on_incident = on_incident
        self._running = False

    def _check_system(self):
        """Check local system metrics."""
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory().percent
        disk = psutil.disk_usage("/").percent

        # 🩺 Live metric logging
        print(f"📊 CPU: {cpu:.1f}% | MEM: {mem:.1f}% | DISK: {disk:.1f}%", end="\r")

        # 🚨 Trigger incidents
        if cpu >= self.config.CPU_THRESHOLD_PERCENT:
            print(f"\n🚨 CPU threshold exceeded: {cpu}%")
            self.on_incident({"type": "cpu_high", "value": cpu})

        if mem >= self.config.MEM_THRESHOLD_PERCENT:
            print(f"\n🚨 Memory threshold exceeded: {mem}%")
            self.on_incident({"type": "memory_high", "value": mem})

        if disk >= self.config.DISK_THRESHOLD_PERCENT:
            print(f"\n🚨 Disk threshold exceeded: {disk}%")
            self.on_incident({"type": "disk_high", "value": disk})

    def _check_aws(self):
        """Optionally check AWS EC2 instances."""
        try:
            aws = AWSTool(region=os.getenv("AWS_REGION", "eu-north-1"), dry_run=True)
            instances = aws.list_instances().get("instances", [])
            for i in instances:
                metrics = aws.get_cpu_metrics(i["id"])
                if metrics.get("metrics"):
                    avg = metrics["metrics"][-1].get("Average", 0)
                    if avg > 80:
                        print(f"\n⚠️ EC2 {i['id']} CPU high: {avg}%")
                        self.on_incident({
                            "type": "ec2_cpu_high",
                            "instance_id": i["id"],
                            "value": avg,
                            "description": f"High CPU ({avg}%) on EC2 {i['id']}"
                        })
        except Exception as e:
            print(f"\n[AWS Monitor Error] {e}")

    def _check_all(self):
        """Run both system and AWS checks."""
        self._check_system()
        self._check_aws()

    def run_forever(self, poll_interval: int = None):
        """Continuous monitoring loop with live output."""
        if poll_interval is None:
            poll_interval = self.config.POLL_INTERVAL_SECONDS
        self._running = True
        print(f"📡 Monitoring every {poll_interval}s (Ctrl+C to stop)")
        try:
            while self._running:
                self._check_all()
                time.sleep(poll_interval)
        except KeyboardInterrupt:
            self._running = False
            print("\n🛑 Monitoring stopped.")

    def stop(self):
        """Stop the monitoring loop."""
        self._running = False
