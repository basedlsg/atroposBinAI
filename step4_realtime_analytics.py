#!/usr/bin/env python3
"""
STEP 4: Real-time Analytics Dashboard
====================================

Provides real-time monitoring and analytics for the enhanced agent system.
"""

import asyncio
import json
import time
import sqlite3
from datetime import datetime
from typing import Dict, List, Any
from collections import deque
import logging

# Import our enhanced systems
from step2_scale_testing import ScaleTestRunner

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealTimeAnalytics:
    """Real-time analytics engine for agent system monitoring"""
    
    def __init__(self, db_path: str = "analytics.db"):
        self.db_path = db_path
        self.setup_database()
        
        # Real-time data streams
        self.performance_stream = deque(maxlen=100)
        self.behavioral_stream = deque(maxlen=100)
        
        # Dashboard state
        self.dashboard_data = {
            'current_metrics': {},
            'trends': {},
            'alerts': [],
            'insights': []
        }
        
        self.is_monitoring = False
    
    def setup_database(self):
        """Setup analytics database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                decisions_per_second REAL,
                memory_usage_mb REAL,
                active_agents INTEGER,
                avg_decision_time_ms REAL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS behavioral_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                avg_cooperation REAL,
                avg_happiness REAL,
                decision_diversity INTEGER,
                dominant_action TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    async def start_monitoring(self, test_runner: ScaleTestRunner, 
                             num_agents: int = 300, monitoring_duration: int = 30):
        """Start real-time monitoring of agent system"""
        
        print(f"🔍 STARTING REAL-TIME ANALYTICS")
        print(f"   Monitoring {num_agents} agents for {monitoring_duration} seconds")
        print("=" * 60)
        
        self.is_monitoring = True
        
        # Start monitoring tasks
        monitor_task = asyncio.create_task(
            self._continuous_monitoring(test_runner, num_agents, monitoring_duration)
        )
        
        dashboard_task = asyncio.create_task(self._update_dashboard())
        
        try:
            await asyncio.gather(monitor_task, dashboard_task)
        except KeyboardInterrupt:
            print("\n⏹️  Monitoring stopped by user")
        finally:
            self.is_monitoring = False
            print("\n📊 MONITORING COMPLETE")
            await self.generate_final_report()
    
    async def _continuous_monitoring(self, test_runner: ScaleTestRunner, 
                                   num_agents: int, duration: int):
        """Continuously monitor system performance and behavior"""
        
        start_time = time.time()
        monitoring_interval = 5  # seconds
        
        while self.is_monitoring and (time.time() - start_time) < duration:
            try:
                # Run a quick simulation to get current metrics
                result = await test_runner.run_scale_test(
                    num_agents, 1, f"realtime_monitor_{int(time.time())}"
                )
                
                # Extract metrics
                performance = result['performance']
                behavior = result['behavioral_analysis']
                
                # Store in streams
                timestamp = datetime.now()
                
                perf_data = {
                    'timestamp': timestamp,
                    'decisions_per_second': performance['decisions_per_second'],
                    'memory_usage_mb': performance['avg_memory_mb'],
                    'active_agents': num_agents,
                    'avg_decision_time_ms': performance['avg_decision_time_ms']
                }
                
                behavioral_data = {
                    'timestamp': timestamp,
                    'avg_cooperation': behavior['final_avg_cooperation'],
                    'avg_happiness': behavior['final_avg_happiness'],
                    'decision_diversity': behavior['decision_diversity'],
                    'dominant_action': behavior['most_common_actions'][0][0] if behavior['most_common_actions'] else 'none'
                }
                
                self.performance_stream.append(perf_data)
                self.behavioral_stream.append(behavioral_data)
                
                # Store in database
                await self._store_metrics(perf_data, behavioral_data)
                
                print(f"   📊 {timestamp.strftime('%H:%M:%S')}: "
                      f"{performance['decisions_per_second']:.0f} dec/sec, "
                      f"coop={behavior['final_avg_cooperation']:.3f}, "
                      f"happy={behavior['final_avg_happiness']:.3f}")
                
                await asyncio.sleep(monitoring_interval)
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                await asyncio.sleep(monitoring_interval)
    
    async def _update_dashboard(self):
        """Update dashboard with current data"""
        
        while self.is_monitoring:
            try:
                if self.performance_stream and self.behavioral_stream:
                    # Get latest data
                    latest_perf = self.performance_stream[-1]
                    latest_behavior = self.behavioral_stream[-1]
                    
                    # Update dashboard
                    self.dashboard_data['current_metrics'] = {
                        'performance': latest_perf,
                        'behavior': latest_behavior,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    # Print dashboard update every 15 seconds
                    await self._print_dashboard()
                
                await asyncio.sleep(15)
                
            except Exception as e:
                logger.error(f"Dashboard update error: {e}")
                await asyncio.sleep(15)
    
    async def _store_metrics(self, perf_data: Dict, behavioral_data: Dict):
        """Store metrics in database"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO performance_metrics 
            (decisions_per_second, memory_usage_mb, active_agents, avg_decision_time_ms)
            VALUES (?, ?, ?, ?)
        ''', (
            perf_data['decisions_per_second'],
            perf_data['memory_usage_mb'],
            perf_data['active_agents'],
            perf_data['avg_decision_time_ms']
        ))
        
        cursor.execute('''
            INSERT INTO behavioral_patterns 
            (avg_cooperation, avg_happiness, decision_diversity, dominant_action)
            VALUES (?, ?, ?, ?)
        ''', (
            behavioral_data['avg_cooperation'],
            behavioral_data['avg_happiness'],
            behavioral_data['decision_diversity'],
            behavioral_data['dominant_action']
        ))
        
        conn.commit()
        conn.close()
    
    async def _print_dashboard(self):
        """Print current dashboard state"""
        
        print("\n" + "="*60)
        print("📊 REAL-TIME ANALYTICS DASHBOARD")
        print("="*60)
        
        current = self.dashboard_data.get('current_metrics', {})
        if current:
            perf = current.get('performance', {})
            behavior = current.get('behavior', {})
            
            print(f"🔥 CURRENT PERFORMANCE:")
            print(f"   • {perf.get('decisions_per_second', 0):.0f} decisions/second")
            print(f"   • {perf.get('memory_usage_mb', 0):.1f}MB memory usage")
            print(f"   • {perf.get('avg_decision_time_ms', 0):.2f}ms avg decision time")
            
            print(f"\n🧠 BEHAVIORAL METRICS:")
            print(f"   • Cooperation: {behavior.get('avg_cooperation', 0):.3f}")
            print(f"   • Happiness: {behavior.get('avg_happiness', 0):.3f}")
            print(f"   • Dominant Action: {behavior.get('dominant_action', 'unknown')}")
        
        print("="*60)
    
    async def generate_final_report(self):
        """Generate comprehensive analytics report"""
        
        print("\n📋 GENERATING FINAL ANALYTICS REPORT")
        print("="*60)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Performance summary
        cursor.execute('''
            SELECT AVG(decisions_per_second), AVG(memory_usage_mb), 
                   MIN(decisions_per_second), MAX(decisions_per_second)
            FROM performance_metrics
            WHERE timestamp > datetime('now', '-1 hour')
        ''')
        
        perf_stats = cursor.fetchone()
        if perf_stats and perf_stats[0]:
            print(f"⚡ PERFORMANCE SUMMARY:")
            print(f"   • Average: {perf_stats[0]:.0f} decisions/sec")
            print(f"   • Memory: {perf_stats[1]:.1f}MB average")
            print(f"   • Range: {perf_stats[2]:.0f} - {perf_stats[3]:.0f} decisions/sec")
        
        # Behavioral summary
        cursor.execute('''
            SELECT AVG(avg_cooperation), AVG(avg_happiness), 
                   COUNT(DISTINCT dominant_action)
            FROM behavioral_patterns
            WHERE timestamp > datetime('now', '-1 hour')
        ''')
        
        behavior_stats = cursor.fetchone()
        if behavior_stats and behavior_stats[0]:
            print(f"\n🧠 BEHAVIORAL SUMMARY:")
            print(f"   • Average Cooperation: {behavior_stats[0]:.3f}")
            print(f"   • Average Happiness: {behavior_stats[1]:.3f}")
            print(f"   • Action Diversity: {behavior_stats[2]} different actions")
        
        conn.close()
        
        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"analytics_report_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.dashboard_data, f, indent=2, default=str)
        
        print(f"\n💾 Full report saved to: {filename}")

# Main execution
async def main():
    """Run real-time analytics demonstration"""
    
    analytics = RealTimeAnalytics()
    test_runner = ScaleTestRunner()
    
    # Start monitoring with 200 agents for 25 seconds
    await analytics.start_monitoring(
        test_runner=test_runner,
        num_agents=200,
        monitoring_duration=25
    )

if __name__ == "__main__":
    asyncio.run(main())
