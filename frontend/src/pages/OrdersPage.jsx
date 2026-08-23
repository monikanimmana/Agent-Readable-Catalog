import React, { useState, useEffect } from 'react';
import './OrdersPage.css';

const API_BASE = 'http://localhost:8001';

export function OrdersPage() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchOrders();
  }, []);

  const fetchOrders = async () => {
    try {
      const response = await fetch(`${API_BASE}/audit-log?action_type=initiate_purchase`);
      if (!response.ok) throw new Error('Failed to fetch orders');
      
      const logs = await response.json();
      
      const orders = logs
        .filter(log => log.status === 'success')
        .map((log, idx) => ({
          id: log.razorpay_order_id || idx,
          productId: log.input_data.product_id,
          quantity: log.input_data.quantity,
          amount: log.output_data.amount,
          status: log.status,
          timestamp: new Date(log.timestamp).toLocaleDateString(),
          orderId: log.razorpay_order_id
        }));
      
      setOrders(orders);
    } catch (error) {
      console.error('Error fetching orders:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="orders-page">
      <div className="orders-header">
        <h2>My Orders</h2>
        <p className="orders-subtitle">View all your successful purchases</p>
      </div>

      {loading ? (
        <div className="loading">Loading orders...</div>
      ) : orders.length === 0 ? (
        <div className="empty-state">
          <p className="empty-icon">📦</p>
          <p className="empty-text">No orders yet</p>
          <p className="empty-subtext">Start chatting with the agent to place an order</p>
        </div>
      ) : (
        <div className="orders-list">
          {orders.map((order, idx) => (
            <div key={idx} className="order-card">
              <div className="order-header">
                <div>
                  <p className="order-id">Order #{order.orderId?.slice(-8) || idx + 1}</p>
                  <p className="order-date">{order.timestamp}</p>
                </div>
                <span className="order-status success">✓ Completed</span>
              </div>
              <div className="order-details">
                <p>Quantity: <strong>{order.quantity} item(s)</strong></p>
                <p>Amount: <strong className="amount">₹{order.amount?.toLocaleString() || 'N/A'}</strong></p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
