"""
AI-Admin-Agent: Main Orchestrator
Integrates system monitor, Groq AI reasoning, and automated fix execution.
"""

import argparse
import os
import json
from dotenv import load_dotenv

from configs.defaults import Defaults
from logdb import LogDB
from monitor import Monitor

from ai_controllers import AIController
from tools.bash_tools import BashTool
from tools.powershell_tools import PowerShellTool
from tools.aws_tool import AWSTool
from tools.azure_tool import AzureTool
from tools.email_tool import EmailTool

load_dotenv()


# ---------------------------------------------------------------------------
# CLOUD EXECUTORS
# ---------------------------------------------------------------------------

def execute_aws_action(command: str, aws_tool: AWSTool) -> dict:
    cmd = command.lower().split()
    if not cmd:
        return {"error": "Invalid AWS command"}

    action = cmd[0]
    target = cmd[-1] if len(cmd) > 1 else None

    if action in ("list_instances", "list"):
        return aws_tool.list_instances()
    elif action in ("start", "start_instance") and target:
        return aws_tool.start_instance(target)
    elif action in ("stop", "stop_instance") and target:
        return aws_tool.stop_instance(target)
    elif action in ("restart", "reboot", "reboot_instance") and target:
        return aws_tool.reboot_instance(target)
    else:
        return {"warning": f"Unknown AWS action: {command}"}

def resolve_azure_vm(vm_name: str, azure_tool: AzureTool):
    """
    Resolve VM name → (actual_name, resource_group)
    """
    data = azure_tool.list_instances()
    if "instances" not in data:
        return None, None

    for vm in data["instances"]:
        if vm["name"].lower() == vm_name.lower():
            return vm["name"], vm["resource_group"]

    return None, None

def execute_azure_action(command: str, azure_tool: AzureTool) -> dict:
    cmd = command.lower().split()
    if not cmd:
        return {"error": "Invalid Azure command"}

    action = cmd[0]

    # -----------------------
    # LIST
    # -----------------------
    if action in ("list", "list_vms"):
        return azure_tool.list_instances()

    # -----------------------
    # START ALL VMS
    # -----------------------
    if command.lower() in ("start all vms", "start all"):
        data = azure_tool.list_instances()
        if "instances" not in data:
            return {"error": "Unable to list VMs"}

        results = []
        for vm in data["instances"]:
            res = azure_tool.start_instance(
                vm["name"],
                vm["resource_group"]
            )
            results.append({
                "vm": vm["name"],
                "resource_group": vm["resource_group"],
                "result": res
            })

        return {
            "action": "start_all_vms",
            "count": len(results),
            "results": results
        }

    # -----------------------
    # START / STOP / RESTART ONE VM
    # -----------------------
    if action in ("start", "start_vm", "stop", "stop_vm", "restart", "restart_vm", "reboot"):
        if len(cmd) < 2:
            return {"error": "VM name required"}

        vm_input = cmd[1]
        data = azure_tool.list_instances()

        matched = next(
            (vm for vm in data.get("instances", [])
             if vm["name"].lower() == vm_input.lower()),
            None
        )

        if not matched:
            return {"error": f"VM '{vm_input}' not found"}

        if action.startswith("start"):
            return azure_tool.start_instance(matched["name"], matched["resource_group"])
        elif action.startswith("stop"):
            return azure_tool.stop_instance(matched["name"], matched["resource_group"])
        elif action.startswith(("restart", "reboot")):
            return azure_tool.reboot_instance(matched["name"], matched["resource_group"])

    return {"warning": f"Unknown Azure action: {command}"}





# ---------------------------------------------------------------------------
# INCIDENT HANDLER
# ---------------------------------------------------------------------------

def handle_incident(
    incident: dict,
    logdb: LogDB,
    ai: AIController,
    bash_tool: BashTool,
    ps_tool: PowerShellTool,
    aws_tool: AWSTool,
    azure_tool: AzureTool,
    email_tool: EmailTool,
):
    print("\n🚨 Incident detected:", incident)
    incident_id = logdb.log_incident(incident)

    email_tool.send_email(
        subject=f"🚨 AI Admin Agent Incident: {incident.get('type')}",
        body=json.dumps(incident, indent=2),
    )

    plan = ai.generate_plan(incident)
    print("\n🧠 AI Plan:", json.dumps(plan, indent=2))

    if plan.get("confidence", 0) < 0.7:
        print("⚠️ Low confidence plan — refusing to execute.")
        return plan

    for step in plan.get("steps", []):
        tool = step.get("tool", "").lower()
        command = step.get("command")

        print(f"\n➡️ Executing: {tool} → {command}")

        if tool == "aws":
            result = execute_aws_action(command, aws_tool)
        elif tool == "azure":
            result = execute_azure_action(command, azure_tool)
        elif tool == "bash":
            result = bash_tool.execute(command)
        elif tool == "powershell":
            result = ps_tool.execute(command)
        else:
            result = {"error": f"Unknown tool: {tool}"}

        print("✅ Result:", result)
        logdb.log_action(incident_id, step, result)

    return plan


# ---------------------------------------------------------------------------
# COMPONENT BUILDER
# ---------------------------------------------------------------------------

def build_components(config: Defaults, dry_run: bool):
    os.makedirs(os.path.dirname(config.DB_PATH), exist_ok=True)

    logdb = LogDB(config.DB_PATH)

    ai = AIController(api_key=os.getenv("GROQ_API_KEY"), dry_run=dry_run)

    bash_tool = BashTool(list(config.COMMAND_WHITELIST), dry_run=dry_run)
    ps_tool = PowerShellTool(list(config.COMMAND_WHITELIST), dry_run=dry_run)

    aws_tool = AWSTool(
        region=os.getenv("AWS_REGION", "us-east-1"),
        dry_run=dry_run,
    )

    azure_tool = AzureTool(
        subscription_id=os.getenv("AZURE_SUBSCRIPTION_ID"),
        resource_group=os.getenv("AZURE_RESOURCE_GROUP"),
        dry_run=dry_run,
    )

    email_tool = EmailTool(
        sender=os.getenv("EMAIL_SENDER"),
        password=os.getenv("EMAIL_PASSWORD"),
        receiver=os.getenv("EMAIL_RECEIVER"),
        smtp_server=os.getenv("SMTP_SERVER", "smtp.gmail.com"),
        smtp_port=int(os.getenv("SMTP_PORT", 587)),
    )

    return logdb, ai, bash_tool, ps_tool, aws_tool, azure_tool, email_tool


# ---------------------------------------------------------------------------
# MAIN ENTRYPOINT
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(prog="ai-admin-agent")
    parser.add_argument("--ask", type=str)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--monitor", action="store_true")
    parser.add_argument("--run-once", action="store_true")
    parser.add_argument(
    "--interactive",
    action="store_true",
    help="Start interactive AI session (ask multiple questions)")

    args = parser.parse_args()

    config = Defaults()
    dry_run = args.dry_run

    (
        logdb,
        ai,
        bash_tool,
        ps_tool,
        aws_tool,
        azure_tool,
        email_tool,
    ) = build_components(config, dry_run)

    # ---- AI COMMAND MODE ----
    # ---- INTERACTIVE MODE ----
    if args.interactive:
        interactive_loop(
            ai,
            bash_tool,
            ps_tool,
            aws_tool,
            azure_tool,
        )
        return


    if args.ask:
        print(f"\n🧠 AI interpreting: {args.ask}\n")
        plan = ai.generate_plan({"type": "user_request", "prompt": args.ask})
        print("🧩 AI Plan:", json.dumps(plan, indent=2))

        if plan.get("confidence", 0) < 0.7:
            print("⚠️ Low confidence — refusing to execute.")
            return

        for step in plan.get("steps", []):
            tool = step.get("tool", "").lower()
            command = step.get("command")

            print(f"\n➡️ Executing: {tool} → {command}")

            if tool == "aws":
                result = execute_aws_action(command, aws_tool)
            elif tool == "azure":
                result = execute_azure_action(command, azure_tool)
            elif tool == "bash":
                result = bash_tool.execute(command)
            elif tool == "powershell":
                result = ps_tool.execute(command)
            else:
                result = {"error": f"Unknown tool: {tool}"}

            print("✅ Result:", result)

        return

    # ---- MONITOR MODE ----
    if args.monitor:
        monitor = Monitor(
            config,
            lambda inc: handle_incident(
                inc,
                logdb,
                ai,
                bash_tool,
                ps_tool,
                aws_tool,
                azure_tool,
                email_tool,
            ),
        )

        if args.run_once:
            monitor._check_all()
        else:
            monitor.run_forever()
        return

    parser.print_help()

def interactive_loop(ai, bash_tool, ps_tool, aws_tool, azure_tool):
    print("\n🧠 AI Admin Agent (interactive mode)")
    print("Type 'exit' or 'quit' to stop\n")

    while True:
        try:
            user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Exiting interactive mode.")
            break

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit"):
            print("👋 Goodbye.")
            break

        plan = ai.generate_plan({
            "type": "user_request",
            "prompt": user_input
        })

        print("\n🧩 AI Plan:")
        print(json.dumps(plan, indent=2))

        if plan.get("confidence", 0) < 0.7:
            print("⚠️ Low confidence — not executing.\n")
            continue

        for step in plan.get("steps", []):
            tool = step.get("tool", "").lower()
            command = step.get("command")

            print(f"\n➡️ Executing: {tool} → {command}")

            if tool == "aws":
                result = execute_aws_action(command, aws_tool)
            elif tool == "azure":
                result = execute_azure_action(command, azure_tool)
            elif tool == "bash":
                result = bash_tool.execute(command)
            elif tool == "powershell":
                result = ps_tool.execute(command)
            else:
                result = {"error": f"Unknown tool: {tool}"}

            print("✅ Result:", result)

        print()


if __name__ == "__main__":
    main()
