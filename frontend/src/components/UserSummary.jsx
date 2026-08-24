import React, { useState, useEffect } from 'react';
import './UserSummary.css';

const API_BASE = 'http://localhost:5000';

export function UserSummary() {
  const [stats, setStats] = useState({
    totalOrders: 0,
    totalSpent: 0,
    currentOrder: null
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchUserStats();
    // Refresh stats every 5 seconds
    const interval = setInterval(fetchUserStats, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchUserStats = async () => {
    try {
      const response = await fetch(`${API_BASE}/audit-log?limit=100`);
      if (!response.ok) throw new Error('Failed to fetch stats');
      
      const logs = await response.json();
      
      // Calculate totals
      const purchaseOrders = logs.filter(l => l.action_type === 'purchase_attempt' || l.action_type === 'payment_verified');
      const successfulOrders = purchaseOrders.filter(l => l.status === 'success').length;
      const totalSpent = purchaseOrders
        .filter(l => l.status === 'success')
        .reduce((sum, log) => {
          const price = log.input_data?.amount || log.output_data?.amount || 0;
          return sum + price;
        }, 0);
      
      // Get latest order
      const latestOrder = purchaseOrders.length > 0 ? purchaseOrders[0] : null;
      
      setStats({
        totalOrders: successfulOrders,
        totalSpent: totalSpent,
        currentOrder: latestOrder || {
          product: 'Casual Summer Dress',
          price: 699,
          color: 'Pink',
          size: 'M',
          status: 'Ready to Order'
        }
      });
    } catch (error) {
      console.error('Error fetching stats:', error);
      // Set default data on error
      setStats({
        totalOrders: 0,
        totalSpent: 0,
        currentOrder: {
          product: 'Casual Summer Dress',
          price: 699,
          color: 'Pink',
          size: 'M',
          status: 'Ready to Order'
        }
      });
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="user-summary">Loading...</div>;
  }

  return (
    <div className="user-summary">
      {/* Stats Cards */}
      <div className="stats-section">
        <div className="summary-card">
          <p className="summary-label">📦 Total Orders</p>
          <p className="summary-value">{stats.totalOrders}</p>
        </div>
        
        <div className="summary-card">
          <p className="summary-label">💰 Total Spent</p>
          <p className="summary-value">₹{stats.totalSpent.toLocaleString()}</p>
        </div>
      </div>

      {/* Current Order Details */}
      <div className="order-section">
        <h3 className="order-title">📋 Current Order</h3>
        
        {stats.currentOrder && (
          <div className="order-details">
            <div className="detail-row">
              <span className="detail-label">Product:</span>
              <span className="detail-value">{stats.currentOrder.product}</span>
            </div>
            
            <div className="detail-row">
              <span className="detail-label">Price:</span>
              <span className="detail-value">₹{stats.currentOrder.price}</span>
            </div>
            
            <div className="detail-row">
              <span className="detail-label">Color:</span>
              <span className="detail-value">{stats.currentOrder.color || '—'}</span>
            </div>
            
            <div className="detail-row">
              <span className="detail-label">Size:</span>
              <span className="detail-value">{stats.currentOrder.size || '—'}</span>
            </div>
            
            <div className="detail-row">
              <span className="detail-label">Status:</span>
              <span className="detail-value status">{stats.currentOrder.status || 'Processing'}</span>
            </div>
          </div>
        )}
      </div>

      {/* Quick Info */}
      <div className="quick-info">
        <p className="info-text">✅ Select a product to start ordering</p>
      </div>
    </div>
  );
}
