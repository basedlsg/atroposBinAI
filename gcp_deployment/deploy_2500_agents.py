#!/usr/bin/env python3
"""
Cloud Deployment Script for 2,500 Agent Society Simulation
Deploys agents across multiple Google Cloud instances with Groq API integration
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, List

import aiohttp
import requests
from google.cloud import compute_v1


class CloudAgentDeployer:
    """Manages deployment of 2,500 agents across cloud instances"""
    
    def __init__(self, project_id: str, zone: str = "us-central1-a"):
        self.project_id = project_id
        self.zone = zone
        self.compute_client = compute_v1.InstancesClient()
        self.groq_api_keys = self.load_groq_keys()
        
        # Configure logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def load_groq_keys(self) -> List[str]:
        """Load multiple Groq API keys for rate limit distribution"""
        keys = []
        
        # Primary key from environment
        primary_key = os.getenv("GROQ_API_KEY")
        if primary_key:
            keys.append(primary_key)
        
        # Additional keys from file if available
        try:
            with open("groq_keys.json", "r") as f:
                additional_keys = json.load(f)
                keys.extend(additional_keys.get("keys", []))
        except FileNotFoundError:
            self.logger.warning("No additional Groq keys file found")
        
        if not keys:
            raise ValueError("No Groq API keys available")
        
        self.logger.info(f"Loaded {len(keys)} Groq API keys")
        return keys
    
    async def deploy_2500_agents(self, deployment_config: Dict) -> Dict:
        """Deploy 2,500 agents across cloud instances"""
        
        self.logger.info("🚀 Starting 2,500 agent cloud deployment")
        
        # Deployment configuration
        total_agents = 2500
        instances = deployment_config.get("instances", 5)
        agents_per_instance = total_agents // instances
        
        self.logger.info(f"Deploying {total_agents} agents across {instances} instances")
        self.logger.info(f"Agents per instance: {agents_per_instance}")
        
        # Create instances
        instance_names = await self.create_instances(instances, deployment_config)
        
        # Wait for instances to be ready
        await self.wait_for_instances_ready(instance_names)
        
        # Deploy agents to instances
        deployment_results = await self.deploy_agents_to_instances(
            instance_names, agents_per_instance, deployment_config
        )
        
        # Monitor simulation
        monitoring_results = await self.monitor_simulation(
            instance_names, deployment_config.get("simulation_duration", "3_hours")
        )
        
        # Collect results
        final_results = await self.collect_results(instance_names)
        
        # Cleanup instances (optional)
        if deployment_config.get("cleanup", True):
            await self.cleanup_instances(instance_names)
        
        return {
            "deployment_results": deployment_results,
            "monitoring_results": monitoring_results,
            "final_results": final_results,
            "total_agents": total_agents,
            "instances_used": len(instance_names),
            "deployment_timestamp": datetime.utcnow().isoformat()
        }
    
    async def create_instances(self, count: int, config: Dict) -> List[str]:
        """Create cloud instances for agent deployment"""
        
        self.logger.info(f"Creating {count} cloud instances")
        
        instance_names = []
        
        for i in range(count):
            instance_name = f"agent-simulation-{int(time.time())}-{i}"
            
            # Instance configuration
            instance_config = {
                "name": instance_name,
                "machine_type": f"zones/{self.zone}/machineTypes/{config.get('instance_type', 'c2-standard-16')}",
                "disks": [{
                    "boot": True,
                    "auto_delete": True,
                    "initialize_params": {
                        "source_image": "projects/debian-cloud/global/images/family/debian-11",
                        "disk_size_gb": "100"
                    }
                }],
                "network_interfaces": [{
                    "network": "global/networks/default",
                    "access_configs": [{"type": "ONE_TO_ONE_NAT"}]
                }],
                "service_accounts": [{
                    "email": "default",
                    "scopes": ["https://www.googleapis.com/auth/cloud-platform"]
                }],
                "metadata": {
                    "items": [{
                        "key": "startup-script",
                        "value": self.generate_startup_script(config)
                    }]
                }
            }
            
            # Create instance
            operation = self.compute_client.insert(
                project=self.project_id,
                zone=self.zone,
                instance_resource=instance_config
            )
            
            instance_names.append(instance_name)
            self.logger.info(f"Created instance: {instance_name}")
        
        return instance_names
    
    def generate_startup_script(self, config: Dict) -> str:
        """Generate startup script for cloud instances"""
        
        script = f"""#!/bin/bash
# Startup script for 2,500 agent simulation

# Update system
apt-get update
apt-get install -y python3 python3-pip git

# Install Python dependencies
pip3 install groq requests aiohttp mesa numpy pandas

# Set environment variables
export GROQ_API_KEY="{self.groq_api_keys[0]}"
export SIMULATION_CONFIG='{json.dumps(config)}'

# Clone simulation code (if needed)
# git clone https://github.com/your-repo/simulation.git /opt/simulation

# Create simulation directory
mkdir -p /opt/simulation
cd /opt/simulation

# Create agent simulation script
cat > agent_simulation.py << 'EOF'
{self.get_agent_simulation_code()}
EOF

# Make script executable
chmod +x agent_simulation.py

# Start simulation
python3 agent_simulation.py > /var/log/simulation.log 2>&1 &

# Create status endpoint
cat > status_server.py << 'EOF'
{self.get_status_server_code()}
EOF

# Start status server
python3 status_server.py > /var/log/status.log 2>&1 &
"""
        
        return script
    
    def get_agent_simulation_code(self) -> str:
        """Get the agent simulation code to run on instances"""
        
        return '''
import asyncio
import json
import os
import time
from datetime import datetime
from typing import Dict, List

import aiohttp
import numpy as np


class CloudAgent:
    """Individual agent running in cloud simulation"""
    
    def __init__(self, agent_id: int, groq_api_key: str):
        self.id = agent_id
        self.groq_api_key = groq_api_key
        self.position = np.random.uniform(0, 100, 2)
        self.energy = np.random.uniform(0.5, 1.0)
        self.happiness = np.random.uniform(0.3, 0.8)
        self.wealth = np.random.uniform(100, 1000)
        self.beliefs = self.generate_initial_beliefs()
        self.connections = []
        self.history = []
    
    def generate_initial_beliefs(self) -> Dict:
        """Generate initial belief system for agent"""
        beliefs = {
            "cooperation_value": np.random.uniform(0.3, 0.9),
            "authority_respect": np.random.uniform(0.2, 0.8),
            "innovation_openness": np.random.uniform(0.4, 0.9),
            "resource_sharing": np.random.uniform(0.3, 0.8),
            "conflict_avoidance": np.random.uniform(0.4, 0.9)
        }
        return beliefs
    
    async def make_decision(self, context: Dict) -> Dict:
        """Make decision using Groq API"""
        
        prompt = f"""
        You are Agent {self.id} in a society simulation.
        
        Current Status:
        - Energy: {self.energy:.2f}
        - Happiness: {self.happiness:.2f}
        - Wealth: {self.wealth:.0f}
        - Beliefs: {json.dumps(self.beliefs, indent=2)}
        
        Context: {json.dumps(context, indent=2)}
        
        Based on your current status and beliefs, what action do you take?
        Respond with a JSON object containing:
        - action: (move, trade, cooperate, compete, rest, innovate)
        - target: (agent_id if applicable)
        - reasoning: (brief explanation)
        - belief_change: (any belief updates as a dict)
        """
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.groq_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "llama-3.1-8b-instant",
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 200,
                        "temperature": 0.7
                    }
                ) as response:
                    result = await response.json()
                    
                    if response.status == 200:
                        content = result["choices"][0]["message"]["content"]
                        try:
                            decision = json.loads(content)
                            return decision
                        except json.JSONDecodeError:
                            return {"action": "rest", "reasoning": "Failed to parse decision"}
                    else:
                        return {"action": "rest", "reasoning": "API error"}
        
        except Exception as e:
            return {"action": "rest", "reasoning": f"Error: {str(e)}"}
    
    def update_state(self, decision: Dict, interactions: List):
        """Update agent state based on decision and interactions"""
        
        # Update beliefs if specified
        if "belief_change" in decision and decision["belief_change"]:
            for belief, change in decision["belief_change"].items():
                if belief in self.beliefs:
                    self.beliefs[belief] = np.clip(
                        self.beliefs[belief] + change, 0.0, 1.0
                    )
        
        # Update energy based on action
        action = decision.get("action", "rest")
        if action == "rest":
            self.energy = min(1.0, self.energy + 0.1)
        else:
            self.energy = max(0.0, self.energy - 0.05)
        
        # Update happiness based on interactions
        if interactions:
            avg_interaction_quality = np.mean([i.get("quality", 0.5) for i in interactions])
            self.happiness += (avg_interaction_quality - 0.5) * 0.1
            self.happiness = np.clip(self.happiness, 0.0, 1.0)
        
        # Record history
        self.history.append({
            "timestamp": datetime.utcnow().isoformat(),
            "decision": decision,
            "energy": self.energy,
            "happiness": self.happiness,
            "wealth": self.wealth,
            "beliefs": self.beliefs.copy()
        })


class CloudSimulation:
    """Manages agents on a single cloud instance"""
    
    def __init__(self, n_agents: int, groq_api_key: str):
        self.n_agents = n_agents
        self.groq_api_key = groq_api_key
        self.agents = []
        self.step_count = 0
        self.results = []
        
        # Create agents
        for i in range(n_agents):
            agent = CloudAgent(i, groq_api_key)
            self.agents.append(agent)
    
    async def run_simulation(self, duration_hours: int = 3):
        """Run simulation for specified duration"""
        
        print(f"🚀 Starting simulation with {self.n_agents} agents")
        print(f"Duration: {duration_hours} hours")
        
        start_time = time.time()
        end_time = start_time + (duration_hours * 3600)
        
        while time.time() < end_time:
            await self.simulation_step()
            
            # Progress update
            if self.step_count % 10 == 0:
                elapsed = time.time() - start_time
                remaining = end_time - time.time()
                print(f"Step {self.step_count}: {elapsed/60:.1f}m elapsed, {remaining/60:.1f}m remaining")
            
            # Small delay to prevent overwhelming API
            await asyncio.sleep(1)
        
        print(f"✅ Simulation completed: {self.step_count} steps")
        return self.get_final_results()
    
    async def simulation_step(self):
        """Execute one simulation step"""
        
        # Get decisions from all agents
        decisions = []
        for agent in self.agents:
            context = self.get_agent_context(agent)
            decision = await agent.make_decision(context)
            decisions.append((agent, decision))
        
        # Process interactions
        interactions = self.process_interactions(decisions)
        
        # Update agent states
        for agent, decision in decisions:
            agent_interactions = [i for i in interactions if agent.id in i.get("participants", [])]
            agent.update_state(decision, agent_interactions)
        
        # Record step results
        step_result = {
            "step": self.step_count,
            "timestamp": datetime.utcnow().isoformat(),
            "avg_energy": np.mean([a.energy for a in self.agents]),
            "avg_happiness": np.mean([a.happiness for a in self.agents]),
            "total_wealth": sum([a.wealth for a in self.agents]),
            "decisions": [d[1] for d in decisions],
            "interactions": interactions
        }
        
        self.results.append(step_result)
        self.step_count += 1
    
    def get_agent_context(self, agent) -> Dict:
        """Get context for agent decision making"""
        
        # Find nearby agents
        nearby_agents = []
        for other in self.agents:
            if other.id != agent.id:
                distance = np.linalg.norm(agent.position - other.position)
                if distance < 20:  # Within interaction range
                    nearby_agents.append({
                        "id": other.id,
                        "distance": distance,
                        "energy": other.energy,
                        "wealth": other.wealth
                    })
        
        return {
            "nearby_agents": nearby_agents[:5],  # Limit to 5 nearest
            "step": self.step_count,
            "avg_society_happiness": np.mean([a.happiness for a in self.agents]),
            "total_society_wealth": sum([a.wealth for a in self.agents])
        }
    
    def process_interactions(self, decisions: List) -> List:
        """Process interactions between agents"""
        
        interactions = []
        
        # Group agents by action type
        action_groups = {}
        for agent, decision in decisions:
            action = decision.get("action", "rest")
            if action not in action_groups:
                action_groups[action] = []
            action_groups[action].append((agent, decision))
        
        # Process cooperation
        if "cooperate" in action_groups:
            coop_agents = action_groups["cooperate"]
            if len(coop_agents) >= 2:
                # Random pairing for cooperation
                for i in range(0, len(coop_agents) - 1, 2):
                    agent1, decision1 = coop_agents[i]
                    agent2, decision2 = coop_agents[i + 1]
                    
                    # Cooperation benefit
                    benefit = np.random.uniform(50, 150)
                    agent1.wealth += benefit
                    agent2.wealth += benefit
                    
                    interactions.append({
                        "type": "cooperation",
                        "participants": [agent1.id, agent2.id],
                        "benefit": benefit,
                        "quality": 0.8
                    })
        
        # Process competition
        if "compete" in action_groups:
            comp_agents = action_groups["compete"]
            if len(comp_agents) >= 2:
                # Random competition
                for i in range(0, len(comp_agents) - 1, 2):
                    agent1, decision1 = comp_agents[i]
                    agent2, decision2 = comp_agents[i + 1]
                    
                    # Competition outcome
                    if np.random.random() > 0.5:
                        winner, loser = agent1, agent2
                    else:
                        winner, loser = agent2, agent1
                    
                    transfer = np.random.uniform(20, 100)
                    winner.wealth += transfer
                    loser.wealth = max(0, loser.wealth - transfer)
                    
                    interactions.append({
                        "type": "competition",
                        "participants": [agent1.id, agent2.id],
                        "winner": winner.id,
                        "transfer": transfer,
                        "quality": 0.3
                    })
        
        return interactions
    
    def get_final_results(self) -> Dict:
        """Get final simulation results"""
        
        return {
            "simulation_type": "cloud_2500_agents",
            "n_agents": self.n_agents,
            "total_steps": self.step_count,
            "final_metrics": {
                "avg_energy": np.mean([a.energy for a in self.agents]),
                "avg_happiness": np.mean([a.happiness for a in self.agents]),
                "total_wealth": sum([a.wealth for a in self.agents]),
                "wealth_distribution": {
                    "min": min([a.wealth for a in self.agents]),
                    "max": max([a.wealth for a in self.agents]),
                    "std": np.std([a.wealth for a in self.agents])
                }
            },
            "agent_histories": [a.history[-5:] for a in self.agents],  # Last 5 steps
            "step_results": self.results[-10:],  # Last 10 steps
            "timestamp": datetime.utcnow().isoformat()
        }


# Main execution
if __name__ == "__main__":
    # Get configuration from environment
    config = json.loads(os.getenv("SIMULATION_CONFIG", "{}"))
    groq_api_key = os.getenv("GROQ_API_KEY")
    
    # Default configuration
    n_agents = config.get("agents_per_instance", 500)
    duration_hours = config.get("duration_hours", 3)
    
    # Run simulation
    simulation = CloudSimulation(n_agents, groq_api_key)
    
    # Save results
    async def run_and_save():
        results = await simulation.run_simulation(duration_hours)
        
        # Save to file
        with open("/opt/simulation/results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        print("✅ Results saved to /opt/simulation/results.json")
    
    asyncio.run(run_and_save())
'''
    
    def get_status_server_code(self) -> str:
        """Get status server code for monitoring"""
        
        return '''
import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler


class StatusHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/status":
            try:
                with open("/opt/simulation/results.json", "r") as f:
                    results = json.load(f)
                
                status = {
                    "status": "running",
                    "last_update": results.get("timestamp", "unknown"),
                    "total_steps": results.get("total_steps", 0),
                    "final_metrics": results.get("final_metrics", {})
                }
            except FileNotFoundError:
                status = {"status": "starting", "message": "Simulation not yet started"}
            
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(status).encode())
        else:
            self.send_response(404)
            self.end_headers()


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8080), StatusHandler)
    server.serve_forever()
'''
    
    async def wait_for_instances_ready(self, instance_names: List[str]):
        """Wait for instances to be ready"""
        
        self.logger.info("Waiting for instances to be ready...")
        
        for instance_name in instance_names:
            while True:
                instance = self.compute_client.get(
                    project=self.project_id,
                    zone=self.zone,
                    instance=instance_name
                )
                
                if instance.status == "RUNNING":
                    self.logger.info(f"Instance {instance_name} is ready")
                    break
                
                await asyncio.sleep(10)
        
        # Additional wait for startup script to complete
        self.logger.info("Waiting for startup scripts to complete...")
        await asyncio.sleep(120)  # 2 minutes for startup
    
    async def deploy_agents_to_instances(self, instance_names: List[str], 
                                       agents_per_instance: int, config: Dict) -> Dict:
        """Deploy agents to running instances"""
        
        self.logger.info("Deploying agents to instances...")
        
        deployment_results = {}
        
        for i, instance_name in enumerate(instance_names):
            # Get instance external IP
            instance = self.compute_client.get(
                project=self.project_id,
                zone=self.zone,
                instance=instance_name
            )
            
            external_ip = instance.network_interfaces[0].access_configs[0].nat_ip
            
            # Check if simulation is running
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"http://{external_ip}:8080/status") as response:
                        if response.status == 200:
                            status = await response.json()
                            deployment_results[instance_name] = {
                                "status": "deployed",
                                "external_ip": external_ip,
                                "agents": agents_per_instance,
                                "simulation_status": status
                            }
                        else:
                            deployment_results[instance_name] = {
                                "status": "error",
                                "external_ip": external_ip,
                                "error": "Status endpoint not responding"
                            }
            except Exception as e:
                deployment_results[instance_name] = {
                    "status": "error",
                    "external_ip": external_ip,
                    "error": str(e)
                }
        
        return deployment_results
    
    async def monitor_simulation(self, instance_names: List[str], duration: str) -> Dict:
        """Monitor simulation progress"""
        
        self.logger.info(f"Monitoring simulation for {duration}")
        
        # Parse duration
        if duration.endswith("_hours"):
            hours = int(duration.split("_")[0])
            total_seconds = hours * 3600
        else:
            total_seconds = 3600  # Default 1 hour
        
        monitoring_results = {}
        start_time = time.time()
        
        while time.time() - start_time < total_seconds:
            for instance_name in instance_names:
                try:
                    instance = self.compute_client.get(
                        project=self.project_id,
                        zone=self.zone,
                        instance=instance_name
                    )
                    
                    external_ip = instance.network_interfaces[0].access_configs[0].nat_ip
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.get(f"http://{external_ip}:8080/status") as response:
                            if response.status == 200:
                                status = await response.json()
                                monitoring_results[instance_name] = status
                
                except Exception as e:
                    self.logger.warning(f"Failed to monitor {instance_name}: {e}")
            
            # Log progress
            elapsed = time.time() - start_time
            remaining = total_seconds - elapsed
            self.logger.info(f"Monitoring: {elapsed/60:.1f}m elapsed, {remaining/60:.1f}m remaining")
            
            await asyncio.sleep(60)  # Check every minute
        
        return monitoring_results
    
    async def collect_results(self, instance_names: List[str]) -> Dict:
        """Collect final results from all instances"""
        
        self.logger.info("Collecting final results...")
        
        all_results = {}
        
        for instance_name in instance_names:
            try:
                instance = self.compute_client.get(
                    project=self.project_id,
                    zone=self.zone,
                    instance=instance_name
                )
                
                external_ip = instance.network_interfaces[0].access_configs[0].nat_ip
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"http://{external_ip}:8080/status") as response:
                        if response.status == 200:
                            results = await response.json()
                            all_results[instance_name] = results
            
            except Exception as e:
                self.logger.error(f"Failed to collect results from {instance_name}: {e}")
        
        # Aggregate results
        aggregated = self.aggregate_results(all_results)
        
        return {
            "individual_results": all_results,
            "aggregated_results": aggregated,
            "collection_timestamp": datetime.utcnow().isoformat()
        }
    
    def aggregate_results(self, all_results: Dict) -> Dict:
        """Aggregate results from all instances"""
        
        total_agents = 0
        total_steps = 0
        all_metrics = []
        
        for instance_name, results in all_results.items():
            if "final_metrics" in results:
                total_agents += results.get("n_agents", 0)
                total_steps += results.get("total_steps", 0)
                all_metrics.append(results["final_metrics"])
        
        if all_metrics:
            aggregated_metrics = {
                "total_agents": total_agents,
                "avg_steps_per_instance": total_steps / len(all_results) if all_results else 0,
                "overall_avg_energy": sum(m.get("avg_energy", 0) for m in all_metrics) / len(all_metrics),
                "overall_avg_happiness": sum(m.get("avg_happiness", 0) for m in all_metrics) / len(all_metrics),
                "total_wealth": sum(m.get("total_wealth", 0) for m in all_metrics),
                "instances_completed": len(all_results)
            }
        else:
            aggregated_metrics = {"error": "No valid results collected"}
        
        return aggregated_metrics
    
    async def cleanup_instances(self, instance_names: List[str]):
        """Clean up cloud instances"""
        
        self.logger.info("Cleaning up instances...")
        
        for instance_name in instance_names:
            try:
                operation = self.compute_client.delete(
                    project=self.project_id,
                    zone=self.zone,
                    instance=instance_name
                )
                self.logger.info(f"Deleted instance: {instance_name}")
            except Exception as e:
                self.logger.error(f"Failed to delete {instance_name}: {e}")


async def main():
    """Main deployment function"""
    
    # Configuration
    deployment_config = {
        "instances": 5,
        "instance_type": "c2-standard-16",
        "agents_per_instance": 500,
        "simulation_duration": "3_hours",
        "duration_hours": 3,
        "cleanup": True
    }
    
    # Deploy
    deployer = CloudAgentDeployer(
        project_id="amien-research-pipeline",
        zone="us-central1-a"
    )
    
    results = await deployer.deploy_2500_agents(deployment_config)
    
    # Save results
    with open("2500_agent_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print("🎉 2,500 agent deployment completed!")
    print(f"Results saved to: 2500_agent_results.json")
    
    return results


if __name__ == "__main__":
    asyncio.run(main()) 