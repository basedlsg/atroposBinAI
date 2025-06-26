#!/usr/bin/env python3
"""
Live Society Dashboard - Real-time monitoring and control for LLM society simulation
Integrates enhanced agent communication, analytics, and visualization
"""

import json
import time
import threading
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from collections import defaultdict, deque
import sqlite3
import logging

from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import plotly.graph_objs as go
import plotly.utils
import pandas as pd
import numpy as np

# Import our enhanced systems
from integrated_enhanced_society import EnhancedSocietySimulation, Agent
from agent_communication_system import MessageBroker, NegotiationProtocol

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SimulationMetrics:
    """Real-time simulation metrics"""
    timestamp: datetime
    step: int
    total_agents: int
    active_agents: int
    total_messages: int
    negotiations_active: int
    negotiations_completed: int
    average_happiness: float
    average_wealth: float
    average_health: float
    total_wealth: float
    wealth_gini: float
    cooperation_index: float
    innovation_events: int
    trade_volume: float
    
class LiveMetricsCollector:
    """Collects and processes real-time simulation metrics"""
    
    def __init__(self, max_history=1000):
        self.max_history = max_history
        self.metrics_history = deque(maxlen=max_history)
        self.db_path = "live_simulation_metrics.db"
        self.setup_database()
        
    def setup_database(self):
        """Initialize SQLite database for metrics storage"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS simulation_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                step INTEGER,
                total_agents INTEGER,
                active_agents INTEGER,
                total_messages INTEGER,
                negotiations_active INTEGER,
                negotiations_completed INTEGER,
                average_happiness REAL,
                average_wealth REAL,
                average_health REAL,
                total_wealth REAL,
                wealth_gini REAL,
                cooperation_index REAL,
                innovation_events INTEGER,
                trade_volume REAL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS agent_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                step INTEGER,
                agent_id TEXT,
                position_x REAL,
                position_y REAL,
                health REAL,
                energy REAL,
                happiness REAL,
                wealth REAL,
                personality_data TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def collect_metrics(self, simulation: EnhancedSocietySimulation) -> SimulationMetrics:
        """Collect current simulation metrics"""
        agents = simulation.agents
        message_broker = simulation.communication_system.message_broker
        
        # Basic agent metrics
        total_agents = len(agents)
        active_agents = sum(1 for agent in agents if agent.health > 0.1)
        
        # Wealth and happiness metrics
        wealth_values = [agent.wealth for agent in agents]
        happiness_values = [agent.happiness for agent in agents]
        health_values = [agent.health for agent in agents]
        
        avg_happiness = np.mean(happiness_values) if happiness_values else 0
        avg_wealth = np.mean(wealth_values) if wealth_values else 0
        avg_health = np.mean(health_values) if health_values else 0
        total_wealth = sum(wealth_values)
        
        # Calculate Gini coefficient for wealth inequality
        wealth_gini = self.calculate_gini(wealth_values) if wealth_values else 0
        
        # Communication metrics
        total_messages = len(message_broker.message_history)
        negotiations_active = len([n for n in simulation.communication_system.negotiation_protocol.active_negotiations.values() if n['status'] == 'active'])
        negotiations_completed = len([n for n in simulation.communication_system.negotiation_protocol.active_negotiations.values() if n['status'] == 'completed'])
        
        # Calculate cooperation index based on successful negotiations and positive interactions
        cooperation_index = self.calculate_cooperation_index(simulation)
        
        # Innovation and trade metrics
        innovation_events = getattr(simulation, 'innovation_count', 0)
        trade_volume = getattr(simulation, 'total_trade_volume', 0.0)
        
        metrics = SimulationMetrics(
            timestamp=datetime.now(),
            step=simulation.current_step,
            total_agents=total_agents,
            active_agents=active_agents,
            total_messages=total_messages,
            negotiations_active=negotiations_active,
            negotiations_completed=negotiations_completed,
            average_happiness=avg_happiness,
            average_wealth=avg_wealth,
            average_health=avg_health,
            total_wealth=total_wealth,
            wealth_gini=wealth_gini,
            cooperation_index=cooperation_index,
            innovation_events=innovation_events,
            trade_volume=trade_volume
        )
        
        self.metrics_history.append(metrics)
        self.store_metrics(metrics, agents)
        return metrics
        
    def calculate_gini(self, values: List[float]) -> float:
        """Calculate Gini coefficient for inequality measurement"""
        if not values or len(values) < 2:
            return 0.0
            
        sorted_values = sorted(values)
        n = len(sorted_values)
        cumsum = np.cumsum(sorted_values)
        return (n + 1 - 2 * sum(cumsum) / cumsum[-1]) / n if cumsum[-1] > 0 else 0
        
    def calculate_cooperation_index(self, simulation: EnhancedSocietySimulation) -> float:
        """Calculate cooperation index based on agent interactions"""
        if not hasattr(simulation, 'cooperation_events'):
            return 0.5  # Default neutral cooperation
            
        positive_interactions = getattr(simulation, 'positive_interactions', 0)
        total_interactions = getattr(simulation, 'total_interactions', 1)
        
        return positive_interactions / total_interactions if total_interactions > 0 else 0.5
        
    def store_metrics(self, metrics: SimulationMetrics, agents: List[Agent]):
        """Store metrics and agent snapshots in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Store simulation metrics
        cursor.execute('''
            INSERT INTO simulation_metrics (
                timestamp, step, total_agents, active_agents, total_messages,
                negotiations_active, negotiations_completed, average_happiness,
                average_wealth, average_health, total_wealth, wealth_gini,
                cooperation_index, innovation_events, trade_volume
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            metrics.timestamp.isoformat(),
            metrics.step,
            metrics.total_agents,
            metrics.active_agents,
            metrics.total_messages,
            metrics.negotiations_active,
            metrics.negotiations_completed,
            metrics.average_happiness,
            metrics.average_wealth,
            metrics.average_health,
            metrics.total_wealth,
            metrics.wealth_gini,
            metrics.cooperation_index,
            metrics.innovation_events,
            metrics.trade_volume
        ))
        
        # Store agent snapshots (sample every 10th step to avoid database bloat)
        if metrics.step % 10 == 0:
            for agent in agents:
                cursor.execute('''
                    INSERT INTO agent_snapshots (
                        timestamp, step, agent_id, position_x, position_y,
                        health, energy, happiness, wealth, personality_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    metrics.timestamp.isoformat(),
                    metrics.step,
                    agent.agent_id,
                    agent.position[0],
                    agent.position[1],
                    agent.health,
                    agent.energy,
                    agent.happiness,
                    agent.wealth,
                    json.dumps(asdict(agent.personality))
                ))
        
        conn.commit()
        conn.close()

class LiveSocietyDashboard:
    """Real-time dashboard for LLM society simulation"""
    
    def __init__(self, host='localhost', port=5000):
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'society_simulation_2024'
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        self.host = host
        self.port = port
        self.simulation = None
        self.metrics_collector = LiveMetricsCollector()
        self.simulation_thread = None
        self.is_running = False
        
        self.setup_routes()
        self.setup_socketio_events()
        
    def setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            return self.render_dashboard()
            
        @self.app.route('/api/metrics')
        def get_metrics():
            """Get current simulation metrics"""
            if self.simulation:
                metrics = self.metrics_collector.collect_metrics(self.simulation)
                return jsonify(asdict(metrics))
            return jsonify({'error': 'No active simulation'})
            
        @self.app.route('/api/agents')
        def get_agents():
            """Get current agent states"""
            if self.simulation:
                agents_data = []
                for agent in self.simulation.agents:
                    agents_data.append({
                        'id': agent.agent_id,
                        'position': agent.position,
                        'health': agent.health,
                        'energy': agent.energy,
                        'happiness': agent.happiness,
                        'wealth': agent.wealth,
                        'personality': asdict(agent.personality)
                    })
                return jsonify(agents_data)
            return jsonify([])
            
        @self.app.route('/api/messages')
        def get_messages():
            """Get recent messages"""
            if self.simulation:
                messages = self.simulation.communication_system.message_broker.get_recent_messages(50)
                return jsonify([asdict(msg) for msg in messages])
            return jsonify([])
            
        @self.app.route('/api/start_simulation', methods=['POST'])
        def start_simulation():
            """Start the simulation"""
            config = request.json or {}
            num_agents = config.get('num_agents', 100)
            
            if not self.is_running:
                self.start_simulation_thread(num_agents)
                return jsonify({'status': 'started', 'num_agents': num_agents})
            return jsonify({'status': 'already_running'})
            
        @self.app.route('/api/stop_simulation', methods=['POST'])
        def stop_simulation():
            """Stop the simulation"""
            self.stop_simulation_thread()
            return jsonify({'status': 'stopped'})
            
        @self.app.route('/api/export_data')
        def export_data():
            """Export simulation data"""
            return self.export_simulation_data()
    
    def setup_socketio_events(self):
        """Setup SocketIO event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect():
            logger.info('Client connected to dashboard')
            emit('status', {'connected': True})
            
        @self.socketio.on('disconnect')
        def handle_disconnect():
            logger.info('Client disconnected from dashboard')
            
        @self.socketio.on('request_update')
        def handle_update_request():
            """Send current simulation state to client"""
            if self.simulation:
                metrics = self.metrics_collector.collect_metrics(self.simulation)
                emit('metrics_update', asdict(metrics))
    
    def render_dashboard(self):
        """Render the main dashboard HTML"""
        return '''
<!DOCTYPE html>
<html>
<head>
    <title>Live Society Simulation Dashboard</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .controls { background: white; padding: 15px; border-radius: 8px; margin-bottom: 20px; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-bottom: 20px; }
        .metric-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .metric-value { font-size: 2em; font-weight: bold; color: #3498db; }
        .metric-label { color: #7f8c8d; margin-top: 5px; }
        .charts-container { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .chart-container { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .status-indicator { display: inline-block; width: 12px; height: 12px; border-radius: 50%; margin-right: 8px; }
        .status-running { background: #27ae60; }
        .status-stopped { background: #e74c3c; }
        button { background: #3498db; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; margin-right: 10px; }
        button:hover { background: #2980b9; }
        button:disabled { background: #bdc3c7; cursor: not-allowed; }
        .log-container { background: #2c3e50; color: #ecf0f1; padding: 15px; border-radius: 8px; height: 200px; overflow-y: auto; font-family: monospace; font-size: 12px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🏙️ Live Society Simulation Dashboard</h1>
        <p>Real-time monitoring of LLM-driven agent society with enhanced communication</p>
        <div>
            <span class="status-indicator" id="status-indicator"></span>
            <span id="status-text">Disconnected</span>
        </div>
    </div>
    
    <div class="controls">
        <button onclick="startSimulation()" id="start-btn">Start Simulation</button>
        <button onclick="stopSimulation()" id="stop-btn">Stop Simulation</button>
        <button onclick="exportData()">Export Data</button>
        <label>Agents: <input type="number" id="num-agents" value="100" min="10" max="1000"></label>
    </div>
    
    <div class="metrics-grid">
        <div class="metric-card">
            <div class="metric-value" id="total-agents">0</div>
            <div class="metric-label">Total Agents</div>
        </div>
        <div class="metric-card">
            <div class="metric-value" id="avg-happiness">0.0</div>
            <div class="metric-label">Average Happiness</div>
        </div>
        <div class="metric-card">
            <div class="metric-value" id="avg-wealth">$0</div>
            <div class="metric-label">Average Wealth</div>
        </div>
        <div class="metric-card">
            <div class="metric-value" id="total-messages">0</div>
            <div class="metric-label">Total Messages</div>
        </div>
        <div class="metric-card">
            <div class="metric-value" id="active-negotiations">0</div>
            <div class="metric-label">Active Negotiations</div>
        </div>
        <div class="metric-card">
            <div class="metric-value" id="cooperation-index">0.0</div>
            <div class="metric-label">Cooperation Index</div>
        </div>
    </div>
    
    <div class="charts-container">
        <div class="chart-container">
            <div id="happiness-chart"></div>
        </div>
        <div class="chart-container">
            <div id="wealth-chart"></div>
        </div>
        <div class="chart-container">
            <div id="communication-chart"></div>
        </div>
        <div class="chart-container">
            <div id="agent-positions"></div>
        </div>
    </div>
    
    <div class="log-container" id="log-container">
        <div>Dashboard initialized. Waiting for simulation data...</div>
    </div>

    <script>
        const socket = io();
        let isRunning = false;
        let metricsHistory = [];
        
        socket.on('connect', function() {
            updateStatus(true);
            log('Connected to dashboard server');
        });
        
        socket.on('disconnect', function() {
            updateStatus(false);
            log('Disconnected from dashboard server');
        });
        
        socket.on('metrics_update', function(metrics) {
            updateMetrics(metrics);
            metricsHistory.push(metrics);
            updateCharts();
        });
        
        function updateStatus(connected) {
            const indicator = document.getElementById('status-indicator');
            const text = document.getElementById('status-text');
            
            if (connected) {
                indicator.className = 'status-indicator status-running';
                text.textContent = 'Connected';
            } else {
                indicator.className = 'status-indicator status-stopped';
                text.textContent = 'Disconnected';
            }
        }
        
        function updateMetrics(metrics) {
            document.getElementById('total-agents').textContent = metrics.total_agents;
            document.getElementById('avg-happiness').textContent = metrics.average_happiness.toFixed(2);
            document.getElementById('avg-wealth').textContent = '$' + metrics.average_wealth.toFixed(2);
            document.getElementById('total-messages').textContent = metrics.total_messages;
            document.getElementById('active-negotiations').textContent = metrics.negotiations_active;
            document.getElementById('cooperation-index').textContent = metrics.cooperation_index.toFixed(3);
            
            log(`Step ${metrics.step}: ${metrics.active_agents} active agents, ${metrics.total_messages} messages`);
        }
        
        function updateCharts() {
            if (metricsHistory.length < 2) return;
            
            const steps = metricsHistory.map(m => m.step);
            const happiness = metricsHistory.map(m => m.average_happiness);
            const wealth = metricsHistory.map(m => m.average_wealth);
            const messages = metricsHistory.map(m => m.total_messages);
            const cooperation = metricsHistory.map(m => m.cooperation_index);
            
            // Happiness chart
            Plotly.newPlot('happiness-chart', [{
                x: steps,
                y: happiness,
                type: 'scatter',
                mode: 'lines+markers',
                name: 'Average Happiness',
                line: {color: '#e74c3c'}
            }], {
                title: 'Happiness Over Time',
                xaxis: {title: 'Simulation Step'},
                yaxis: {title: 'Happiness Level'}
            });
            
            // Wealth chart
            Plotly.newPlot('wealth-chart', [{
                x: steps,
                y: wealth,
                type: 'scatter',
                mode: 'lines+markers',
                name: 'Average Wealth',
                line: {color: '#f39c12'}
            }], {
                title: 'Wealth Over Time',
                xaxis: {title: 'Simulation Step'},
                yaxis: {title: 'Wealth ($)'}
            });
            
            // Communication chart
            Plotly.newPlot('communication-chart', [{
                x: steps,
                y: messages,
                type: 'scatter',
                mode: 'lines+markers',
                name: 'Total Messages',
                line: {color: '#3498db'}
            }, {
                x: steps,
                y: cooperation,
                type: 'scatter',
                mode: 'lines+markers',
                name: 'Cooperation Index',
                yaxis: 'y2',
                line: {color: '#27ae60'}
            }], {
                title: 'Communication & Cooperation',
                xaxis: {title: 'Simulation Step'},
                yaxis: {title: 'Message Count'},
                yaxis2: {
                    title: 'Cooperation Index',
                    overlaying: 'y',
                    side: 'right'
                }
            });
        }
        
        function startSimulation() {
            const numAgents = document.getElementById('num-agents').value;
            fetch('/api/start_simulation', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({num_agents: parseInt(numAgents)})
            })
            .then(response => response.json())
            .then(data => {
                log(`Simulation started with ${data.num_agents} agents`);
                isRunning = true;
                updateButtons();
            });
        }
        
        function stopSimulation() {
            fetch('/api/stop_simulation', {method: 'POST'})
            .then(response => response.json())
            .then(data => {
                log('Simulation stopped');
                isRunning = false;
                updateButtons();
            });
        }
        
        function exportData() {
            window.open('/api/export_data', '_blank');
            log('Data export initiated');
        }
        
        function updateButtons() {
            document.getElementById('start-btn').disabled = isRunning;
            document.getElementById('stop-btn').disabled = !isRunning;
        }
        
        function log(message) {
            const container = document.getElementById('log-container');
            const timestamp = new Date().toLocaleTimeString();
            container.innerHTML += `<div>[${timestamp}] ${message}</div>`;
            container.scrollTop = container.scrollHeight;
        }
        
        // Request updates every 2 seconds
        setInterval(() => {
            if (isRunning) {
                socket.emit('request_update');
            }
        }, 2000);
        
        // Initial setup
        updateButtons();
    </script>
</body>
</html>
        '''
    
    def start_simulation_thread(self, num_agents: int = 100):
        """Start simulation in background thread"""
        if self.is_running:
            return
            
        self.is_running = True
        self.simulation = EnhancedSocietySimulation(num_agents=num_agents)
        
        def run_simulation():
            logger.info(f"Starting simulation with {num_agents} agents")
            step = 0
            
            while self.is_running:
                try:
                    # Run simulation step
                    self.simulation.step()
                    step += 1
                    
                    # Collect and broadcast metrics
                    metrics = self.metrics_collector.collect_metrics(self.simulation)
                    self.socketio.emit('metrics_update', asdict(metrics))
                    
                    # Sleep to control simulation speed
                    time.sleep(1)  # 1 second per step
                    
                except Exception as e:
                    logger.error(f"Simulation error at step {step}: {e}")
                    break
                    
            logger.info("Simulation stopped")
            
        self.simulation_thread = threading.Thread(target=run_simulation)
        self.simulation_thread.daemon = True
        self.simulation_thread.start()
        
    def stop_simulation_thread(self):
        """Stop simulation thread"""
        self.is_running = False
        if self.simulation_thread:
            self.simulation_thread.join(timeout=5)
            
    def export_simulation_data(self):
        """Export simulation data as JSON"""
        if not self.simulation:
            return jsonify({'error': 'No simulation data available'})
            
        # Get recent metrics
        recent_metrics = list(self.metrics_collector.metrics_history)[-100:]
        
        # Get agent data
        agents_data = []
        for agent in self.simulation.agents:
            agents_data.append({
                'id': agent.agent_id,
                'position': agent.position,
                'health': agent.health,
                'energy': agent.energy,
                'happiness': agent.happiness,
                'wealth': agent.wealth,
                'personality': asdict(agent.personality)
            })
            
        export_data = {
            'timestamp': datetime.now().isoformat(),
            'simulation_step': self.simulation.current_step,
            'metrics_history': [asdict(m) for m in recent_metrics],
            'agents': agents_data,
            'messages': [asdict(msg) for msg in self.simulation.communication_system.message_broker.get_recent_messages(100)]
        }
        
        return jsonify(export_data)
        
    def run(self, debug=False):
        """Run the dashboard server"""
        logger.info(f"Starting Live Society Dashboard on http://{self.host}:{self.port}")
        self.socketio.run(self.app, host=self.host, port=self.port, debug=debug)

if __name__ == "__main__":
    dashboard = LiveSocietyDashboard()
    dashboard.run(debug=True)