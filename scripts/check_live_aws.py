from tools.aws_tool import AWSTool
import json

aws = AWSTool(region="eu-north-1", dry_run=False)
instances = aws.list_instances()

print("\n🖥️ EC2 Instance Summary:")
print(json.dumps(instances, indent=2))
for instance in instances.get("instances", []):
    instance_id = instance["id"]
    cpu_metrics = aws.get_cpu_metrics(instance_id)
    print(f"\n⏱️ CPU Metrics for Instance {instance_id}:")
    print(json.dumps(cpu_metrics, indent=2))