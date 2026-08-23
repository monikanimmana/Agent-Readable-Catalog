import React, { useState } from 'react';
import { TopBar } from './TopBar';
import { IconRail } from './IconRail';
import { ChatWindow } from './ChatWindow';
import { ActivityFeed } from './ActivityFeed';
import { UserSummary } from './UserSummary';
import { OrdersPage } from '../pages/OrdersPage';
import './Layout.css';

export function Layout() {
  const [activeTab, setActiveTab] = useState('chat');

  return (
    <div className="layout">
      <TopBar />
      <div className="layout-content">
        <IconRail activeTab={activeTab} onTabChange={setActiveTab} />
        
        <main className="main-content">
          {activeTab === 'chat' && <ChatWindow />}
          {activeTab === 'orders' && <OrdersPage />}
        </main>

        <aside className="right-panel">
          <div className="panel-section">
            <UserSummary />
          </div>
          <div className="panel-section">
            <ActivityFeed />
          </div>
        </aside>
      </div>
    </div>
  );
}
