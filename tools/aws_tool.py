# File: tools/aws_tool.py
"""
AWS integration layer for ai-admin-agent.
Handles EC2, S3, and CloudWatch operations with dry-run safety.
Requires:
    - boto3
    - Valid AWS credentials in environment or ~/.aws/config
"""

import boto3
import datetime
from typing import Dict, Any, List


class AWSTool:
    """Unified AWS operations utility for EC2, S3, and CloudWatch."""

    def __init__(self, region: str = "us-east-1", dry_run: bool = True):
        self.region = region
        self.dry_run = dry_run
        try:
            self.ec2 = boto3.client("ec2", region_name=self.region)
            self.s3 = boto3.client("s3", region_name=self.region)
            self.cloudwatch = boto3.client("cloudwatch", region_name=self.region)
        except Exception as e:
            raise RuntimeError(f"AWS client initialization failed: {e}")

    # ---------------------- EC2 OPERATIONS ----------------------

    def list_instances(self) -> Dict[str, Any]:
        """List EC2 instances and their current state."""
        if self.dry_run:
            return {"simulated": True, "action": "list_instances"}

        try:
            resp = self.ec2.describe_instances()
            instances: List[Dict[str, Any]] = []
            for reservation in resp.get("Reservations", []):
                for instance in reservation.get("Instances", []):
                    instances.append({
                        "id": instance.get("InstanceId"),
                        "state": instance.get("State", {}).get("Name"),
                        "type": instance.get("InstanceType"),
                        "launch_time": str(instance.get("LaunchTime"))
                    })
            return {"instances": instances}
        except Exception as e:
            return {"error": str(e)}

    def reboot_instance(self, instance_id: str) -> Dict[str, Any]:
        """Reboot an EC2 instance safely."""
        if self.dry_run:
            return {"simulated": True, "action": f"reboot_instance({instance_id})"}

        try:
            self.ec2.reboot_instances(InstanceIds=[instance_id])
            return {"status": "reboot_initiated", "instance_id": instance_id}
        except Exception as e:
            return {"error": str(e), "instance_id": instance_id}

    def stop_instance(self, instance_id: str) -> Dict[str, Any]:
        """Stop an EC2 instance."""
        if self.dry_run:
            return {"simulated": True, "action": f"stop_instance({instance_id})"}

        try:
            self.ec2.stop_instances(InstanceIds=[instance_id])
            return {"status": "stopped_initiated", "instance_id": instance_id}
        except Exception as e:
            return {"error": str(e), "instance_id": instance_id}

    def start_instance(self, instance_id: str) -> Dict[str, Any]:
        """Start an EC2 instance."""
        if self.dry_run:
            return {"simulated": True, "action": f"start_instance({instance_id})"}

        try:
            self.ec2.start_instances(InstanceIds=[instance_id])
            return {"status": "start_initiated", "instance_id": instance_id}
        except Exception as e:
            return {"error": str(e), "instance_id": instance_id}

    # ---------------------- CLOUDWATCH METRICS ----------------------

    def get_cpu_metrics(self, instance_id: str) -> Dict[str, Any]:
        """Fetch average CPU utilization for the last 30 minutes."""
        if self.dry_run:
            return {"simulated": True, "action": f"get_cpu_metrics({instance_id})"}

        try:
            metrics = self.cloudwatch.get_metric_statistics(
                Namespace="AWS/EC2",
                MetricName="CPUUtilization",
                Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
                StartTime=datetime.datetime.utcnow() - datetime.timedelta(minutes=30),
                EndTime=datetime.datetime.utcnow(),
                Period=300,
                Statistics=["Average"],
                Unit="Percent"
            )
            datapoints = sorted(metrics.get("Datapoints", []), key=lambda x: x["Timestamp"])
            return {"instance_id": instance_id, "metrics": datapoints}
        except Exception as e:
            return {"error": str(e), "instance_id": instance_id}

    # ---------------------- S3 OPERATIONS ----------------------

    def list_s3_buckets(self) -> Dict[str, Any]:
        """List all available S3 buckets."""
        if self.dry_run:
            return {"simulated": True, "action": "list_s3_buckets"}

        try:
            resp = self.s3.list_buckets()
            buckets = [b["Name"] for b in resp.get("Buckets", [])]
            return {"buckets": buckets}
        except Exception as e:
            return {"error": str(e)}

    def create_s3_bucket(self, bucket_name: str) -> Dict[str, Any]:
        """Create a new S3 bucket in the configured region."""
        if self.dry_run:
            return {"simulated": True, "action": f"create_s3_bucket({bucket_name})"}

        try:
            self.s3.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={"LocationConstraint": self.region}
            )
            return {"status": "bucket_created", "bucket_name": bucket_name}
        except Exception as e:
            return {"error": str(e), "bucket_name": bucket_name}

    def delete_s3_bucket(self, bucket_name: str) -> Dict[str, Any]:
        """Delete an S3 bucket."""
        if self.dry_run:
            return {"simulated": True, "action": f"delete_s3_bucket({bucket_name})"}

        try:
            self.s3.delete_bucket(Bucket=bucket_name)
            return {"status": "bucket_deleted", "bucket_name": bucket_name}
        except Exception as e:
            return {"error": str(e), "bucket_name": bucket_name}
