# File: tools/aws_tool.py
"""
AWS integration layer for ai-admin-agent.
Handles EC2, S3, CloudWatch, and Network metrics.
Performs safe automation such as rebooting instances and inspecting networking.
Requires boto3 and valid AWS credentials.
"""

import boto3
import datetime
from typing import Dict, Any, List


class AWSTool:
    """Unified AWS operations utility for EC2, S3, CloudWatch, and networking."""

    def __init__(self, region: str = "us-east-1", dry_run: bool = True):
        self.region = region
        self.dry_run = dry_run

        try:
            self.ec2 = boto3.client("ec2", region_name=self.region)
            self.cloudwatch = boto3.client("cloudwatch", region_name=self.region)
            self.s3 = boto3.client("s3", region_name=self.region)
        except Exception as e:
            raise RuntimeError(f"AWS client initialization failed: {e}")

    # ---------------------- EC2 OPERATIONS ----------------------

    def list_instances(self) -> Dict[str, Any]:
        """List EC2 instances, states, and IP details."""
        if self.dry_run:
            return {"simulated": True, "action": "list_instances"}

        try:
            resp = self.ec2.describe_instances()
            instances = []
            for r in resp.get("Reservations", []):
                for i in r.get("Instances", []):
                    instances.append({
                        "id": i.get("InstanceId"),
                        "state": i.get("State", {}).get("Name"),
                        "type": i.get("InstanceType"),
                        "private_ip": i.get("PrivateIpAddress"),
                        "public_ip": i.get("PublicIpAddress"),
                        "vpc_id": i.get("VpcId"),
                        "subnet_id": i.get("SubnetId"),
                        "launch_time": str(i.get("LaunchTime"))
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

    def start_instance(self, instance_id: str) -> Dict[str, Any]:
        """Start an EC2 instance."""
        if self.dry_run:
            return {"simulated": True, "action": f"start_instance({instance_id})"}

        try:
            self.ec2.start_instances(InstanceIds=[instance_id])
            return {"status": "start_initiated", "instance_id": instance_id}
        except Exception as e:
            return {"error": str(e), "instance_id": instance_id}

    def stop_instance(self, instance_id: str) -> Dict[str, Any]:
        """Stop an EC2 instance."""
        if self.dry_run:
            return {"simulated": True, "action": f"stop_instance({instance_id})"}

        try:
            self.ec2.stop_instances(InstanceIds=[instance_id])
            return {"status": "stop_initiated", "instance_id": instance_id}
        except Exception as e:
            return {"error": str(e), "instance_id": instance_id}

    # ---------------------- NETWORK INFO ----------------------

    def get_network_details(self, instance_id: str) -> Dict[str, Any]:
        """Fetch VPC, subnet, and security group info for a given instance."""
        if self.dry_run:
            return {"simulated": True, "action": f"get_network_details({instance_id})"}

        try:
            desc = self.ec2.describe_instances(InstanceIds=[instance_id])
            i = desc["Reservations"][0]["Instances"][0]
            network_info = {
                "InstanceId": instance_id,
                "PrivateIP": i.get("PrivateIpAddress"),
                "PublicIP": i.get("PublicIpAddress"),
                "VPCId": i.get("VpcId"),
                "SubnetId": i.get("SubnetId"),
                "SecurityGroups": [sg["GroupName"] for sg in i.get("SecurityGroups", [])]
            }
            return network_info
        except Exception as e:
            return {"error": str(e), "instance_id": instance_id}

    # ---------------------- CLOUDWATCH NETWORK METRICS ----------------------

    def get_network_metrics(self, instance_id: str) -> Dict[str, Any]:
        """Get network in/out usage from CloudWatch (last 30 minutes)."""
        if self.dry_run:
            return {"simulated": True, "action": f"get_network_metrics({instance_id})"}

        try:
            end_time = datetime.datetime.utcnow()
            start_time = end_time - datetime.timedelta(minutes=30)

            metrics = {}
            for direction in ["NetworkIn", "NetworkOut"]:
                data = self.cloudwatch.get_metric_statistics(
                    Namespace="AWS/EC2",
                    MetricName=direction,
                    Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
                    StartTime=start_time,
                    EndTime=end_time,
                    Period=300,
                    Statistics=["Sum"],
                    Unit="Bytes"
                )
                datapoints = sorted(data.get("Datapoints", []), key=lambda x: x["Timestamp"])
                metrics[direction] = datapoints[-1]["Sum"] if datapoints else 0

            return {
                "InstanceId": instance_id,
                "NetworkIn_Bytes": metrics.get("NetworkIn", 0),
                "NetworkOut_Bytes": metrics.get("NetworkOut", 0),
                "PeriodMinutes": 30
            }
        except Exception as e:
            return {"error": str(e), "instance_id": instance_id}

    # ---------------------- S3 OPERATIONS ----------------------

    def list_s3_buckets(self) -> Dict[str, Any]:
        """List all S3 buckets."""
        if self.dry_run:
            return {"simulated": True, "action": "list_s3_buckets"}

        try:
            resp = self.s3.list_buckets()
            buckets = [b["Name"] for b in resp.get("Buckets", [])]
            return {"buckets": buckets}
        except Exception as e:
            return {"error": str(e)}

    def create_s3_bucket(self, bucket_name: str) -> Dict[str, Any]:
        """Create an S3 bucket."""
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
