import React, { useState, useEffect } from 'react';
import './ActivityFeed.css';

const API_BASE = 'http://localhost:5000';

export function ActivityFeed() {
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAuditLog();
  }, []);

  const fetchAuditLog = async () => {
    try {
      const response = await fetch(`${API_BASE}/audit-log?limit=10`);
      if (!response.ok) throw new Error('Failed to fetch audit log');
      
      const logs = await response.json();
      
      // Convert logs to activity descriptions
      const activities = logs.map(log => ({
        id: log.id,
        action: log.action_type,
        description: formatAction(log.action_type, log.input_data),
        timestamp: new Date(log.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        status: log.status,
        icon: getIcon(log.action_type)
      }));
      
      setActivities(activities);
    } catch (error) {
      console.error('Error fetching audit log:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatAction = (actionType, inputData) => {
    switch (actionType) {
      case 'search':
        return `Searched for "${inputData.query || 'products'}"`;
      case 'check_stock':
        return `Checked stock for product`;
      case 'get_price':
        return `Got price information`;
      case 'initiate_purchase':
        return `Purchase attempt (${inputData.quantity || 1} item)`;
      default:
        return `Action: ${actionType}`;
    }
  };

  const getIcon = (actionType) => {
    switch (actionType) {
      case 'search':
        return '🔍';
      case 'check_stock':
        return '📦';
      case 'get_price':
        return '💰';
      case 'initiate_purchase':
        return '🛒';
      default:
        return '•';
    }
  };

  return (
    <div className="activity-feed">
      <h3>Activity Feed</h3>
      
      {loading ? (
        <div className="loading">Loading activity...</div>
      ) : activities.length === 0 ? (
        <div className="empty">No activity yet</div>
      ) : (
        <div className="activities-list">
          {activities.map(activity => (
            <div key={activity.id} className="activity-item">
              <span className="activity-icon">{activity.icon}</span>
              <div className="activity-details">
                <p className="activity-description">{activity.description}</p>
                <span className="activity-time">{activity.timestamp}</span>
              </div>
              <span className={`activity-status ${activity.status}`}>
                {activity.status === 'success' ? '✓' : activity.status === 'blocked' ? '⊗' : '✕'}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
