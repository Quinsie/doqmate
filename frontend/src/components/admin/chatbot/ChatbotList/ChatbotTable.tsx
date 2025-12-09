import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import type { Chatbot } from '../../../../types/admin/chatbot';
import { Table } from '../../../common/Table';
import type { TableColumn } from '../../../common/Table';
import ToggleSwitch from '../../../common/ToggleSwitch';
import Modal from '../../../common/Modal';
import Tooltip from '../../../common/Tooltip';
import { useChatbotListContext } from '../../../../contexts/ChatbotListContext';

interface ChatbotTableProps {
  chatbots: Chatbot[];
}

function ChatbotTable({ chatbots }: ChatbotTableProps) {
  const { onTogglePublic, isUpdating } = useChatbotListContext();
  const navigate = useNavigate();
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [selectedChatbot, setSelectedChatbot] = useState<Chatbot | null>(null);
  const [pendingPublicState, setPendingPublicState] = useState(false);

  const handleToggleClick = (chatbot: Chatbot, newState: boolean) => {
    setSelectedChatbot(chatbot);
    setPendingPublicState(newState);
    setShowConfirmModal(true);
  };

  const handleConfirm = () => {
    if (selectedChatbot) {
      onTogglePublic(selectedChatbot.chatbot_id, selectedChatbot.is_public);
    }
    setShowConfirmModal(false);
    setSelectedChatbot(null);
  };

  const handleCancel = () => {
    setShowConfirmModal(false);
    setSelectedChatbot(null);
  };

  const handleRowClick = (chatbot: Chatbot) => {
    navigate(`/admin/chatbot/${chatbot.chatbot_id}/manual`);
  };

  const columns: TableColumn<Chatbot>[] = [
    {
      key: 'index',
      label: 'ID',
      width: 'w-16',
      align: 'center',
      render: (_, __, index) => (
        <span className="text-gray-600 font-medium">{index + 1}</span>
      ),
    },
    {
      key: 'name',
      label: '챗봇 명칭',
      width: 'w-56',
      align: 'center',
      render: (value, row) => (
        <Tooltip content={row.name} position="bottom" onlyWhenTruncated>
          <span className="text-gray-800 font-semibold max-w-[200px] truncate block mx-auto">
            {value as string}
          </span>
        </Tooltip>
      ),
    },
    {
      key: 'tag',
      label: '태그',
      width: 'w-24',
      align: 'center',
      render: (value, row) => (
        <Tooltip content={row.tag || ''} position="bottom" onlyWhenTruncated>
          <span className="text-gray-600 max-w-[80px] truncate block mx-auto">
            {(value as string) || <span className="text-gray-400">-</span>}
          </span>
        </Tooltip>
      ),
    },
    {
      key: 'description',
      label: '설명',
      align: 'center',
      render: (value, row) => (
        <Tooltip content={row.description || ''} position="bottom" onlyWhenTruncated>
          <span className="text-gray-600 max-w-[200px] truncate block mx-auto">
            {(value as string) || <span className="text-gray-400">-</span>}
          </span>
        </Tooltip>
      ),
    },
    {
      key: 'is_public',
      label: '상태',
      width: 'w-40',
      align: 'center',
      render: (_, row) => (
        <div
          className="flex items-center justify-center gap-2"
          onClick={(e) => e.stopPropagation()}
        >
          <ToggleSwitch
            checked={row.is_public}
            onChange={(newState) => handleToggleClick(row, newState)}
            disabled={isUpdating}
          />
          <span
            className={`w-14 text-left truncate ${row.is_public ? 'text-green-600' : 'text-gray-500'} ${isUpdating ? 'opacity-50' : ''}`}
            title={isUpdating ? '처리중...' : row.is_public ? '공개' : '비공개'}
          >
            {isUpdating ? '처리중...' : row.is_public ? '공개' : '비공개'}
          </span>
        </div>
      ),
    },
  ];

  return (
    <>
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <Table
          data={chatbots}
          columns={columns}
          keyExtractor={(row) => row.chatbot_id}
          onRowClick={handleRowClick}
          emptyMessage="등록된 챗봇이 없습니다."
          fixedLayout
        />
      </div>

      <Modal
        isOpen={showConfirmModal}
        title="공개 상태 변경"
        message={`해당 챗봇을 ${pendingPublicState ? '공개' : '비공개'}로 전환합니다.`}
        confirmText="확인"
        cancelText="취소"
        onConfirm={handleConfirm}
        onCancel={handleCancel}
      />
    </>
  );
}

export default ChatbotTable;
