


"""
AIController using Groq chat completion API.
Generates structured JSON plans for incidents and user requests.
"""

from groq import Groq
from typing import Dict, Any
import os
import json


SYSTEM_PROMPT = """
You are an intelligent system administrator AI.

You analyze system incidents and user requests involving:
- Linux systems
- Windows systems
- AWS resources
- Azure resources

You MUST return a safe JSON plan describing the root cause and actions.

IMPORTANT TOOL RULES:
- Use "aws" ONLY for AWS resources
- Use "azure" ONLY for Azure resources
- Use "bash" ONLY for local Linux commands
- Use "powershell" ONLY for local Windows commands
- NEVER use cloud CLIs (aws cli, az cli)
- For Azure VM actions, resource group may be omitted; the system resolves it automatically

Allowed tools:
- bash
- powershell
- aws
- azure

Azure command examples:
- list_vms
- start_vm <vm_name>
- stop_vm <vm_name>
- restart_vm <vm_name>

AWS command examples:
- list_instances
- start_instance <id>
- stop_instance <id>
- reboot_instance <id>

Respond ONLY in valid JSON using this format:
{
  "root_cause": "...",
  "steps": [
    {
      "tool": "bash|powershell|aws|azure",
      "command": "...",
      "verify": "...",
      "risk": "low|medium|high"
    }
  ],
  "confidence": 0.0-1.0
}
"""


class AIController:
    def __init__(self, api_key: str = None, dry_run: bool = True):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.dry_run = dry_run

        if not self.api_key:
            raise ValueError("Missing GROQ_API_KEY in environment.")

        self.client = Groq(api_key=self.api_key)

    # ------------------------------------------------------------------
    # INTERNAL: CLEAN + PARSE MODEL OUTPUT
    # ------------------------------------------------------------------

    def _parse_json(self, text: str) -> Dict[str, Any]:
        clean = text.strip()

        # Remove ```json fences
        if clean.startswith("```"):
            clean = clean.strip("`").strip()
            if clean.lower().startswith("json"):
                clean = clean[4:].strip()

        # Attempt to recover truncated JSON
        if not clean.endswith("}"):
            clean = clean + "}"

        try:
            return json.loads(clean)
        except Exception:
            return {
                "root_cause": "Invalid or truncated AI response",
                "steps": [],
                "confidence": 0.0,
                "raw_response": text,
            }

    # ------------------------------------------------------------------
    # PUBLIC API
    # ------------------------------------------------------------------

    def generate_plan(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a structured remediation plan using Groq."""
        try:
            completion = self.client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Incident: {json.dumps(incident)}"},
                ],
                temperature=0.2,
                max_completion_tokens=1024,
                top_p=1,
                reasoning_effort="medium",
                stream=False,
            )

            raw = completion.choices[0].message.content
            return self._parse_json(raw)

        except Exception as e:
            return {
                "root_cause": "AI error",
                "steps": [],
                "confidence": 0.0,
                "error": str(e),
            }
