# File: tools/azure_tool.py
"""
Path: tools/azure_tool.py
Placeholder Azure helper module. Add azure-mgmt SDK usage as needed.
"""
""" class AzureTool:
    def __init__(self, credentials: dict = None):
        self.credentials = credentials or {}

    def list_vms(self):
        # TODO: implement using azure-mgmt-compute
        return {"info": "stub", "vms": []}
        cur = self._conn.cursor()
        cur.execute("SELECT id, ts, action_json, result_json FROM actions WHERE incident_id = ? ORDER BY id ASC", (incident_id,))
        rows = cur.fetchall()
        return [dict(r) for r in rows] """
"""
Azure integration layer for ai-admin-agent.
Handles Virtual Machines, Blob Storage, Azure Monitor metrics,
and basic network inspection.
"""

import datetime
from typing import Dict, Any, List, Optional

from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.monitor import MonitorManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.storage.blob import BlobServiceClient


"""
Azure integration layer for ai-admin-agent.

- Lists Virtual Machines across ALL resource groups
- Safely starts/stops/restarts VMs (explicit RG required)
- Supports basic networking, metrics, and blob storage
"""

import datetime
from typing import Dict, Any, Optional

from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.monitor import MonitorManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.storage.blob import BlobServiceClient


class AzureTool:
    def __init__(
        self,
        subscription_id: str,
        resource_group: Optional[str] = None,
        dry_run: bool = True,
    ):
        if not subscription_id:
            raise ValueError("AZURE_SUBSCRIPTION_ID is required")

        self.subscription_id = subscription_id
        self.default_resource_group = resource_group
        self.dry_run = dry_run

        self.credential = DefaultAzureCredential()

        self.compute = ComputeManagementClient(
            self.credential, self.subscription_id
        )
        self.network = NetworkManagementClient(
            self.credential, self.subscription_id
        )
        self.monitor = MonitorManagementClient(
            self.credential, self.subscription_id
        )
        self.storage = StorageManagementClient(
            self.credential, self.subscription_id
        )

    # ---------------------------------------------------------------------
    # HELPERS
    # ---------------------------------------------------------------------

    @staticmethod
    def _extract_resource_group(resource_id: str) -> str:
        return resource_id.split("/resourceGroups/")[1].split("/")[0]

    # ---------------------------------------------------------------------
    # VIRTUAL MACHINE MANAGEMENT (ALL RESOURCE GROUPS)
    # ---------------------------------------------------------------------
    def _normalize_os_type(self, os_type):
        if hasattr(os_type, "value"):
            return os_type.value
        return os_type

    def list_instances(self) -> Dict[str, Any]:
        """List ALL Azure VMs across ALL resource groups."""
        if self.dry_run:
            return {
                "simulated": True,
                "action": "list_instances_all_resource_groups",
            }

        try:
            instances = []

            for vm in self.compute.virtual_machines.list_all():
                instances.append({
                    "id": vm.id,
                    "name": vm.name,
                    "location": vm.location,
                    "vm_size": vm.hardware_profile.vm_size
                    if vm.hardware_profile else None,
                    "resource_group": self._extract_resource_group(vm.id),
                    "os_type": (
                        self._normalize_os_type(vm.storage_profile.os_disk.os_type)
                        if vm.storage_profile and vm.storage_profile.os_disk
                        else None
                ),

                })

            return {"instances": instances}

        except Exception as e:
            return {"error": str(e)}

    # ---------------------------------------------------------------------
    # VM ACTIONS (RESOURCE GROUP REQUIRED)
    # ---------------------------------------------------------------------

    def start_instance(self, vm_name: str, resource_group: Optional[str] = None):
        rg = resource_group or self.default_resource_group
        if not rg:
            return {"error": "resource_group is required to start a VM"}

        if self.dry_run:
            return {"simulated": True, "action": f"start_vm({vm_name}, {rg})"}

        try:
            self.compute.virtual_machines.begin_start(rg, vm_name)
            return {"status": "start_initiated", "vm_name": vm_name, "resource_group": rg}
        except Exception as e:
            return {"error": str(e)}

    def stop_instance(self, vm_name: str, resource_group: Optional[str] = None):
        rg = resource_group or self.default_resource_group
        if not rg:
            return {"error": "resource_group is required to stop a VM"}

        if self.dry_run:
            return {"simulated": True, "action": f"stop_vm({vm_name}, {rg})"}

        try:
            self.compute.virtual_machines.begin_deallocate(rg, vm_name)
            return {"status": "stop_initiated", "vm_name": vm_name, "resource_group": rg}
        except Exception as e:
            return {"error": str(e)}

    def reboot_instance(self, vm_name: str, resource_group: Optional[str] = None):
        rg = resource_group or self.default_resource_group
        if not rg:
            return {"error": "resource_group is required to restart a VM"}

        if self.dry_run:
            return {"simulated": True, "action": f"restart_vm({vm_name}, {rg})"}

        try:
            self.compute.virtual_machines.begin_restart(rg, vm_name)
            return {"status": "restart_initiated", "vm_name": vm_name, "resource_group": rg}
        except Exception as e:
            return {"error": str(e)}

    # ---------------------------------------------------------------------
    # CPU METRICS
    # ---------------------------------------------------------------------

    def get_cpu_metrics(self, vm_id: str) -> Dict[str, Any]:
        """Fetch CPU Percentage metrics using VM resource ID."""
        if self.dry_run:
            return {"simulated": True, "action": "get_cpu_metrics"}

        try:
            end = datetime.datetime.utcnow()
            start = end - datetime.timedelta(minutes=30)

            metrics = self.monitor.metrics.list(
                resource_uri=vm_id,
                timespan=f"{start}/{end}",
                interval="PT5M",
                metricnames="Percentage CPU",
                aggregation="Average,Maximum",
            )

            return {
                "vm_id": vm_id,
                "metrics": [
                    {
                        "timestamp": d.time_stamp,
                        "average": d.average,
                        "maximum": d.maximum,
                    }
                    for m in metrics.value
                    for d in m.timeseries[0].data
                ],
                "period_minutes": 30,
            }
        except Exception as e:
            return {"error": str(e)}

    # ---------------------------------------------------------------------
    # STORAGE (OPTIONAL)
    # ---------------------------------------------------------------------

    def list_storage_accounts(self) -> Dict[str, Any]:
        """List storage accounts across subscription."""
        if self.dry_run:
            return {"simulated": True, "action": "list_storage_accounts"}

        try:
            accounts = self.storage.storage_accounts.list()
            return {"storage_accounts": [a.name for a in accounts]}
        except Exception as e:
            return {"error": str(e)}
