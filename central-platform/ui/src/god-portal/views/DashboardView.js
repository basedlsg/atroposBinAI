import React, { useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { fetchMetrics, fetchWorkflows, fetchComponents } from '../../store/dashboardSlice';
import ComponentStatusCard from '../components/ComponentStatusCard';
import ActivityFeed from '../components/ActivityFeed';
import MetricCard from '../components/MetricCard';

const DashboardView = () => {
  const dispatch = useDispatch();
  const { metrics, workflows, components, loading, error } = useSelector((state) => state.dashboard);

  useEffect(() => {
    dispatch(fetchMetrics());
    dispatch(fetchWorkflows());
    dispatch(fetchComponents());
  }, [dispatch]);

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div className="dashboard-view">
      <h2>Platform Overview</h2>
      <div className="metrics-grid">
        <MetricCard title="Active Workflows" value={metrics.activeWorkflows} />
        <MetricCard title="Completed Tasks" value={metrics.completedTasks} />
        <MetricCard title="System Health" value={metrics.systemHealth} />
        <MetricCard title="Alerts" value={metrics.alerts} />
      </div>
      <h2>Component Status</h2>
      <div className="component-status-grid">
        {components.map(comp => (
          <ComponentStatusCard key={comp.id} component={comp} />
        ))}
      </div>
      <ActivityFeed activities={workflows} />
    </div>
  );
};

export default DashboardView;