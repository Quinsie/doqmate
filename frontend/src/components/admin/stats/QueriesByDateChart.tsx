import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import type { DateQueryCount } from '../../../types/admin/stats';

interface QueriesByDateChartProps {
  data: DateQueryCount[];
}

function QueriesByDateChart({ data }: QueriesByDateChartProps) {
  const sortedData = [...data].sort(
    (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()
  );

  const formattedData = sortedData.map((item) => ({
    ...item,
    displayDate: item.date.slice(5), // "2025-11-15" -> "11-15"
  }));

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-6">날짜별 질의 추이</h3>
      <div style={{ width: '100%', minHeight: 280 }}>
        <ResponsiveContainer width="100%" height={280}>
          <LineChart data={formattedData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <defs>
              <linearGradient id="colorQueries" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.1}/>
                <stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
            <XAxis
              dataKey="displayDate"
              tick={{ fontSize: 12, fill: '#6B7280' }}
              axisLine={{ stroke: '#E5E7EB' }}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 12, fill: '#6B7280' }}
              axisLine={{ stroke: '#E5E7EB' }}
              tickLine={false}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#fff',
                border: '1px solid #E5E7EB',
                borderRadius: '8px',
                boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
              }}
              labelFormatter={(label) => `날짜: ${label}`}
              formatter={(value: number) => [value.toLocaleString(), '질의 수']}
            />
            <Line
              type="monotone"
              dataKey="queries"
              stroke="#3B82F6"
              strokeWidth={2.5}
              dot={{ fill: '#fff', stroke: '#3B82F6', strokeWidth: 2, r: 4 }}
              activeDot={{ fill: '#3B82F6', stroke: '#fff', strokeWidth: 2, r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default QueriesByDateChart;
