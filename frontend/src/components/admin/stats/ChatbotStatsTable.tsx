import { Table } from '../../common/Table';
import type { TableColumn } from '../../common/Table';
import type { ChatbotQueryCount } from '../../../types/admin/stats';

interface ChatbotStatsTableProps {
  data: ChatbotQueryCount[];
  totalQueries: number;
  onSelectChatbot: (chatbotId: string) => void;
  selectedChatbotId: string | null;
}

function ChatbotStatsTable({
  data,
  totalQueries,
  onSelectChatbot,
  selectedChatbotId,
}: ChatbotStatsTableProps) {
  const sortedData = [...data].sort((a, b) => b.queries - a.queries);

  const calculatePercent = (queries: number) => {
    if (totalQueries === 0) return '0.0';
    return ((queries / totalQueries) * 100).toFixed(1);
  };

  const columns: TableColumn<ChatbotQueryCount>[] = [
    {
      key: 'chatbot_name',
      label: '챗봇명',
      align: 'left',
      render: (_, row) => (
        <div className="flex items-center gap-3">
          <span className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-white text-xs font-medium">
            {row.chatbot_id.slice(0, 2).toUpperCase()}
          </span>
          <span className="font-medium text-gray-900">
            {row.chatbot_name || row.chatbot_id.slice(0, 8)}
          </span>
        </div>
      ),
    },
    {
      key: 'queries',
      label: '질의 수',
      align: 'center',
      render: (value) => (
        <span className="font-semibold text-gray-900">
          {(value as number).toLocaleString()}
        </span>
      ),
    },
    {
      key: 'percent',
      label: '비율',
      align: 'center',
      render: (_, row) => (
        <span className="inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-700">
          {calculatePercent(row.queries)}%
        </span>
      ),
    },
  ];

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-6">챗봇별 상세</h3>
      <Table
        data={sortedData}
        columns={columns}
        keyExtractor={(row) => row.chatbot_id}
        selectedKey={selectedChatbotId}
        onRowClick={(row) => onSelectChatbot(row.chatbot_id)}
      />
    </div>
  );
}

export default ChatbotStatsTable;
