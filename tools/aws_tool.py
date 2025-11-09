# File: tools/aws_tool.py
"""
AWS integration layer for ai-admin-agent.
Handles EC2, S3, CloudWatch, and basic network monitoring.
"""

import boto3
import datetime
from typing import Dict, Any, List


class AWSTool:
    def __init__(self, region: str = "us-east-1", dry_run: bool = True):
        self.region = region
        self.dry_run = dry_run
        self.ec2 = boto3.client("ec2", region_name=self.region)
        self.s3 = boto3.client("s3", region_name=self.region)
        self.cloudwatch = boto3.client("cloudwatch", region_name=self.region)

    # -------------------------------------------------------------------------
    # EC2 INSTANCE MANAGEMENT
    # -------------------------------------------------------------------------

    def list_instances(self) -> Dict[str, Any]:
        """List EC2 instances and basic info."""
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
                        "launch_time": str(i.get("LaunchTime")),
                        "vpc_id": i.get("VpcId"),
                        "subnet_id": i.get("SubnetId"),
                        "private_ip": i.get("PrivateIpAddress"),
                        "public_ip": i.get("PublicIpAddress"),
                    })
            return {"instances": instances}
        except Exception as e:
            return {"error": str(e)}

    def reboot_instance(self, instance_id: str) -> Dict[str, Any]:
        """Reboot an EC2 instance."""
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

    # -------------------------------------------------------------------------
    # NETWORK + CLOUDWATCH METRICS
    # -------------------------------------------------------------------------

    def get_network_details(self, instance_id: str) -> Dict[str, Any]:
        """Fetch VPC, Subnet, IPs, and Security Groups for a given EC2 instance."""
        if self.dry_run:
            return {"simulated": True, "action": f"get_network_details({instance_id})"}
        try:
            resp = self.ec2.describe_instances(InstanceIds=[instance_id])
            if not resp["Reservations"]:
                return {"error": "Instance not found"}

            instance = resp["Reservations"][0]["Instances"][0]
            return {
                "InstanceId": instance_id,
                "PrivateIP": instance.get("PrivateIpAddress"),
                "PublicIP": instance.get("PublicIpAddress"),
                "VPCId": instance.get("VpcId"),
                "SubnetId": instance.get("SubnetId"),
                "SecurityGroups": [sg["GroupName"] for sg in instance.get("SecurityGroups", [])],
            }
        except Exception as e:
            return {"error": str(e), "instance_id": instance_id}

    def get_network_metrics(self, instance_id: str) -> Dict[str, Any]:
        """Fetch recent NetworkIn and NetworkOut metrics."""
        if self.dry_run:
            return {"simulated": True, "action": f"get_network_metrics({instance_id})"}

        try:
            end = datetime.datetime.utcnow()
            start = end - datetime.timedelta(minutes=30)

            def get_metric(name: str):
                resp = self.cloudwatch.get_metric_statistics(
                    Namespace="AWS/EC2",
                    MetricName=name,
                    Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
                    StartTime=start,
                    EndTime=end,
                    Period=300,
                    Statistics=["Sum"]
                )
                return sum([p["Sum"] for p in resp.get("Datapoints", [])])

            return {
                "InstanceId": instance_id,
                "NetworkIn_Bytes": get_metric("NetworkIn"),
                "NetworkOut_Bytes": get_metric("NetworkOut"),
                "PeriodMinutes": 30
            }

        except Exception as e:
            return {"error": str(e), "instance_id": instance_id}

    # -------------------------------------------------------------------------
    # S3 MANAGEMENT
    # -------------------------------------------------------------------------

    def list_s3_buckets(self) -> Dict[str, Any]:
        """List all S3 buckets."""
        if self.dry_run:
            return {"simulated": True, "action": "list_s3_buckets"}
        try:
            resp = self.s3.list_buckets()
            return {"buckets": [b["Name"] for b in resp.get("Buckets", [])]}
        except Exception as e:
            return {"error": str(e)}

    def create_s3_bucket(self, bucket_name: str) -> Dict[str, Any]:
        """Create a new S3 bucket."""
        if self.dry_run:
            return {"simulated": True, "action": f"create_s3_bucket({bucket_name})"}
        try:
            self.s3.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={'LocationConstraint': self.region}
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
        
        # -------------------------------------------------------------------------
    # INSTANCE HELPER METHODS
    # -------------------------------------------------------------------------

    def find_instance_by_name(self, name: str) -> str:
        """Find instance ID by Name tag or partial ID."""
        try:
            resp = self.ec2.describe_instances(
                Filters=[{"Name": "tag:Name", "Values": [name]}]
            )
            for r in resp.get("Reservations", []):
                for i in r.get("Instances", []):
                    return i["InstanceId"]
            # fallback: match partial ID
            all_instances = self.list_instances().get("instances", [])
            for i in all_instances:
                if name in i["id"]:
                    return i["id"]
            return None
        except Exception as e:
            return None

    def get_instance_status(self, instance_id: str) -> Dict[str, Any]:
        """Get the current state of an instance."""
        try:
            resp = self.ec2.describe_instance_status(
                InstanceIds=[instance_id],
                IncludeAllInstances=True
            )
            if not resp["InstanceStatuses"]:
                return {"instance_id": instance_id, "state": "unknown"}
            state = resp["InstanceStatuses"][0]["InstanceState"]["Name"]
            return {"instance_id": instance_id, "state": state}
        except Exception as e:
            return {"error": str(e)}
    def get_cpu_metrics(self, instance_id: str) -> Dict[str, Any]:
        """Fetch recent CPUUtilization metrics for an instance."""
        if self.dry_run:
            return {"simulated": True, "action": f"get_cpu_metrics({instance_id})"}

        try:
            end = datetime.datetime.utcnow()
            start = end - datetime.timedelta(minutes=30)

            resp = self.cloudwatch.get_metric_statistics(
                Namespace="AWS/EC2",
                MetricName="CPUUtilization",
                Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
                StartTime=start,
                EndTime=end,
                Period=300,
                Statistics=["Average", "Maximum"]
            )

            metrics = sorted(resp.get("Datapoints", []), key=lambda x: x["Timestamp"])
            return {
                "InstanceId": instance_id,
                "metrics": metrics,
                "PeriodMinutes": 30
            }

        except Exception as e:
            return {"error": str(e), "instance_id": instance_id}