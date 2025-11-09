# File: tools/azure_tool.py
"""
Path: tools/azure_tool.py
Placeholder Azure helper module. Add azure-mgmt SDK usage as needed.
"""
class AzureTool:
    def __init__(self, credentials: dict = None):
        self.credentials = credentials or {}

    def list_vms(self):
        # TODO: implement using azure-mgmt-compute
        return {"info": "stub", "vms": []}
        cur = self._conn.cursor()
        cur.execute("SELECT id, ts, action_json, result_json FROM actions WHERE incident_id = ? ORDER BY id ASC", (incident_id,))
        rows = cur.fetchall()
        return [dict(r) for r in rows] 