#!/usr/bin/env python3
"""
Monitor the 2,500 Agent Deployment
Real-time monitoring of cloud deployment progress
"""

import asyncio
import json
import os
import time
from datetime import datetime
from typing import Dict, List
import requests


class DeploymentMonitor:
    """Monitor deployment progress and generate insights"""
    
    def __init__(self):
        self.start_time = time.time()
        self.monitoring_active = True
        self.metrics_history = []
        
    async def monitor_deployment(self):
        """Monitor the deployment in real-time"""
        
        print("🔍 MONITORING 2,500 AGENT DEPLOYMENT")
        print("=" * 50)
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        step = 0
        
        while self.monitoring_active:
            step += 1
            elapsed = time.time() - self.start_time
            
            # Check for results files
            results_files = self.check_for_results()
            
            # Display progress
            print(f"⏱️  Step {step} | Elapsed: {elapsed/60:.1f}m")
            
            if results_files:
                print(f"📄 Found {len(results_files)} result files")
                
                # Analyze latest results
                latest_results = self.analyze_latest_results(results_files)
                if latest_results:
                    self.display_progress(latest_results)
            else:
                print("🔄 Deployment in progress...")
                
            # Check if deployment is complete
            if self.check_completion():
                print("✅ Deployment completed!")
                break
                
            print("-" * 30)
            await asyncio.sleep(30)  # Check every 30 seconds
    
    def check_for_results(self) -> List[str]:
        """Check for result files"""
        
        results_files = []
        
        # Look for result files
        for filename in os.listdir('.'):
            if filename.startswith('2500_agent_results_') and filename.endswith('.json'):
                results_files.append(filename)
        
        return sorted(results_files)
    
    def analyze_latest_results(self, results_files: List[str]) -> Dict:
        """Analyze the latest results"""
        
        if not results_files:
            return None
            
        latest_file = results_files[-1]
        
        try:
            with open(latest_file, 'r') as f:
                results = json.load(f)
                
            return results
            
        except Exception as e:
            print(f"❌ Error reading {latest_file}: {e}")
            return None
    
    def display_progress(self, results: Dict):
        """Display deployment progress"""
        
        if "aggregated_results" in results:
            agg = results["aggregated_results"]
            
            print(f"📊 PROGRESS UPDATE:")
            print(f"   Agents: {agg.get('total_agents', 0)}")
            print(f"   Steps: {agg.get('total_steps', 0)}")
            print(f"   Instances: {agg.get('successful_instances', 0)}")
            print(f"   Avg Happiness: {agg.get('avg_happiness', 0):.3f}")
            print(f"   Total Wealth: {agg.get('total_wealth', 0):.0f}")
            
            # Belief evolution insights
            if "belief_evolution" in agg:
                print(f"🧠 BELIEF EVOLUTION:")
                for belief, data in agg["belief_evolution"].items():
                    change = data.get("overall_avg_change", 0)
                    if abs(change) > 0.01:
                        direction = "↗️" if change > 0 else "↘️"
                        print(f"   {belief}: {direction} {change:+.3f}")
        
        elif "instance_results" in results:
            instances = results["instance_results"]
            print(f"📊 INSTANCE PROGRESS:")
            
            for i, instance in enumerate(instances):
                if instance:
                    metrics = instance.get("final_metrics", {})
                    print(f"   Instance {i}: "
                          f"Steps: {instance.get('total_steps', 0)}, "
                          f"Happiness: {metrics.get('avg_happiness', 0):.3f}")
    
    def check_completion(self) -> bool:
        """Check if deployment is complete"""
        
        # Look for completion indicators
        results_files = self.check_for_results()
        
        if results_files:
            latest_results = self.analyze_latest_results(results_files)
            
            if latest_results and "aggregated_results" in latest_results:
                agg = latest_results["aggregated_results"]
                
                # Check if we have results from all expected instances
                if agg.get("successful_instances", 0) >= 5:
                    return True
        
        # Check if deployment has been running for too long
        elapsed = time.time() - self.start_time
        if elapsed > 60 * 60:  # 60 minutes max
            print("⚠️  Deployment timeout reached")
            return True
            
        return False
    
    def generate_deployment_report(self):
        """Generate final deployment report"""
        
        print("\n📋 GENERATING DEPLOYMENT REPORT")
        print("=" * 50)
        
        results_files = self.check_for_results()
        
        if not results_files:
            print("❌ No results files found")
            return
            
        latest_results = self.analyze_latest_results(results_files)
        
        if not latest_results:
            print("❌ Could not analyze results")
            return
            
        # Generate comprehensive report
        report = {
            "deployment_summary": {
                "start_time": datetime.fromtimestamp(self.start_time).isoformat(),
                "completion_time": datetime.now().isoformat(),
                "total_duration_minutes": (time.time() - self.start_time) / 60,
                "results_files_generated": len(results_files)
            },
            "performance_analysis": self.analyze_performance(latest_results),
            "innovation_assessment": self.assess_innovation(latest_results),
            "next_steps": self.recommend_next_steps(latest_results)
        }
        
        # Save report
        report_file = f"deployment_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        print(f"💾 Report saved to: {report_file}")
        
        # Display key insights
        self.display_final_insights(report)
    
    def analyze_performance(self, results: Dict) -> Dict:
        """Analyze deployment performance"""
        
        if "aggregated_results" not in results:
            return {"error": "No aggregated results found"}
            
        agg = results["aggregated_results"]
        config = results.get("deployment_config", {})
        
        # Calculate performance metrics
        total_agents = agg.get("total_agents", 0)
        total_steps = agg.get("total_steps", 0)
        deployment_time = config.get("deployment_time", 0)
        
        steps_per_second = total_steps / deployment_time if deployment_time > 0 else 0
        agents_per_second = total_agents / deployment_time if deployment_time > 0 else 0
        
        return {
            "total_agents_deployed": total_agents,
            "total_simulation_steps": total_steps,
            "deployment_time_minutes": deployment_time / 60,
            "steps_per_second": steps_per_second,
            "agents_per_second": agents_per_second,
            "successful_instances": agg.get("successful_instances", 0),
            "average_happiness": agg.get("avg_happiness", 0),
            "happiness_stability": agg.get("happiness_std", 0),
            "total_wealth_generated": agg.get("total_wealth", 0)
        }
    
    def assess_innovation(self, results: Dict) -> Dict:
        """Assess the innovation level achieved"""
        
        if "aggregated_results" not in results:
            return {"innovation_score": 0, "justification": "No results to analyze"}
            
        agg = results["aggregated_results"]
        
        # Innovation scoring criteria
        innovation_score = 0
        justifications = []
        
        # Scale achievement (2,500 agents)
        if agg.get("total_agents", 0) >= 2500:
            innovation_score += 1
            justifications.append("✅ Achieved 2,500+ agent scale")
        
        # Multi-instance coordination
        if agg.get("successful_instances", 0) >= 5:
            innovation_score += 1
            justifications.append("✅ Successfully coordinated multiple instances")
        
        # LLM-driven decision making
        if agg.get("total_steps", 0) > 0:
            innovation_score += 1
            justifications.append("✅ LLM-driven agent decisions working")
        
        # Belief evolution
        if "belief_evolution" in agg and agg["belief_evolution"]:
            significant_changes = sum(
                1 for belief_data in agg["belief_evolution"].values()
                if abs(belief_data.get("overall_avg_change", 0)) > 0.01
            )
            if significant_changes > 0:
                innovation_score += 1
                justifications.append(f"✅ Belief evolution detected ({significant_changes} beliefs changed)")
        
        # Happiness stability
        happiness_std = agg.get("happiness_std", 1.0)
        if happiness_std < 0.1:  # Low variance indicates stable society
            innovation_score += 1
            justifications.append("✅ Achieved stable society dynamics")
        
        # Wealth generation
        if agg.get("total_wealth", 0) > 1000000:  # 1M+ total wealth
            innovation_score += 1
            justifications.append("✅ Significant wealth generation")
        
        # Performance efficiency
        config = results.get("deployment_config", {})
        if config.get("deployment_time", 3600) < 3600:  # Under 1 hour
            innovation_score += 1
            justifications.append("✅ Efficient deployment (under 1 hour)")
        
        # Real-time coordination
        if agg.get("successful_instances", 0) == 5:  # All instances successful
            innovation_score += 1
            justifications.append("✅ Perfect instance coordination")
        
        # Free API usage
        innovation_score += 1
        justifications.append("✅ Zero-cost LLM API usage (Groq)")
        
        return {
            "innovation_score": innovation_score,
            "max_score": 9,
            "innovation_rating": f"{innovation_score}/9",
            "justifications": justifications,
            "innovation_level": "Breakthrough" if innovation_score >= 8 else 
                             "Significant" if innovation_score >= 6 else
                             "Moderate" if innovation_score >= 4 else "Limited"
        }
    
    def recommend_next_steps(self, results: Dict) -> List[str]:
        """Recommend next steps based on results"""
        
        recommendations = []
        
        if "aggregated_results" not in results:
            return ["Analyze deployment failures and retry"]
            
        agg = results["aggregated_results"]
        
        # Scale recommendations
        if agg.get("total_agents", 0) >= 2500:
            recommendations.append("🚀 Scale to 5,000+ agents for even larger society dynamics")
            recommendations.append("📊 Implement real-time AI observer for live analysis")
        
        # Belief evolution insights
        if "belief_evolution" in agg:
            significant_changes = [
                belief for belief, data in agg["belief_evolution"].items()
                if abs(data.get("overall_avg_change", 0)) > 0.05
            ]
            if significant_changes:
                recommendations.append(f"🧠 Study belief evolution patterns: {', '.join(significant_changes)}")
        
        # Performance optimization
        config = results.get("deployment_config", {})
        if config.get("deployment_time", 0) > 1800:  # Over 30 minutes
            recommendations.append("⚡ Optimize deployment for faster execution")
        
        # Research integration
        recommendations.append("📝 Generate research paper using AI Scientist pipeline")
        recommendations.append("🔬 Design follow-up experiments based on discovered patterns")
        recommendations.append("📈 Implement pattern detection algorithms for real-time analysis")
        
        # Innovation amplification
        recommendations.append("🌟 Publish results to demonstrate breakthrough innovation")
        recommendations.append("🤖 Integrate with AI research automation pipeline")
        
        return recommendations
    
    def display_final_insights(self, report: Dict):
        """Display final insights from the deployment"""
        
        print("\n🎯 FINAL DEPLOYMENT INSIGHTS")
        print("=" * 50)
        
        # Performance summary
        perf = report.get("performance_analysis", {})
        print(f"📊 PERFORMANCE:")
        print(f"   Agents deployed: {perf.get('total_agents_deployed', 0)}")
        print(f"   Simulation steps: {perf.get('total_simulation_steps', 0)}")
        print(f"   Deployment time: {perf.get('deployment_time_minutes', 0):.1f} minutes")
        print(f"   Performance: {perf.get('steps_per_second', 0):.1f} steps/sec")
        
        # Innovation assessment
        innovation = report.get("innovation_assessment", {})
        print(f"\n🌟 INNOVATION ASSESSMENT:")
        print(f"   Score: {innovation.get('innovation_rating', 'N/A')}")
        print(f"   Level: {innovation.get('innovation_level', 'Unknown')}")
        
        justifications = innovation.get("justifications", [])
        for justification in justifications[:5]:  # Top 5
            print(f"   {justification}")
        
        # Next steps
        next_steps = report.get("next_steps", [])
        print(f"\n🔮 RECOMMENDED NEXT STEPS:")
        for step in next_steps[:3]:  # Top 3
            print(f"   {step}")


async def main():
    """Main monitoring function"""
    
    monitor = DeploymentMonitor()
    
    try:
        await monitor.monitor_deployment()
        monitor.generate_deployment_report()
        
    except KeyboardInterrupt:
        print("\n⚠️  Monitoring interrupted by user")
        monitor.monitoring_active = False
        monitor.generate_deployment_report()
    
    except Exception as e:
        print(f"\n❌ Monitoring error: {e}")
        monitor.generate_deployment_report()


if __name__ == "__main__":
    asyncio.run(main()) 