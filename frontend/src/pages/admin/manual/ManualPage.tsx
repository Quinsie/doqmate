import { useState, useRef, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Settings, PencilLine, Trash2, Plus } from 'lucide-react';
import Button from '../../../components/common/Button';
import ChatbotTable from '../../../components/admin/chatbot/ChatbotList/ChatbotTable';
import ManualFileList from '../../../components/admin/manual/ManualFileList';
import Input from '../../../components/common/Input';
import Textarea from '../../../components/common/Textarea';
import ToggleSwitch from '../../../components/common/ToggleSwitch';
import Modal from '../../../components/common/Modal';
import PageHero from '../../../components/common/PageHero';
import type { Chatbot, UpdateChatbotRequest } from '../../../types/admin/chatbot';
import type { Manual, UploadingFile } from '../../../types/admin/manual';
import { ROUTES } from '../../../constants/routes';
import { ChatbotListProvider } from '../../../contexts/ChatbotListContext';
import { useGetChatbotDetail, useUpdateChatbot, useDeleteChatbot } from '../../../hooks/chatbot/useChatbot';
import { useGetManuals, useUploadManual, useDeleteManual } from '../../../hooks/admin/useManual';

function ManualPage() {
  const navigate = useNavigate();
  const { chatbotId } = useParams<{ chatbotId: string }>();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  const { getChatbotDetail, isLoading: isLoadingDetail } = useGetChatbotDetail();
  const { updateChatbot, isLoading: isUpdating } = useUpdateChatbot();
  const { deleteChatbot, isLoading: isDeleting } = useDeleteChatbot();

  const { getManuals, isLoading: isLoadingManuals } = useGetManuals();
  const { uploadManual, isLoading: isUploading } = useUploadManual();
  const { deleteManual, isLoading: isDeletingManual } = useDeleteManual();

  const [chatbot, setChatbot] = useState<Chatbot | null>(null);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [editFormData, setEditFormData] = useState<UpdateChatbotRequest>({
    name: '',
    description: undefined,
    is_public: true,
    tag: undefined,
  });

  const [manuals, setManuals] = useState<Manual[]>([]);
  const [uploadingFiles, setUploadingFiles] = useState<UploadingFile[]>([]);

  const loadManuals = async () => {
    if (!chatbotId) return;
    const data = await getManuals(chatbotId);
    if (data) {
      setManuals(data.manuals);
    }
  };

  useEffect(() => {
    const loadChatbot = async () => {
      if (!chatbotId) {
        alert('챗봇 ID가 없습니다.');
        navigate(ROUTES.ADMIN.CHATBOT_LIST);
        return;
      }

      const data = await getChatbotDetail(chatbotId);
      if (data) {
        setChatbot(data);
      } else {
        alert('챗봇 정보를 불러오지 못했습니다.');
        navigate(ROUTES.ADMIN.CHATBOT_LIST);
      }
    };

    loadChatbot();
    loadManuals();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chatbotId]);

  const processFiles = (files: FileList | File[]) => {
    const pdfFiles = Array.from(files).filter(file => file.type === 'application/pdf');
    const newFiles = pdfFiles.map(file => ({
      file,
      display_name: file.name.replace('.pdf', ''),
    }));

    setUploadingFiles(prev => [...prev, ...newFiles]);

    // input 초기화하여 같은 파일도 다시 선택 가능하게
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      processFiles(e.target.files);
    }
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (e.dataTransfer.files) {
      processFiles(e.dataTransfer.files);
    }
  };

  const handleRemoveFile = (index: number) => {
    setUploadingFiles(prev => prev.filter((_, i) => i !== index));
  };

  const handleDeleteManual = async (manualId: string) => {
    if (!confirm('이 매뉴얼을 삭제하시겠습니까?')) return;

    const success = await deleteManual(manualId);
    if (success) {
      await loadManuals();
    } else {
      alert('매뉴얼 삭제에 실패했습니다.');
    }
  };

  const handleUpdateDisplayName = (index: number, newName: string) => {
    setUploadingFiles(prev =>
      prev.map((item, i) =>
        i === index ? { ...item, display_name: newName } : item
      )
    );
  };


  const handleSubmit = async () => {
    if (!chatbotId || uploadingFiles.length === 0) return;

    let successCount = 0;
    let failCount = 0;

    for (const file of uploadingFiles) {
      const result = await uploadManual(chatbotId, {
        file: file.file,
        display_name: file.display_name,
      });

      if (result) {
        successCount++;
      } else {
        failCount++;
      }
    }

    if (failCount > 0) {
      alert(`${successCount}개 업로드 성공, ${failCount}개 업로드 실패`);
    } else {
      alert(`${successCount}개 매뉴얼이 등록되었습니다.`);
    }

    setUploadingFiles([]);
    await loadManuals();
  };

  const handleCancel = () => {
    navigate(ROUTES.ADMIN.CHATBOT_LIST);
  };

  const handleTogglePublic = async (chatbotId: string, isPublic: boolean) => {
    const updatedChatbot = await updateChatbot(chatbotId, { is_public: !isPublic });

    if (updatedChatbot) {
      setChatbot(updatedChatbot);
    } else {
      alert('공개 상태 변경에 실패했습니다.');
    }
  };

  const handleEditClick = () => {
    if (!chatbot) return;

    setEditFormData({
      name: chatbot.name,
      description: chatbot.description || undefined,
      is_public: chatbot.is_public,
      tag: chatbot.tag || undefined,
    });
    setShowEditModal(true);
  };

  const handleEditInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setEditFormData((prev) => ({ ...prev, [name]: value || undefined }));
  };

  const handleEditToggleChange = (value: boolean) => {
    setEditFormData((prev) => ({ ...prev, is_public: value }));
  };

  const handleEditSubmit = async () => {
    if (!chatbot || !editFormData.name || !editFormData.name.trim()) {
      alert('챗봇 이름을 입력해주세요.');
      return;
    }

    const updatedChatbot = await updateChatbot(chatbot.chatbot_id, editFormData);

    if (updatedChatbot) {
      setChatbot(updatedChatbot);
      setShowEditModal(false);
      alert('챗봇 정보가 수정되었습니다.');
    } else {
      alert('챗봇 수정에 실패했습니다.');
    }
  };

  const handleDeleteClick = () => {
    setShowDeleteModal(true);
  };

  const handleDeleteConfirm = async () => {
    if (!chatbot) return;

    const success = await deleteChatbot(chatbot.chatbot_id);

    if (success) {
      alert('챗봇이 삭제되었습니다.');
      navigate(ROUTES.ADMIN.CHATBOT_LIST);
    } else {
      alert('챗봇 삭제에 실패했습니다.');
      setShowDeleteModal(false);
    }
  };

  const heroSection = (
    <PageHero
      icon={<Settings size={40} className="text-white" />}
      title="챗봇 설정"
      gradient="from-indigo-500 via-indigo-600 to-purple-600"
    />
  );

  if (isLoadingDetail) {
    return (
      <main className="flex-1 p-8 lg:p-12">
        <div className="max-w-5xl mx-auto">
          {heroSection}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-12 text-center">
            <p className="text-gray-500">로딩 중...</p>
          </div>
        </div>
      </main>
    );
  }

  if (!chatbot) {
    return (
      <main className="flex-1 p-8 lg:p-12">
        <div className="max-w-5xl mx-auto">
          {heroSection}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-12 text-center">
            <p className="text-gray-500">챗봇 정보를 불러올 수 없습니다.</p>
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="flex-1 p-8 lg:p-12">
      <div className="max-w-5xl mx-auto">
        {heroSection}

        {/* 선택된 챗봇 정보 */}
        <div className="mb-6">
          {/* 챗봇 수정/삭제 버튼 */}
          <div className="flex justify-end gap-3 mb-4">
            <Button variant="outline" onClick={handleEditClick} icon={<PencilLine size={20} />}>
              수정
            </Button>
            <Button variant="red" onClick={handleDeleteClick} disabled={isDeleting} icon={<Trash2 size={20} />}>
              삭제
            </Button>
          </div>

          <ChatbotListProvider
            onTogglePublic={handleTogglePublic}
            isUpdating={isUpdating}
          >
            <ChatbotTable chatbots={[chatbot]} />
          </ChatbotListProvider>
        </div>

        {/* 파일 미리보기/관리 영역 */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`transition-all ${isDragging ? 'opacity-50' : ''}`}
        >
          <ManualFileList
            manuals={manuals}
            uploadingFiles={uploadingFiles}
            onRemoveFile={handleRemoveFile}
            onUpdateDisplayName={handleUpdateDisplayName}
            onDeleteManual={handleDeleteManual}
            isDeletingManual={isDeletingManual}
            isLoadingManuals={isLoadingManuals}
            isDragging={isDragging}
          />
        </div>

        {/* PDF 추가 버튼 */}
        <div className="mb-6">
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf"
            multiple
            onChange={handleFileSelect}
            className="hidden"
          />
          <Button
            variant="outline"
            onClick={() => fileInputRef.current?.click()}
            icon={<Plus size={20} />}
          >
            pdf 추가
          </Button>
        </div>

        {/* 하단 버튼들 */}
        <div className="flex justify-end gap-3">
          <Button
            variant="primary"
            onClick={handleSubmit}
            disabled={uploadingFiles.length === 0 || isUploading}
          >
            {isUploading ? '등록 중...' : '등록'}
          </Button>
          <Button variant="secondary" onClick={handleCancel}>
            취소
          </Button>
        </div>

        {/* 챗봇 정보 수정 모달 */}
        <Modal
          isOpen={showEditModal}
          title="챗봇 정보 수정"
          maxWidth="2xl"
          confirmText={isUpdating ? '수정 중...' : '수정'}
          cancelText="취소"
          onConfirm={handleEditSubmit}
          onCancel={() => setShowEditModal(false)}
          confirmDisabled={isUpdating}
        >
          <div className="space-y-6">
            <Input
              label="챗봇 이름"
              name="name"
              type="text"
              value={editFormData.name || ''}
              onChange={handleEditInputChange}
              placeholder="챗봇 이름을 입력하세요"
              required
            />

            <Textarea
              label="설명"
              id="description"
              name="description"
              value={editFormData.description || ''}
              onChange={handleEditInputChange}
              placeholder="챗봇에 대한 설명을 입력하세요"
              rows={3}
            />

            <Input
              label="태그"
              name="tag"
              type="text"
              value={editFormData.tag || ''}
              onChange={handleEditInputChange}
              placeholder="예: 고객지원, 사내용"
            />

            <div className="bg-gray-50 rounded-lg p-5 border border-gray-200">
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <label className="text-sm font-medium text-gray-900 block mb-1">
                    공개 여부
                  </label>
                  <p className="text-xs text-gray-500">
                    {editFormData.is_public
                      ? '모든 사용자가 이 챗봇을 사용할 수 있습니다'
                      : '관리자만 이 챗봇을 사용할 수 있습니다'}
                  </p>
                </div>
                <div className="flex items-center gap-3 ml-4">
                  <span
                    className={`text-sm font-medium ${
                      editFormData.is_public ? 'text-blue-600' : 'text-gray-500'
                    }`}
                  >
                    {editFormData.is_public ? '공개' : '비공개'}
                  </span>
                  <ToggleSwitch
                    checked={editFormData.is_public ?? true}
                    onChange={handleEditToggleChange}
                  />
                </div>
              </div>
            </div>
          </div>
        </Modal>

        {/* 챗봇 삭제 확인 모달 */}
        <Modal
          isOpen={showDeleteModal}
          title="챗봇 삭제"
          message={`'${chatbot.name}' 챗봇을 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.`}
          confirmText="삭제"
          cancelText="취소"
          onConfirm={handleDeleteConfirm}
          onCancel={() => setShowDeleteModal(false)}
        />
      </div>
    </main>
  );
}

export default ManualPage;
