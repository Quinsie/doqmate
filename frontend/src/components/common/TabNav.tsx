export interface TabItem<T extends string = string> {
  key: T;
  label: string;
}

interface TabNavProps<T extends string = string> {
  tabs: TabItem<T>[];
  activeTab: T;
  onChange: (tab: T) => void;
}

function TabNav<T extends string = string>({ tabs, activeTab, onChange }: TabNavProps<T>) {
  return (
    <div className="flex border-b border-gray-200">
      {tabs.map((tab) => (
        <button
          key={tab.key}
          onClick={() => onChange(tab.key)}
          className={`px-6 py-3 text-sm font-medium transition-colors cursor-pointer ${
            activeTab === tab.key
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

export default TabNav;
