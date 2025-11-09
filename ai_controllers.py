# File: ai_controller.py
"""
AIController now uses Groq's chat completion API instead of OpenAI.
It diagnoses incidents and returns fix plans as structured JSON.
"""
from groq import Groq
from typing import Dict, Any, List
import os
import json

SYSTEM_PROMPT = """You are an intelligent system administrator AI.
You analyze system incidents (CPU, disk, memory, AWS issues) and return
a safe JSON plan describing the root cause and commands to fix it.
Respond only in JSON with this format:
{
  "root_cause": "...",
  "steps": [
    {"tool": "bash|powershell|aws", "command": "...", "verify": "...", "risk": "low|medium|high"}
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

    def generate_plan(self, incident: Dict[str, Any]) -> Dict[str, Any]:
        """Call Groq model to reason about the incident and generate a safe fix plan."""
        try:
            completion = self.client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Incident: {json.dumps(incident)}"}
                ],
                temperature=0.7,
                max_completion_tokens=1024,
                top_p=1,
                reasoning_effort="medium",
                stream=False
            )

            response = completion.choices[0].message.content
            # Try to parse JSON safely
            try:
                plan = json.loads(response)
            except json.JSONDecodeError:
                plan = {
                    "root_cause": "Unclear response from AI",
                    "steps": [],
                    "confidence": 0.0,
                    "raw_response": response
                }

            return plan

        except Exception as e:
            return {
                "root_cause": "AI error",
                "steps": [],
                "confidence": 0.0,
                "error": str(e)
            }
