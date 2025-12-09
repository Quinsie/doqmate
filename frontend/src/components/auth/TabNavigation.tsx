interface Tab {
  label: string;
  isActive: boolean;
  onClick: () => void;
}

interface TabNavigationProps {
  tabs: Tab[];
}

function TabNavigation({ tabs }: TabNavigationProps) {
  return (
    <div className="flex border-b border-gray-200 mb-6">
      {tabs.map((tab, index) => (
        <button
          key={index}
          type="button"
          onClick={tab.onClick}
          className={`flex-1 py-3 text-sm font-medium transition-colors ${
            tab.isActive
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}

export default TabNavigation;
