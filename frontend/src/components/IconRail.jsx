import React from 'react';
import './IconRail.css';

export function IconRail({ activeTab, onTabChange }) {
  const tabs = [
    { id: 'chat', icon: '💬', label: 'Chat' },
    { id: 'orders', icon: '📦', label: 'Orders' }
  ];

  return (
    <div className="icon-rail">
      {tabs.map(tab => (
        <button
          key={tab.id}
          className={`rail-icon ${activeTab === tab.id ? 'active' : ''}`}
          onClick={() => onTabChange(tab.id)}
          title={tab.label}
        >
          <span>{tab.icon}</span>
        </button>
      ))}
    </div>
  );
}
