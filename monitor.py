"""
System, AWS, and Azure health monitor for AI-Admin-Agent.
"""

import psutil
import time
import os
import datetime
from typing import Callable, Dict, Any

from configs.defaults import Defaults
from tools.aws_tool import AWSTool
from tools.azure_tool import AzureTool


class Monitor:
    def __init__(self, config: Defaults, on_incident: Callable[[Dict[str, Any]], None]):
        self.config = config
        self.on_incident = on_incident
        self._running = False

        # Prevent alert spam (cooldown per incident key)
        self._last_incident_time: Dict[str, float] = {}

        # Cloud clients (reuse)
        self.aws = AWSTool(
            region=os.getenv("AWS_REGION", "eu-north-1"),
            dry_run=True
        )

        self.azure = AzureTool(
            subscription_id=os.getenv("AZURE_SUBSCRIPTION_ID"),
            resource_group=os.getenv("AZURE_RESOURCE_GROUP"),
            dry_run=True
        )

    # ------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------

    def _should_fire(self, key: str, cooldown: int = 300) -> bool:
        now = time.time()
        last = self._last_incident_time.get(key, 0)
        if now - last >= cooldown:
            self._last_incident_time[key] = now
            return True
        return False

    # ------------------------------------------------------------------
    # LOCAL SYSTEM CHECKS
    # ------------------------------------------------------------------

    def _check_system(self):
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory().percent

        disk_path = "C:\\" if os.name == "nt" else "/"
        disk = psutil.disk_usage(disk_path).percent

        print(
            f"📊 CPU: {cpu:.1f}% | MEM: {mem:.1f}% | DISK: {disk:.1f}%",
            end="\r"
        )

        if cpu >= self.config.CPU_THRESHOLD_PERCENT:
            if self._should_fire("local_cpu"):
                self.on_incident({"type": "cpu_high", "value": cpu})

        if mem >= self.config.MEM_THRESHOLD_PERCENT:
            if self._should_fire("local_mem"):
                self.on_incident({"type": "memory_high", "value": mem})

        if disk >= self.config.DISK_THRESHOLD_PERCENT:
            if self._should_fire("local_disk"):
                self.on_incident({"type": "disk_high", "value": disk})

    # ------------------------------------------------------------------
    # AWS CHECKS
    # ------------------------------------------------------------------

    def _check_aws(self):
        try:
            data = self.aws.list_instances()
            for inst in data.get("instances", []):
                metrics = self.aws.get_cpu_metrics(inst["id"])
                datapoints = metrics.get("metrics", [])

                if not datapoints:
                    continue

                latest = sorted(
                    datapoints,
                    key=lambda x: x["Timestamp"]
                )[-1]

                avg = latest.get("Average", 0)
                key = f"aws_cpu_{inst['id']}"

                if avg >= 80 and self._should_fire(key):
                    self.on_incident({
                        "type": "ec2_cpu_high",
                        "instance_id": inst["id"],
                        "value": avg,
                        "description": f"High CPU ({avg}%) on EC2 {inst['id']}"
                    })
        except Exception as e:
            print(f"\n[AWS Monitor Error] {e}")

    # ------------------------------------------------------------------
    # AZURE CHECKS
    # ------------------------------------------------------------------

    def _check_azure(self):
        try:
            data = self.azure.list_instances()
            for vm in data.get("instances", []):
                metrics = self.azure.get_cpu_metrics(vm["id"])
                datapoints = metrics.get("metrics", [])

                if not datapoints:
                    continue

                latest = sorted(
                    datapoints,
                    key=lambda x: x["timestamp"]
                )[-1]

                avg = latest.get("average", 0)
                key = f"azure_cpu_{vm['id']}"

                if avg >= 80 and self._should_fire(key):
                    self.on_incident({
                        "type": "azure_vm_cpu_high",
                        "vm_name": vm["name"],
                        "resource_group": vm["resource_group"],
                        "value": avg,
                        "description": f"High CPU ({avg}%) on Azure VM {vm['name']}"
                    })
        except Exception as e:
            print(f"\n[Azure Monitor Error] {e}")

    # ------------------------------------------------------------------
    # MAIN LOOP
    # ------------------------------------------------------------------

    def _check_all(self):
        self._check_system()
        self._check_aws()
        self._check_azure()

    def run_forever(self, poll_interval: int = None):
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
        self._running = False
