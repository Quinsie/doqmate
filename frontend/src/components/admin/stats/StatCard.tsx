interface StatCardProps {
  title: string;
  value: number;
  icon?: string;
  color?: 'blue' | 'green' | 'purple' | 'yellow' | 'orange';
}

const colorStyles = {
  blue: 'from-blue-300 to-blue-600',
  green: 'from-emerald-300 to-emerald-600',
  purple: 'from-purple-200 to-purple-500',
  yellow: 'from-yellow-300 to-yellow-600',
  orange: 'from-orange-300 to-orange-600',
};

function StatCard({ title, value, icon, color = 'blue' }: StatCardProps) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-gray-500 text-sm font-medium mb-1">{title}</p>
          <p className="text-3xl font-bold text-gray-900">{value.toLocaleString()}</p>
        </div>
        {icon && (
          <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${colorStyles[color]} flex items-center justify-center text-2xl shadow-lg`}>
            {icon}
          </div>
        )}
      </div>
    </div>
  );
}

export default StatCard;
