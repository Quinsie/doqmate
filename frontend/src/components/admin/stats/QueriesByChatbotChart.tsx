import {
  BarChart,
  Bar,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import type { ChatbotQueryCount } from '../../../types/admin/stats';

// 막대 색상 스케일
const BAR_COLOR_SCALE = [
  '#93C5FD', // blue-300 (lowest)
  '#60A5FA', // blue-400
  '#3B82F6', // blue-500
  '#2563EB', // blue-600
  '#1E40AF', // blue-800 (highest)
] as const;

interface QueriesByChatbotChartProps {
  data: ChatbotQueryCount[];
}

function QueriesByChatbotChart({ data }: QueriesByChatbotChartProps) {
  const sortedData = [...data]
    .sort((a, b) => b.queries - a.queries)
    .map((item) => ({
      ...item,
      chatbot_name: item.chatbot_name || item.chatbot_id.slice(0, 8),
    }));

  const maxQueries = Math.max(...sortedData.map((d) => d.queries), 1);
  const minQueries = Math.min(...sortedData.map((d) => d.queries), 0);

  const getBarColor = (value: number): string => {
    const range = maxQueries - minQueries;
    const normalized = range === 0 ? 0.5 : (value - minQueries) / range;
    const index = Math.min(
      Math.floor(normalized * BAR_COLOR_SCALE.length),
      BAR_COLOR_SCALE.length - 1
    );
    return BAR_COLOR_SCALE[index];
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-6">챗봇별 질의 분포</h3>
      <div style={{ width: '100%', minHeight: 280 }}>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={sortedData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" vertical={false} />
            <XAxis
              dataKey="chatbot_name"
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
              formatter={(value: number) => [value.toLocaleString(), '질의 수']}
              cursor={{ fill: 'rgba(59, 130, 246, 0.1)' }}
            />
            <Bar dataKey="queries" radius={[6, 6, 0, 0]} maxBarSize={60}>
              {sortedData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={getBarColor(entry.queries)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}

export default QueriesByChatbotChart;
