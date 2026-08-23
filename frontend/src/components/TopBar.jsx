import React from 'react';
import './TopBar.css';

export function TopBar() {
  const demoUser = {
    name: 'Alex Chen',
    avatar: '👤'
  };

  return (
    <div className="top-bar">
      <div className="top-bar-left">
        <h2 className="app-name">🛍️ Agent Catalog</h2>
      </div>
      
      <div className="top-bar-right">
        <div className="user-badge">
          <span className="avatar">{demoUser.avatar}</span>
          <span className="user-name">{demoUser.name}</span>
        </div>
      </div>
    </div>
  );
}
