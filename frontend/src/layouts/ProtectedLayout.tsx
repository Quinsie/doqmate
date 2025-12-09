import { useState } from 'react';
import { Outlet, Navigate, useLocation } from 'react-router-dom';
import Sidebar from '../components/layout/Sidebar';
import AdminSidebarContent from '../components/layout/AdminSidebarContent';
import Header from '../components/layout/Header';
import { isAuthenticated } from '../utils/permissions';

function ProtectedLayout() {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const location = useLocation();
  const authenticated = isAuthenticated();

  if (!authenticated) {
    return <Navigate to="/auth/login" state={{ from: location }} replace />;
  }

  return (
    <div className="h-screen bg-white overflow-hidden">
      <Sidebar isCollapsed={isCollapsed} setIsCollapsed={setIsCollapsed}>
        <AdminSidebarContent isCollapsed={isCollapsed} />
      </Sidebar>
      <div className={`flex flex-col h-screen transition-all duration-300 ${isCollapsed ? 'ml-20' : 'ml-64'}`}>
        <Header />
        <div className="flex-1 overflow-y-auto">
          <Outlet />
        </div>
      </div>
    </div>
  );
}

export default ProtectedLayout;
