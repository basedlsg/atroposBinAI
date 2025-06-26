#!/usr/bin/env python3
"""
Google Cloud Platform Deployment Script
=======================================

Automatically provisions and deploys the God Portal system to GCP:
- Creates compute instances
- Sets up networking
- Deploys the application
- Configures monitoring
- Manages scaling
"""

import os
import json
import time
import asyncio
import subprocess
from datetime import datetime
from typing import Dict, List, Any, Optional

class GCPDeployer:
    """Handles Google Cloud Platform deployment"""
    
    def __init__(self, project_id: str = "nous-god-portal"):
        self.project_id = project_id
        self.region = "us-central1"
        self.zone = "us-central1-a"
        self.deployment_id = f"god-portal-{int(time.time())}"
        
    def check_gcp_setup(self) -> bool:
        """Check if GCP CLI is set up and authenticated"""
        try:
            # Check if gcloud is installed
            result = subprocess.run(["gcloud", "version"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                print("❌ Google Cloud CLI not found. Please install gcloud.")
                return False
            
            # Check authentication
            result = subprocess.run(["gcloud", "auth", "list"], 
                                  capture_output=True, text=True, timeout=10)
            if "ACTIVE" not in result.stdout:
                print("❌ Not authenticated with Google Cloud. Run: gcloud auth login")
                return False
            
            # Check project
            result = subprocess.run(["gcloud", "config", "get-value", "project"], 
                                  capture_output=True, text=True, timeout=10)
            current_project = result.stdout.strip()
            
            if not current_project:
                print(f"⚠️  No project set. Setting to {self.project_id}")
                subprocess.run(["gcloud", "config", "set", "project", self.project_id])
            
            print(f"✅ GCP setup verified. Project: {current_project or self.project_id}")
            return True
            
        except subprocess.TimeoutExpired:
            print("❌ GCP CLI commands timed out")
            return False
        except Exception as e:
            print(f"❌ GCP setup check failed: {e}")
            return False
    
    def create_startup_script(self) -> str:
        """Create startup script for compute instances"""
        
        startup_script = f'''#!/bin/bash
# God Portal Cloud Instance Startup Script
set -e

echo "🚀 Starting God Portal instance setup..."

# Update system
apt-get update
apt-get install -y python3 python3-pip git

# Create application directory
mkdir -p /opt/god-portal
cd /opt/god-portal

# Copy application files (would be from Cloud Storage in production)
cat > cloud_god_portal.py << 'EOF'
{self._get_application_code()}
EOF

cat > requirements.txt << 'EOF'
groq>=0.4.0
numpy>=1.21.0
aiohttp>=3.8.0
asyncio-throttle>=1.0.0
EOF

# Install Python dependencies
pip3 install -r requirements.txt

# Set environment variables
export GROQ_API_KEY="{os.getenv('GROQ_API_KEY', '')}"
export INSTANCE_ID="$(curl -H 'Metadata-Flavor: Google' http://metadata.google.internal/computeMetadata/v1/instance/id)"
export INSTANCE_NAME="$(curl -H 'Metadata-Flavor: Google' http://metadata.google.internal/computeMetadata/v1/instance/name)"

# Create systemd service
cat > /etc/systemd/system/god-portal.service << 'EOF'
[Unit]
Description=God Portal Agent Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/god-portal
Environment=GROQ_API_KEY={os.getenv('GROQ_API_KEY', '')}
ExecStart=/usr/bin/python3 cloud_god_portal.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
systemctl daemon-reload
systemctl enable god-portal
systemctl start god-portal

echo "✅ God Portal instance setup complete"
'''
        return startup_script
    
    def _get_application_code(self) -> str:
        """Get the application code to embed in startup script"""
        try:
            with open('cloud_god_portal.py', 'r') as f:
                return f.read()
        except FileNotFoundError:
            # Fallback minimal code
            return '''
import asyncio
import time
import json
from datetime import datetime

async def main():
    print("🌐 God Portal Cloud Instance Running")
    print(f"Instance started at: {datetime.now()}")
    
    # Simulate work for demo
    for i in range(10):
        print(f"Processing batch {i+1}/10...")
        await asyncio.sleep(2)
    
    print("✅ Instance work completed")

if __name__ == "__main__":
    asyncio.run(main())
'''
    
    def create_instance_template(self) -> Dict[str, Any]:
        """Create compute instance template"""
        
        startup_script = self.create_startup_script()
        
        template = {
            "name": f"{self.deployment_id}-template",
            "properties": {
                "machineType": f"zones/{self.zone}/machineTypes/c2-standard-4",
                "disks": [
                    {
                        "boot": True,
                        "autoDelete": True,
                        "initializeParams": {
                            "sourceImage": "projects/ubuntu-os-cloud/global/images/family/ubuntu-2004-lts",
                            "diskSizeGb": "50",
                            "diskType": f"zones/{self.zone}/diskTypes/pd-ssd"
                        }
                    }
                ],
                "networkInterfaces": [
                    {
                        "network": "global/networks/default",
                        "accessConfigs": [
                            {
                                "type": "ONE_TO_ONE_NAT",
                                "name": "External NAT"
                            }
                        ]
                    }
                ],
                "metadata": {
                    "items": [
                        {
                            "key": "startup-script",
                            "value": startup_script
                        },
                        {
                            "key": "deployment-id",
                            "value": self.deployment_id
                        }
                    ]
                },
                "tags": {
                    "items": ["god-portal", "http-server", "https-server"]
                },
                "serviceAccounts": [
                    {
                        "email": "default",
                        "scopes": [
                            "https://www.googleapis.com/auth/cloud-platform"
                        ]
                    }
                ]
            }
        }
        
        return template
    
    async def deploy_to_gcp(self, num_instances: int = 5) -> Dict[str, Any]:
        """Deploy the God Portal system to GCP"""
        
        print(f"🌐 Starting GCP deployment: {self.deployment_id}")
        print(f"   Project: {self.project_id}")
        print(f"   Region: {self.region}")
        print(f"   Instances: {num_instances}")
        
        deployment_start = time.time()
        deployment_results = {
            "deployment_id": self.deployment_id,
            "start_time": datetime.now().isoformat(),
            "project_id": self.project_id,
            "region": self.region,
            "instances": [],
            "status": "starting"
        }
        
        try:
            # Check GCP setup
            if not self.check_gcp_setup():
                deployment_results["status"] = "failed"
                deployment_results["error"] = "GCP setup check failed"
                return deployment_results
            
            # Create instances
            print(f"\n📦 Creating {num_instances} compute instances...")
            
            for i in range(num_instances):
                instance_name = f"{self.deployment_id}-instance-{i}"
                
                print(f"   Creating instance: {instance_name}")
                
                # Create instance using gcloud command
                cmd = [
                    "gcloud", "compute", "instances", "create", instance_name,
                    "--zone", self.zone,
                    "--machine-type", "c2-standard-4",
                    "--image-family", "ubuntu-2004-lts",
                    "--image-project", "ubuntu-os-cloud",
                    "--boot-disk-size", "50GB",
                    "--boot-disk-type", "pd-ssd",
                    "--tags", "god-portal,http-server",
                    "--metadata", f"startup-script={self.create_startup_script()}",
                    "--metadata", f"deployment-id={self.deployment_id}",
                    "--metadata", f"instance-role=god-portal-agent",
                    "--scopes", "cloud-platform",
                    "--format", "json"
                ]
                
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                    
                    if result.returncode == 0:
                        instance_data = json.loads(result.stdout)[0]
                        deployment_results["instances"].append({
                            "name": instance_name,
                            "status": "created",
                            "zone": self.zone,
                            "internal_ip": instance_data.get("networkInterfaces", [{}])[0].get("networkIP"),
                            "external_ip": instance_data.get("networkInterfaces", [{}])[0].get("accessConfigs", [{}])[0].get("natIP")
                        })
                        print(f"   ✅ {instance_name} created successfully")
                    else:
                        print(f"   ❌ Failed to create {instance_name}: {result.stderr}")
                        deployment_results["instances"].append({
                            "name": instance_name,
                            "status": "failed",
                            "error": result.stderr
                        })
                
                except subprocess.TimeoutExpired:
                    print(f"   ⏰ Timeout creating {instance_name}")
                    deployment_results["instances"].append({
                        "name": instance_name,
                        "status": "timeout"
                    })
                
                # Small delay between instance creations
                await asyncio.sleep(2)
            
            # Wait for instances to be ready
            print(f"\n⏳ Waiting for instances to initialize...")
            await asyncio.sleep(30)  # Give instances time to start
            
            # Check instance status
            successful_instances = 0
            for instance in deployment_results["instances"]:
                if instance["status"] == "created":
                    instance_name = instance["name"]
                    
                    # Check if instance is running
                    cmd = ["gcloud", "compute", "instances", "describe", instance_name, 
                          "--zone", self.zone, "--format", "json"]
                    
                    try:
                        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                        if result.returncode == 0:
                            instance_info = json.loads(result.stdout)
                            status = instance_info.get("status", "UNKNOWN")
                            instance["gcp_status"] = status
                            
                            if status == "RUNNING":
                                successful_instances += 1
                                print(f"   ✅ {instance_name}: RUNNING")
                            else:
                                print(f"   ⏳ {instance_name}: {status}")
                    except Exception as e:
                        print(f"   ❌ Error checking {instance_name}: {e}")
            
            # Update deployment status
            deployment_time = time.time() - deployment_start
            deployment_results.update({
                "end_time": datetime.now().isoformat(),
                "deployment_time_seconds": deployment_time,
                "successful_instances": successful_instances,
                "total_instances": num_instances,
                "success_rate": successful_instances / num_instances,
                "status": "completed" if successful_instances > 0 else "failed"
            })
            
            print(f"\n🎉 GCP Deployment Summary:")
            print(f"   ✅ Successful instances: {successful_instances}/{num_instances}")
            print(f"   ⏱️  Deployment time: {deployment_time:.1f} seconds")
            print(f"   🆔 Deployment ID: {self.deployment_id}")
            
            # Save deployment info
            filename = f"gcp_deployment_{self.deployment_id}.json"
            with open(filename, 'w') as f:
                json.dump(deployment_results, f, indent=2)
            print(f"   💾 Deployment info saved: {filename}")
            
            return deployment_results
            
        except Exception as e:
            print(f"❌ Deployment failed: {e}")
            deployment_results.update({
                "status": "failed",
                "error": str(e),
                "end_time": datetime.now().isoformat()
            })
            return deployment_results
    
    def cleanup_deployment(self, deployment_id: str = None) -> bool:
        """Clean up GCP resources from a deployment"""
        
        cleanup_id = deployment_id or self.deployment_id
        print(f"🧹 Cleaning up deployment: {cleanup_id}")
        
        try:
            # List instances with the deployment tag
            cmd = [
                "gcloud", "compute", "instances", "list",
                "--filter", f"metadata.deployment-id={cleanup_id}",
                "--format", "value(name,zone)"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and result.stdout.strip():
                instances = result.stdout.strip().split('\n')
                
                for instance_line in instances:
                    if '\t' in instance_line:
                        instance_name, zone = instance_line.split('\t')
                        
                        print(f"   Deleting instance: {instance_name}")
                        
                        delete_cmd = [
                            "gcloud", "compute", "instances", "delete", instance_name,
                            "--zone", zone,
                            "--quiet"
                        ]
                        
                        delete_result = subprocess.run(delete_cmd, capture_output=True, text=True, timeout=60)
                        
                        if delete_result.returncode == 0:
                            print(f"   ✅ Deleted: {instance_name}")
                        else:
                            print(f"   ❌ Failed to delete: {instance_name}")
                
                print(f"✅ Cleanup completed for: {cleanup_id}")
                return True
            else:
                print(f"ℹ️  No instances found for deployment: {cleanup_id}")
                return True
                
        except Exception as e:
            print(f"❌ Cleanup failed: {e}")
            return False
    
    def monitor_deployment(self, deployment_id: str = None) -> Dict[str, Any]:
        """Monitor the status of a deployment"""
        
        monitor_id = deployment_id or self.deployment_id
        print(f"📊 Monitoring deployment: {monitor_id}")
        
        try:
            # Get instances for this deployment
            cmd = [
                "gcloud", "compute", "instances", "list",
                "--filter", f"metadata.deployment-id={monitor_id}",
                "--format", "json"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                instances = json.loads(result.stdout)
                
                monitoring_data = {
                    "deployment_id": monitor_id,
                    "timestamp": datetime.now().isoformat(),
                    "total_instances": len(instances),
                    "instance_status": {},
                    "summary": {}
                }
                
                status_counts = {}
                
                for instance in instances:
                    name = instance["name"]
                    status = instance["status"]
                    zone = instance["zone"].split('/')[-1]
                    
                    monitoring_data["instance_status"][name] = {
                        "status": status,
                        "zone": zone,
                        "machine_type": instance["machineType"].split('/')[-1],
                        "internal_ip": instance.get("networkInterfaces", [{}])[0].get("networkIP"),
                        "external_ip": instance.get("networkInterfaces", [{}])[0].get("accessConfigs", [{}])[0].get("natIP")
                    }
                    
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                monitoring_data["summary"] = status_counts
                
                print(f"   📈 Instance Status Summary:")
                for status, count in status_counts.items():
                    print(f"      {status}: {count}")
                
                return monitoring_data
            else:
                print(f"❌ Failed to get instance status: {result.stderr}")
                return {"error": result.stderr}
                
        except Exception as e:
            print(f"❌ Monitoring failed: {e}")
            return {"error": str(e)}

async def main():
    """Main deployment function"""
    
    print("🌐 God Portal GCP Deployment System")
    print("=" * 50)
    
    # Check if API key is set
    if not os.getenv("GROQ_API_KEY"):
        print("⚠️  GROQ_API_KEY not set. Setting from known value...")
        os.environ["GROQ_API_KEY"] = "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"
    
    deployer = GCPDeployer()
    
    try:
        # Deploy to GCP
        print("\n🚀 Starting GCP deployment...")
        deployment_results = await deployer.deploy_to_gcp(num_instances=5)
        
        if deployment_results["status"] == "completed":
            print(f"\n🎉 Deployment successful!")
            print(f"   Deployment ID: {deployment_results['deployment_id']}")
            print(f"   Successful instances: {deployment_results['successful_instances']}")
            
            # Monitor for a bit
            print(f"\n📊 Monitoring deployment...")
            await asyncio.sleep(10)
            monitoring_data = deployer.monitor_deployment(deployment_results['deployment_id'])
            
            # Ask if user wants to keep running or cleanup
            print(f"\n🤔 Deployment is running. Options:")
            print(f"   1. Keep running (you'll need to cleanup manually later)")
            print(f"   2. Cleanup now (delete all instances)")
            
            # For demo, we'll cleanup after a short time
            print(f"\n⏳ Running simulation for 60 seconds, then cleaning up...")
            await asyncio.sleep(60)
            
            print(f"\n🧹 Cleaning up deployment...")
            cleanup_success = deployer.cleanup_deployment(deployment_results['deployment_id'])
            
            if cleanup_success:
                print(f"✅ Cleanup completed successfully")
            else:
                print(f"⚠️  Cleanup had issues. Check GCP console manually.")
                
        else:
            print(f"❌ Deployment failed: {deployment_results.get('error', 'Unknown error')}")
            
    except KeyboardInterrupt:
        print(f"\n⚠️  Deployment interrupted. Cleaning up...")
        deployer.cleanup_deployment()
    except Exception as e:
        print(f"❌ Fatal deployment error: {e}")

if __name__ == "__main__":
    print("🌐 Starting God Portal GCP Deployment...")
    asyncio.run(main()) 