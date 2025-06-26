"""
Real-Time Analytics Dashboard for Agent Society Simulations
==========================================================

A comprehensive web-based dashboard for monitoring and analyzing agent society simulations
in real-time, featuring live metrics, interactive visualizations, and simulation controls.

Features:
- Real-time agent status monitoring
- Live metrics and KPIs
- Interactive visualizations (charts, graphs, maps)
- Simulation controls and configuration
- Historical data analysis
- Export capabilities
- Multi-simulation comparison
"""

import asyncio
import json
import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque
import uuid
import webbrowser
import os

# Web framework imports
try:
    from flask import Flask, render_template, jsonify, request, Response
    from flask_socketio import SocketIO, emit
    import plotly.graph_objs as go
    import plotly.utils
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    print("Flask not available. Install with: pip install flask flask-socketio plotly")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AgentMetrics:
    """Metrics for a single agent"""
    agent_id: str
    position: Dict[str, float] = field(default_factory=lambda: {"x": 0, "y": 0})
    health: float = 100.0
    energy: float = 100.0
    happiness: float = 50.0
    wealth: float = 0.0
    social_connections: int = 0
    actions_taken: int = 0
    messages_sent: int = 0
    messages_received: int = 0
    last_activity: float = field(default_factory=time.time)
    status: str = "active"
    personality: Dict[str, float] = field(default_factory=dict)

@dataclass
class SimulationMetrics:
    """Overall simulation metrics"""
    simulation_id: str
    start_time: float = field(default_factory=time.time)
    current_step: int = 0
    total_agents: int = 0
    active_agents: int = 0
    total_messages: int = 0
    total_actions: int = 0
    average_happiness: float = 50.0
    average_wealth: float = 0.0
    average_energy: float = 100.0
    social_network_density: float = 0.0
    cooperation_rate: float = 0.0
    innovation_rate: float = 0.0
    conflict_rate: float = 0.0
    resource_distribution: Dict[str, float] = field(default_factory=dict)
    event_history: List[Dict[str, Any]] = field(default_factory=list)

class MetricsCollector:
    """Collects and processes metrics from agent simulations"""
    
    def __init__(self):
        self.agent_metrics: Dict[str, AgentMetrics] = {}
        self.simulation_metrics: Dict[str, SimulationMetrics] = {}
        self.historical_data: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.event_listeners: List[Callable] = []
        self.collection_interval = 1.0  # seconds
        
    def register_agent(self, agent_id: str, initial_data: Dict[str, Any]):
        """Register a new agent for metrics collection"""
        self.agent_metrics[agent_id] = AgentMetrics(
            agent_id=agent_id,
            position=initial_data.get("position", {"x": 0, "y": 0}),
            health=initial_data.get("health", 100.0),
            energy=initial_data.get("energy", 100.0),
            happiness=initial_data.get("happiness", 50.0),
            wealth=initial_data.get("wealth", 0.0),
            personality=initial_data.get("personality", {})
        )
        logger.info(f"Registered agent {agent_id} for metrics collection")
    
    def update_agent_metrics(self, agent_id: str, updates: Dict[str, Any]):
        """Update metrics for a specific agent"""
        if agent_id not in self.agent_metrics:
            return
        
        agent = self.agent_metrics[agent_id]
        
        # Update metrics
        for key, value in updates.items():
            if hasattr(agent, key):
                setattr(agent, key, value)
        
        agent.last_activity = time.time()
        
        # Store historical data
        self._store_historical_data(agent_id, updates)
        
        # Notify listeners
        self._notify_listeners("agent_update", {"agent_id": agent_id, "updates": updates})
    
    def update_simulation_metrics(self, simulation_id: str, updates: Dict[str, Any]):
        """Update overall simulation metrics"""
        if simulation_id not in self.simulation_metrics:
            self.simulation_metrics[simulation_id] = SimulationMetrics(simulation_id=simulation_id)
        
        sim = self.simulation_metrics[simulation_id]
        
        # Update metrics
        for key, value in updates.items():
            if hasattr(sim, key):
                setattr(sim, key, value)
        
        # Calculate derived metrics
        self._calculate_derived_metrics(simulation_id)
        
        # Store historical data
        self._store_simulation_historical_data(simulation_id, updates)
        
        # Notify listeners
        self._notify_listeners("simulation_update", {"simulation_id": simulation_id, "updates": updates})
    
    def _calculate_derived_metrics(self, simulation_id: str):
        """Calculate derived metrics from agent data"""
        sim = self.simulation_metrics[simulation_id]
        
        if not self.agent_metrics:
            return
        
        # Calculate averages
        total_happiness = sum(agent.happiness for agent in self.agent_metrics.values())
        total_wealth = sum(agent.wealth for agent in self.agent_metrics.values())
        total_energy = sum(agent.energy for agent in self.agent_metrics.values())
        total_connections = sum(agent.social_connections for agent in self.agent_metrics.values())
        
        num_agents = len(self.agent_metrics)
        sim.average_happiness = total_happiness / num_agents
        sim.average_wealth = total_wealth / num_agents
        sim.average_energy = total_energy / num_agents
        sim.social_network_density = total_connections / (num_agents * (num_agents - 1)) if num_agents > 1 else 0
        
        # Calculate rates
        total_actions = sum(agent.actions_taken for agent in self.agent_metrics.values())
        total_messages = sum(agent.messages_sent for agent in self.agent_metrics.values())
        
        sim.total_actions = total_actions
        sim.total_messages = total_messages
        
        # Estimate rates based on recent activity
        recent_actions = sum(1 for agent in self.agent_metrics.values() 
                           if time.time() - agent.last_activity < 60)
        sim.cooperation_rate = recent_actions / num_agents if num_agents > 0 else 0
    
    def _store_historical_data(self, agent_id: str, data: Dict[str, Any]):
        """Store historical data for an agent"""
        timestamp = time.time()
        data_point = {
            "timestamp": timestamp,
            "agent_id": agent_id,
            **data
        }
        self.historical_data[f"agent_{agent_id}"].append(data_point)
    
    def _store_simulation_historical_data(self, simulation_id: str, data: Dict[str, Any]):
        """Store historical data for simulation"""
        timestamp = time.time()
        data_point = {
            "timestamp": timestamp,
            "simulation_id": simulation_id,
            **data
        }
        self.historical_data[f"simulation_{simulation_id}"].append(data_point)
    
    def add_event_listener(self, listener: Callable):
        """Add an event listener for metrics updates"""
        self.event_listeners.append(listener)
    
    def _notify_listeners(self, event_type: str, data: Dict[str, Any]):
        """Notify all event listeners"""
        for listener in self.event_listeners:
            try:
                listener(event_type, data)
            except Exception as e:
                logger.error(f"Error in event listener: {e}")
    
    def get_agent_metrics(self, agent_id: str) -> Optional[AgentMetrics]:
        """Get metrics for a specific agent"""
        return self.agent_metrics.get(agent_id)
    
    def get_simulation_metrics(self, simulation_id: str) -> Optional[SimulationMetrics]:
        """Get metrics for a specific simulation"""
        return self.simulation_metrics.get(simulation_id)
    
    def get_all_agent_metrics(self) -> Dict[str, AgentMetrics]:
        """Get metrics for all agents"""
        return self.agent_metrics.copy()
    
    def get_historical_data(self, data_key: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get historical data for a specific key"""
        data = self.historical_data.get(data_key, deque())
        return list(data)[-limit:]
    
    def export_metrics(self, simulation_id: str, format: str = "json") -> str:
        """Export metrics to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"metrics_export_{simulation_id}_{timestamp}.{format}"
        
        export_data = {
            "simulation_metrics": self.simulation_metrics.get(simulation_id, {}),
            "agent_metrics": {k: v.__dict__ for k, v in self.agent_metrics.items()},
            "historical_data": {k: list(v) for k, v in self.historical_data.items()},
            "export_timestamp": timestamp
        }
        
        if format == "json":
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
        
        logger.info(f"Metrics exported to {filename}")
        return filename

class RealTimeDashboard:
    """Real-time web dashboard for agent society simulations"""
    
    def __init__(self, metrics_collector: MetricsCollector, port: int = 5000):
        if not FLASK_AVAILABLE:
            raise ImportError("Flask is required for the dashboard. Install with: pip install flask flask-socketio plotly")
        
        self.metrics_collector = metrics_collector
        self.port = port
        self.app = Flask(__name__)
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # Register event listener
        self.metrics_collector.add_event_listener(self._handle_metrics_update)
        
        # Setup routes
        self._setup_routes()
        self._setup_socketio_events()
        
        # Dashboard state
        self.dashboard_state = {
            "active_simulations": set(),
            "connected_clients": 0,
            "last_update": time.time()
        }
    
    def _setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/')
        def index():
            """Main dashboard page"""
            return self._render_dashboard()
        
        @self.app.route('/api/metrics/<simulation_id>')
        def get_metrics(simulation_id):
            """Get current metrics for a simulation"""
            sim_metrics = self.metrics_collector.get_simulation_metrics(simulation_id)
            agent_metrics = self.metrics_collector.get_all_agent_metrics()
            
            return jsonify({
                "simulation": sim_metrics.__dict__ if sim_metrics else {},
                "agents": {k: v.__dict__ for k, v in agent_metrics.items()},
                "timestamp": time.time()
            })
        
        @self.app.route('/api/historical/<data_key>')
        def get_historical_data(data_key):
            """Get historical data"""
            limit = request.args.get('limit', 100, type=int)
            data = self.metrics_collector.get_historical_data(data_key, limit)
            return jsonify(data)
        
        @self.app.route('/api/export/<simulation_id>')
        def export_metrics(simulation_id):
            """Export metrics"""
            format_type = request.args.get('format', 'json')
            filename = self.metrics_collector.export_metrics(simulation_id, format_type)
            return jsonify({"filename": filename, "status": "success"})
        
        @self.app.route('/api/simulations')
        def list_simulations():
            """List all active simulations"""
            simulations = list(self.metrics_collector.simulation_metrics.keys())
            return jsonify({"simulations": simulations})
    
    def _setup_socketio_events(self):
        """Setup SocketIO events"""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection"""
            self.dashboard_state["connected_clients"] += 1
            logger.info(f"Client connected. Total clients: {self.dashboard_state['connected_clients']}")
            
            # Send initial data
            emit('dashboard_state', self.dashboard_state)
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection"""
            self.dashboard_state["connected_clients"] -= 1
            logger.info(f"Client disconnected. Total clients: {self.dashboard_state['connected_clients']}")
        
        @self.socketio.on('request_metrics')
        def handle_metrics_request(data):
            """Handle metrics request from client"""
            simulation_id = data.get('simulation_id')
            if simulation_id:
                sim_metrics = self.metrics_collector.get_simulation_metrics(simulation_id)
                agent_metrics = self.metrics_collector.get_all_agent_metrics()
                
                emit('metrics_update', {
                    "simulation": sim_metrics.__dict__ if sim_metrics else {},
                    "agents": {k: v.__dict__ for k, v in agent_metrics.items()},
                    "timestamp": time.time()
                })
    
    def _handle_metrics_update(self, event_type: str, data: Dict[str, Any]):
        """Handle metrics updates from collector"""
        # Broadcast to connected clients
        self.socketio.emit('metrics_update', {
            "event_type": event_type,
            "data": data,
            "timestamp": time.time()
        })
        
        self.dashboard_state["last_update"] = time.time()
    
    def _render_dashboard(self) -> str:
        """Render the main dashboard HTML"""
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agent Society Analytics Dashboard</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }}
        .dashboard {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
        }}
        .header h1 {{
            font-size: 2.5em;
            margin: 0;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .metric-card {{
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            border: 1px solid rgba(255,255,255,0.2);
        }}
        .metric-title {{
            font-size: 1.2em;
            font-weight: bold;
            margin-bottom: 10px;
            color: #ffd700;
        }}
        .metric-value {{
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .metric-change {{
            font-size: 0.9em;
            opacity: 0.8;
        }}
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .chart-container {{
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            border: 1px solid rgba(255,255,255,0.2);
        }}
        .chart-title {{
            font-size: 1.3em;
            font-weight: bold;
            margin-bottom: 15px;
            color: #ffd700;
            text-align: center;
        }}
        .controls {{
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            margin-bottom: 20px;
        }}
        .control-group {{
            display: flex;
            gap: 15px;
            align-items: center;
            margin-bottom: 15px;
        }}
        .control-group label {{
            font-weight: bold;
            min-width: 120px;
        }}
        .control-group select, .control-group input {{
            padding: 8px 12px;
            border: none;
            border-radius: 8px;
            background: rgba(255,255,255,0.2);
            color: white;
            font-size: 14px;
        }}
        .control-group button {{
            padding: 8px 16px;
            border: none;
            border-radius: 8px;
            background: #4CAF50;
            color: white;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.3s;
        }}
        .control-group button:hover {{
            background: #45a049;
        }}
        .status-indicator {{
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
        }}
        .status-connected {{
            background: #4CAF50;
        }}
        .status-disconnected {{
            background: #f44336;
        }}
        .agent-list {{
            max-height: 400px;
            overflow-y: auto;
        }}
        .agent-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 12px;
            margin: 4px 0;
            background: rgba(255,255,255,0.05);
            border-radius: 8px;
            border-left: 4px solid #4CAF50;
        }}
        .agent-item.inactive {{
            border-left-color: #f44336;
            opacity: 0.6;
        }}
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="header">
            <h1>🤖 Agent Society Analytics Dashboard</h1>
            <p>Real-time monitoring and analysis of AI agent societies</p>
        </div>
        
        <div class="controls">
            <div class="control-group">
                <label>Simulation:</label>
                <select id="simulationSelect">
                    <option value="">Select Simulation</option>
                </select>
                <button onclick="refreshSimulations()">Refresh</button>
                <button onclick="exportMetrics()">Export Data</button>
            </div>
            <div class="control-group">
                <label>Update Interval:</label>
                <select id="updateInterval">
                    <option value="1000">1 second</option>
                    <option value="5000" selected>5 seconds</option>
                    <option value="10000">10 seconds</option>
                </select>
                <span id="connectionStatus">
                    <span class="status-indicator status-disconnected"></span>
                    Disconnected
                </span>
            </div>
        </div>
        
        <div class="metrics-grid">
            <div class="metric-card">
                <div class="metric-title">Active Agents</div>
                <div class="metric-value" id="activeAgents">0</div>
                <div class="metric-change" id="activeAgentsChange">+0</div>
            </div>
            <div class="metric-card">
                <div class="metric-title">Average Happiness</div>
                <div class="metric-value" id="avgHappiness">50.0</div>
                <div class="metric-change" id="avgHappinessChange">+0.0</div>
            </div>
            <div class="metric-card">
                <div class="metric-title">Average Wealth</div>
                <div class="metric-value" id="avgWealth">0.0</div>
                <div class="metric-change" id="avgWealthChange">+0.0</div>
            </div>
            <div class="metric-card">
                <div class="metric-title">Total Messages</div>
                <div class="metric-value" id="totalMessages">0</div>
                <div class="metric-change" id="totalMessagesChange">+0</div>
            </div>
            <div class="metric-card">
                <div class="metric-title">Cooperation Rate</div>
                <div class="metric-value" id="cooperationRate">0.0%</div>
                <div class="metric-change" id="cooperationRateChange">+0.0%</div>
            </div>
            <div class="metric-card">
                <div class="metric-title">Social Network Density</div>
                <div class="metric-value" id="networkDensity">0.0</div>
                <div class="metric-change" id="networkDensityChange">+0.0</div>
            </div>
        </div>
        
        <div class="charts-grid">
            <div class="chart-container">
                <div class="chart-title">Agent Happiness Distribution</div>
                <div id="happinessChart"></div>
            </div>
            <div class="chart-container">
                <div class="chart-title">Wealth Distribution</div>
                <div id="wealthChart"></div>
            </div>
            <div class="chart-container">
                <div class="chart-title">Activity Over Time</div>
                <div id="activityChart"></div>
            </div>
            <div class="chart-container">
                <div class="chart-title">Agent Status</div>
                <div class="agent-list" id="agentList">
                    <p>No agents available</p>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        // Initialize Socket.IO connection
        const socket = io();
        let currentSimulation = '';
        let updateInterval = 5000;
        let updateTimer = null;
        
        // Connection status
        socket.on('connect', function() {{
            document.getElementById('connectionStatus').innerHTML = 
                '<span class="status-indicator status-connected"></span>Connected';
        }});
        
        socket.on('disconnect', function() {{
            document.getElementById('connectionStatus').innerHTML = 
                '<span class="status-indicator status-disconnected"></span>Disconnected';
        }});
        
        // Handle metrics updates
        socket.on('metrics_update', function(data) {{
            updateDashboard(data);
        }});
        
        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', function() {{
            refreshSimulations();
            setupEventListeners();
            initializeCharts();
        }});
        
        function setupEventListeners() {{
            document.getElementById('simulationSelect').addEventListener('change', function() {{
                currentSimulation = this.value;
                if (currentSimulation) {{
                    requestMetrics();
                }}
            }});
            
            document.getElementById('updateInterval').addEventListener('change', function() {{
                updateInterval = parseInt(this.value);
                if (updateTimer) {{
                    clearInterval(updateTimer);
                }}
                if (currentSimulation) {{
                    updateTimer = setInterval(requestMetrics, updateInterval);
                }}
            }});
        }}
        
        function refreshSimulations() {{
            fetch('/api/simulations')
                .then(response => response.json())
                .then(data => {{
                    const select = document.getElementById('simulationSelect');
                    select.innerHTML = '<option value="">Select Simulation</option>';
                    
                    data.simulations.forEach(sim => {{
                        const option = document.createElement('option');
                        option.value = sim;
                        option.textContent = sim;
                        select.appendChild(option);
                    }});
                    
                    if (data.simulations.length > 0) {{
                        select.value = data.simulations[0];
                        currentSimulation = data.simulations[0];
                        requestMetrics();
                    }}
                }})
                .catch(error => console.error('Error fetching simulations:', error));
        }}
        
        function requestMetrics() {{
            if (currentSimulation) {{
                socket.emit('request_metrics', {{simulation_id: currentSimulation}});
            }}
        }}
        
        function updateDashboard(data) {{
            const simulation = data.simulation;
            const agents = data.agents;
            
            // Update metrics
            document.getElementById('activeAgents').textContent = simulation.active_agents || 0;
            document.getElementById('avgHappiness').textContent = (simulation.average_happiness || 0).toFixed(1);
            document.getElementById('avgWealth').textContent = (simulation.average_wealth || 0).toFixed(1);
            document.getElementById('totalMessages').textContent = simulation.total_messages || 0;
            document.getElementById('cooperationRate').textContent = ((simulation.cooperation_rate || 0) * 100).toFixed(1) + '%';
            document.getElementById('networkDensity').textContent = (simulation.social_network_density || 0).toFixed(3);
            
            // Update charts
            updateHappinessChart(agents);
            updateWealthChart(agents);
            updateActivityChart(simulation);
            updateAgentList(agents);
        }}
        
        function updateHappinessChart(agents) {{
            const happinessValues = Object.values(agents).map(agent => agent.happiness || 0);
            
            const trace = {{
                x: happinessValues,
                type: 'histogram',
                nbinsx: 20,
                marker: {{
                    color: 'rgba(255, 215, 0, 0.7)',
                    line: {{
                        color: 'rgba(255, 215, 0, 1)',
                        width: 1
                    }}
                }}
            }};
            
            const layout = {{
                title: 'Happiness Distribution',
                xaxis: {{title: 'Happiness Level'}},
                yaxis: {{title: 'Number of Agents'}},
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                font: {{color: 'white'}}
            }};
            
            Plotly.newPlot('happinessChart', [trace], layout);
        }}
        
        function updateWealthChart(agents) {{
            const wealthValues = Object.values(agents).map(agent => agent.wealth || 0);
            
            const trace = {{
                x: wealthValues,
                type: 'histogram',
                nbinsx: 20,
                marker: {{
                    color: 'rgba(76, 175, 80, 0.7)',
                    line: {{
                        color: 'rgba(76, 175, 80, 1)',
                        width: 1
                    }}
                }}
            }};
            
            const layout = {{
                title: 'Wealth Distribution',
                xaxis: {{title: 'Wealth Level'}},
                yaxis: {{title: 'Number of Agents'}},
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                font: {{color: 'white'}}
            }};
            
            Plotly.newPlot('wealthChart', [trace], layout);
        }}
        
        function updateActivityChart(simulation) {{
            // This would typically show activity over time
            // For now, show a simple bar chart of recent activity
            const activities = [
                {{name: 'Messages', value: simulation.total_messages || 0}},
                {{name: 'Actions', value: simulation.total_actions || 0}},
                {{name: 'Cooperation', value: Math.round((simulation.cooperation_rate || 0) * 100)}},
                {{name: 'Innovation', value: Math.round((simulation.innovation_rate || 0) * 100)}}
            ];
            
            const trace = {{
                x: activities.map(a => a.name),
                y: activities.map(a => a.value),
                type: 'bar',
                marker: {{
                    color: 'rgba(156, 39, 176, 0.7)',
                    line: {{
                        color: 'rgba(156, 39, 176, 1)',
                        width: 1
                    }}
                }}
            }};
            
            const layout = {{
                title: 'Activity Overview',
                yaxis: {{title: 'Count'}},
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)',
                font: {{color: 'white'}}
            }};
            
            Plotly.newPlot('activityChart', [trace], layout);
        }}
        
        function updateAgentList(agents) {{
            const agentList = document.getElementById('agentList');
            const agentArray = Object.values(agents);
            
            if (agentArray.length === 0) {{
                agentList.innerHTML = '<p>No agents available</p>';
                return;
            }}
            
            agentList.innerHTML = '';
            
            agentArray.forEach(agent => {{
                const agentItem = document.createElement('div');
                agentItem.className = `agent-item ${{agent.status === 'inactive' ? 'inactive' : ''}}`;
                
                agentItem.innerHTML = `
                    <div>
                        <strong>${{agent.agent_id}}</strong><br>
                        <small>Happiness: ${{(agent.happiness || 0).toFixed(1)}} | Wealth: ${{(agent.wealth || 0).toFixed(1)}}</small>
                    </div>
                    <div>
                        <small>Energy: ${{(agent.energy || 0).toFixed(1)}}% | Connections: ${{agent.social_connections || 0}}</small>
                    </div>
                `;
                
                agentList.appendChild(agentItem);
            }});
        }}
        
        function exportMetrics() {{
            if (!currentSimulation) {{
                alert('Please select a simulation first');
                return;
            }}
            
            fetch(`/api/export/${{currentSimulation}}?format=json`)
                .then(response => response.json())
                .then(data => {{
                    if (data.status === 'success') {{
                        alert(`Metrics exported to ${{data.filename}}`);
                    }} else {{
                        alert('Export failed');
                    }}
                }})
                .catch(error => {{
                    console.error('Export error:', error);
                    alert('Export failed');
                }});
        }}
        
        function initializeCharts() {{
            // Initialize empty charts
            updateHappinessChart({{}});
            updateWealthChart({{}});
            updateActivityChart({{}});
        }}
    </script>
</body>
</html>
        """
    
    def start(self, host: str = "0.0.0.0", port: int = None, auto_open: bool = True):
        """Start the dashboard server"""
        if port is None:
            port = self.port
        
        logger.info(f"Starting dashboard server on {host}:{port}")
        
        # Start in a separate thread
        def run_server():
            self.socketio.run(self.app, host=host, port=port, debug=False)
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Wait a moment for server to start
        time.sleep(2)
        
        # Open browser
        if auto_open:
            url = f"http://localhost:{port}"
            logger.info(f"Opening dashboard at {url}")
            webbrowser.open(url)
        
        return server_thread
    
    def stop(self):
        """Stop the dashboard server"""
        logger.info("Stopping dashboard server")
        # The server will stop when the main thread exits

class MockSimulation:
    """Mock simulation for testing the dashboard"""
    
    def __init__(self, metrics_collector: MetricsCollector, num_agents: int = 50):
        self.metrics_collector = metrics_collector
        self.num_agents = num_agents
        self.simulation_id = f"mock_sim_{int(time.time())}"
        self.running = False
        self.step = 0
        
        # Initialize agents
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize mock agents"""
        import random
        
        for i in range(self.num_agents):
            agent_id = f"agent_{i:04d}"
            
            # Random initial state
            initial_data = {
                "position": {"x": random.uniform(0, 100), "y": random.uniform(0, 100)},
                "health": random.uniform(80, 100),
                "energy": random.uniform(60, 100),
                "happiness": random.uniform(30, 80),
                "wealth": random.uniform(0, 1000),
                "personality": {
                    "social": random.random(),
                    "ambitious": random.random(),
                    "trusting": random.random()
                }
            }
            
            self.metrics_collector.register_agent(agent_id, initial_data)
        
        # Initialize simulation metrics
        self.metrics_collector.update_simulation_metrics(self.simulation_id, {
            "total_agents": self.num_agents,
            "active_agents": self.num_agents,
            "current_step": 0
        })
    
    def start(self):
        """Start the mock simulation"""
        self.running = True
        logger.info(f"Starting mock simulation {self.simulation_id} with {self.num_agents} agents")
        
        # Start simulation loop in a separate thread
        import threading
        simulation_thread = threading.Thread(target=self._simulation_loop, daemon=True)
        simulation_thread.start()
        
        return simulation_thread
    
    def stop(self):
        """Stop the mock simulation"""
        self.running = False
        logger.info(f"Stopping mock simulation {self.simulation_id}")
    
    def _simulation_loop(self):
        """Main simulation loop"""
        import random
        
        while self.running:
            self.step += 1
            
            # Update simulation metrics
            self.metrics_collector.update_simulation_metrics(self.simulation_id, {
                "current_step": self.step,
                "total_messages": self.step * self.num_agents // 10,
                "total_actions": self.step * self.num_agents // 5
            })
            
            # Update random agents
            num_updates = max(1, self.num_agents // 10)
            for _ in range(num_updates):
                agent_id = f"agent_{random.randint(0, self.num_agents-1):04d}"
                
                # Random updates
                updates = {
                    "happiness": max(0, min(100, random.uniform(-5, 5))),
                    "energy": max(0, min(100, random.uniform(-2, 2))),
                    "wealth": random.uniform(-50, 50),
                    "social_connections": random.randint(0, 5),
                    "messages_sent": random.randint(0, 3),
                    "messages_received": random.randint(0, 3),
                    "actions_taken": random.randint(0, 2)
                }
                
                self.metrics_collector.update_agent_metrics(agent_id, updates)
            
            # Sleep between steps
            time.sleep(2)

async def main():
    """Main function to run the real-time analytics dashboard"""
    print("🚀 Real-Time Analytics Dashboard")
    print("=" * 50)
    
    # Create metrics collector
    metrics_collector = MetricsCollector()
    
    # Create dashboard
    dashboard = RealTimeDashboard(metrics_collector, port=5000)
    
    # Create and start mock simulation
    mock_sim = MockSimulation(metrics_collector, num_agents=50)
    mock_sim.start()
    
    # Start dashboard
    dashboard.start(auto_open=True)
    
    print("✅ Dashboard started successfully!")
    print("📊 Open your browser to http://localhost:5000")
    print("🔄 Mock simulation is running with 50 agents")
    print("⏹️  Press Ctrl+C to stop")
    
    try:
        # Keep running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Stopping dashboard...")
        mock_sim.stop()
        dashboard.stop()

if __name__ == "__main__":
    if not FLASK_AVAILABLE:
        print("❌ Flask is required for the dashboard.")
        print("Install with: pip install flask flask-socketio plotly")
    else:
        asyncio.run(main()) 