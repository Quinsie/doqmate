import { useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from '../components/layout/Sidebar';
import ChatSidebarContent from '../components/layout/ChatSidebarContent';
import Header from '../components/layout/Header';
import { ChatProvider } from '../contexts/ChatContext';

function PublicLayout() {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const location = useLocation();

  const isAuthPage = location.pathname.startsWith('/auth');

  if (isAuthPage) {
    return (
      <div className="min-h-screen bg-gray-50">
        <main>
          <Outlet />
        </main>
      </div>
    );
  }

  return (
    <ChatProvider>
      <div className="min-h-screen bg-white">
        <Sidebar isCollapsed={isCollapsed} setIsCollapsed={setIsCollapsed}>
          <ChatSidebarContent isCollapsed={isCollapsed} />
        </Sidebar>
        <div className={`flex flex-col transition-all duration-300 ${isCollapsed ? 'ml-20' : 'ml-64'}`}>
          <Header />
          <Outlet />
        </div>
      </div>
    </ChatProvider>
  );
}

export default PublicLayout;
