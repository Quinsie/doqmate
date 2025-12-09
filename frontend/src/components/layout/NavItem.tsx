import { ChevronRight, ChevronDown } from 'lucide-react';

interface NavItemProps {
  icon: string;
  label: string;
  hasDropdown?: boolean;
  isActive?: boolean;
  isCollapsed?: boolean;
  isOpen?: boolean;
  onClick?: () => void;
}

function NavItem({ icon, label, hasDropdown = false, isActive = false, isCollapsed = false, isOpen = false, onClick }: NavItemProps) {
  return (
    <button
      onClick={onClick}
      className={`w-full flex items-center py-3 text-left transition-all duration-200 rounded-lg ${
        isCollapsed ? 'justify-center' : 'gap-3 px-4'
      } ${
        isActive
          ? 'bg-gradient-to-r from-blue-50 to-blue-100 text-blue-600 font-semibold'
          : 'text-gray-700 hover:bg-blue-50'
      }`}
      title={isCollapsed ? label : undefined}
    >
      <span className="text-xl">{icon}</span>
      {!isCollapsed && (
        <div className="flex items-center flex-1">
          <span className="flex-1 font-medium whitespace-nowrap">{label}</span>
          {hasDropdown && (
            isOpen ? <ChevronDown size={18} className="text-blue-500" /> : <ChevronRight size={18} className="text-gray-400" />
          )}
        </div>
      )}
    </button>
  );
}

export default NavItem;
