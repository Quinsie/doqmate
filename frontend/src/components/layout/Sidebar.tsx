import type { ReactNode } from 'react';
import { Menu } from 'lucide-react';

interface SidebarProps {
  isCollapsed: boolean;
  setIsCollapsed: (value: boolean) => void;
  children: ReactNode;
}

function Sidebar({ isCollapsed, setIsCollapsed, children }: SidebarProps) {
  return (
    <aside className={`fixed left-0 top-0 h-screen bg-[#e9eef6] border-r border-gray-200 p-4 flex flex-col transition-all duration-300 overflow-hidden ${isCollapsed ? 'w-20' : 'w-64'}`}>
      <div className="flex mb-6">
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="p-2 hover:bg-gray-300 rounded-full transition-colors"
          aria-label="Toggle Sidebar"
        >
          <Menu size={24} className="text-gray-600" />
        </button>
      </div>

      {children}
    </aside>
  );
}

export default Sidebar;
