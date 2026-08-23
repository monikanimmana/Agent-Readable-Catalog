import React, { useState, useEffect } from 'react';
import './UserSummary.css';

const API_BASE = 'http://localhost:8000';

export function UserSummary() {
  const [stats, setStats] = useState({
    totalOrders: 0,
    totalSpent: 0
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchUserStats();
  }, []);

  const fetchUserStats = async () => {
    try {
      const response = await fetch(`${API_BASE}/audit-log?action_type=initiate_purchase&limit=100`);
      if (!response.ok) throw new Error('Failed to fetch stats');
      
      const logs = await response.json();
      
      // Calculate totals
      const successfulOrders = logs.filter(l => l.status === 'success').length;
      const totalSpent = logs
        .filter(l => l.status === 'success')
        .reduce((sum, log) => sum + (log.output_data?.amount || 0), 0);
      
      setStats({
        totalOrders: successfulOrders,
        totalSpent: totalSpent
      });
    } catch (error) {
      console.error('Error fetching stats:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="user-summary">Loading...</div>;
  }

  return (
    <div className="user-summary">
      <div className="summary-card">
        <p className="summary-label">Total Orders</p>
        <p className="summary-value">{stats.totalOrders}</p>
      </div>
      
      <div className="summary-card">
        <p className="summary-label">Total Spent</p>
        <p className="summary-value">₹{stats.totalSpent.toLocaleString()}</p>
      </div>
    </div>
  );
}
