# File: main_agent.py
"""
AI-Admin-Agent: Main Orchestrator
Integrates system monitor, Groq AI reasoning, and automated fix execution.
"""

import argparse
import os
import sys
from tools.email_tool import EmailTool
import json
from dotenv import load_dotenv
from configs.defaults import Defaults
from logdb import LogDB
from monitor import Monitor
from ai_controllers import AIController
from tools.bash_tools import BashTool
from tools.powershell_tools import PowerShellTool
from tools.aws_tool import AWSTool

load_dotenv()  # Auto-load GROQ_API_KEY and AWS credentials


# ----------------------------- INCIDENT HANDLER ----------------------------- #

def handle_incident(incident: dict, logdb: LogDB, ai: AIController,
                    bash_tool: BashTool, ps_tool: PowerShellTool,
                    aws_tool: AWSTool, email_tool: EmailTool):
    """Process an incident: analyze via Groq AI → execute safe fix plan → log all actions."""
    print("\n🚨 Incident detected:", incident)
    incident_id = logdb.log_incident(incident)

    # ✅ Send one email per incident (not per step)
    email_tool.send_email(
        subject=f"🚨 AI Admin Agent Incident: {incident.get('type')}",
        body=f"Incident details:\n{json.dumps(incident, indent=2)}"
    )

    # Generate AI plan
    plan = ai.generate_plan(incident)
    print("\n🧠 AI Plan:", json.dumps(plan, indent=2))
    logdb.log_action(incident_id, {"type": "plan_generated", "plan": plan})

    # Execute each step
    for step in plan.get("steps", []):
        tool = step.get("tool", "bash").lower()
        command = step.get("command")
        verify = step.get("verify", "")
        risk = step.get("risk", "unknown")

        print(f"\n➡️ Executing step ({risk} risk): {tool} → {command}")
        result = {"error": "No tool executed"}

        try:
            if tool == "bash":
                result = bash_tool.execute(command)
            elif tool == "powershell":
                result = ps_tool.execute(command)
            elif tool == "aws":
                result = execute_aws_action(command, aws_tool)
            else:
                result = {"error": f"Unknown tool: {tool}"}
        except Exception as e:
            result = {"error": str(e)}

        print("✅ Result:", result)
        logdb.log_action(incident_id, {"tool": tool, "command": command, "verify": verify}, result)

    print("\n📘 Incident complete. Logged to database.\n")
    return plan




# ----------------------------- AWS LIVE STATUS ----------------------------- #

def show_aws_status_live(region: str):
    """Fetch and display live EC2 instance details, IPs, and metrics."""
    print(f"\n🌍 Connecting to AWS region: {region} ...")
    aws = AWSTool(region=region, dry_run=False)

    data = aws.list_instances()
    if "error" in data:
        print(f"❌ {data['error']}")
        return

    instances = data.get("instances", [])
    if not instances:
        print("⚠️ No EC2 instances found in this region.")
        return

    print(f"\n🖥️ Found {len(instances)} EC2 instance(s):\n")

    for i in instances:
        print(f"• Instance ID: {i['id']}")
        print(f"  State: {i['state']}")
        print(f"  Type: {i['type']}")
        print(f"  Launch Time: {i['launch_time']}")
        print(f"  VPC: {i.get('vpc_id')}")
        print(f"  Subnet: {i.get('subnet_id')}")
        print(f"  Private IP: {i.get('private_ip')}")
        print(f"  Public IP: {i.get('public_ip')}")

        if i["state"] == "running":
            net_info = aws.get_network_details(i["id"])
            metrics = aws.get_network_metrics(i["id"])
            print(f"  🌐 Security Groups: {net_info.get('SecurityGroups')}")
            print(f"  📊 Network In: {metrics.get('NetworkIn_Bytes')} bytes")
            print(f"  📤 Network Out: {metrics.get('NetworkOut_Bytes')} bytes")
        print("-" * 70)


# ----------------------------- AWS HELPER ----------------------------- #

def execute_aws_action(command: str, aws_tool: AWSTool) -> dict:
    """Interpret and safely execute AWS commands suggested by AI."""
    cmd = command.lower().split()
    if not cmd:
        return {"error": "Invalid AWS command"}

    action = cmd[0]
    target = cmd[-1] if len(cmd) > 1 else None

    if action in ("reboot_instance", "reboot") and target:
        return aws_tool.reboot_instance(target)
    elif action in ("start_instance", "start") and target:
        return aws_tool.start_instance(target)
    elif action in ("stop_instance", "stop") and target:
        return aws_tool.stop_instance(target)
    elif action in ("list_instances", "list"):
        return aws_tool.list_instances()
    else:
        return {"warning": f"Unknown AWS action: {command}"}


# ----------------------------- SIMPLE CLI COMMANDS ----------------------------- #

def simple_cli_action(action: str, target: str = None):
    """Simple CLI: start/stop/reboot/status for EC2 by name or ID."""
    region = os.getenv("AWS_REGION", "us-east-1")
    aws = AWSTool(region=region, dry_run=False)

    if action == "status":
        print("\n🔍 Fetching live EC2 status...\n")
        show_aws_status_live(region)
        return

    if not target:
        print("❌ You must specify an instance name or ID.")
        return

    instance_id = aws.find_instance_by_name(target)
    if not instance_id:
        print(f"❌ Could not find instance named or matching '{target}'")
        return

    print(f"🖥️ Target Instance: {instance_id}")

    if action == "restart":
        result = aws.reboot_instance(instance_id)
    elif action == "start":
        result = aws.start_instance(instance_id)
    elif action == "stop":
        result = aws.stop_instance(instance_id)
    else:
        print(f"❌ Unknown action: {action}")
        return

    print(f"✅ {action.capitalize()} result:", result)


# ----------------------------- COMPONENT BUILDER ----------------------------- #

def build_components(config: Defaults, dry_run: bool):
    os.makedirs(os.path.dirname(config.DB_PATH), exist_ok=True)
    logdb = LogDB(config.DB_PATH)
    ai = AIController(api_key=os.getenv("GROQ_API_KEY"), dry_run=dry_run)
    bash_tool = BashTool(list(config.COMMAND_WHITELIST), dry_run=dry_run)
    ps_tool = PowerShellTool(list(config.COMMAND_WHITELIST), dry_run=dry_run)
    aws_tool = AWSTool(region=os.getenv("AWS_REGION", "us-east-1"), dry_run=dry_run)

    # ✅ Email notifier setup
    email_tool = EmailTool(
        sender=os.getenv("EMAIL_SENDER"),
        password=os.getenv("EMAIL_PASSWORD"),
        receiver=os.getenv("EMAIL_RECEIVER"),
        smtp_server=os.getenv("SMTP_SERVER", "smtp.gmail.com"),
        smtp_port=int(os.getenv("SMTP_PORT", 587))
    )

    return logdb, ai, bash_tool, ps_tool, aws_tool, email_tool




# ----------------------------- MAIN ENTRYPOINT ----------------------------- #

def main():
    parser = argparse.ArgumentParser(prog="ai-admin-agent", description="AI-powered system administration agent")
    parser.add_argument("action", nargs="?", help="Action: start | stop | restart | status | monitor")
    parser.add_argument("target", nargs="?", help="Instance name or ID")
    parser.add_argument("--ask", type=str, help="Ask AI to interpret and execute your instruction")
    parser.add_argument("--dry-run", action="store_true", help="Run in dry-run mode (no destructive actions)")
    parser.add_argument("--monitor", action="store_true", help="Start continuous monitoring")
    parser.add_argument("--run-once", action="store_true", help="Run a single monitoring check and exit")
    parser.add_argument("--incident-json", type=str, help="Pass an incident JSON manually")
    parser.add_argument("--show-logs", action="store_true", help="Display recent incidents and actions")
    parser.add_argument("--aws-status-live", action="store_true", help="Show live AWS EC2 instances and metrics")
    args = parser.parse_args()

    config = Defaults()
    dry_run = args.dry_run or os.getenv("AI_DRY_RUN", "true").lower() in ("true", "1")

    logdb, ai, bash_tool, ps_tool, aws_tool, email_tool = build_components(config, dry_run)

    # --- Simple CLI commands ---
    if args.action in ["restart", "start", "stop", "status"]:
        simple_cli_action(args.action, args.target)
        return

    # --- Natural AI Command Mode ---
    if args.ask:
        prompt = args.ask
        print(f"\n🧠 AI interpreting your request: {prompt}\n")
        plan = ai.generate_plan({"type": "user_request", "prompt": prompt})
        print("🧩 AI Plan:", json.dumps(plan, indent=2))

        for step in plan.get("steps", []):
            tool = step.get("tool")
            cmd = step.get("command")
            print(f"\n➡️ Executing: {tool} → {cmd}")

            if tool == "aws":
                result = execute_aws_action(cmd, aws_tool)
            elif tool == "bash":
                result = bash_tool.execute(cmd)
            elif tool == "powershell":
                result = ps_tool.execute(cmd)
            else:
                result = {"warning": "Unknown tool type"}

            print("✅ Result:", result)
        return

    # --- AWS live status ---
    if args.aws_status_live:
        show_aws_status_live(os.getenv("AWS_REGION", "us-east-1"))
        return

    # --- Show logs ---
    if args.show_logs:
        print("\n📜 Recent Incidents:")
        for inc in logdb.get_recent_incidents():
            print(json.dumps(inc, indent=2))
        return

    # --- Manual incident ---
    if args.incident_json:
        try:
            incident = json.loads(args.incident_json)
            handle_incident(incident, logdb, ai, bash_tool, ps_tool, aws_tool, email_tool)

        except json.JSONDecodeError:
            print("❌ Invalid JSON format for --incident-json")
        return

    # --- Monitor mode ---
    monitor = Monitor(config, lambda inc: handle_incident(inc, logdb, ai, bash_tool, ps_tool, aws_tool, email_tool))

    if args.monitor:
        if args.run_once:
            print("🧩 Running one-time system + AWS health check...")
            monitor._check_all()
            print("✅ Single monitor check complete.")
        else:
            print("🛰️ Starting continuous monitoring — press Ctrl+C to stop.")
            monitor.run_forever()
    else:
        parser.print_help()



if __name__ == "__main__":
    main()
