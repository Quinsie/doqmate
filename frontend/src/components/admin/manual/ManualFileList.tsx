import { useState } from 'react';
import { Pencil, Upload } from 'lucide-react';
import type { Manual, UploadingFile } from '../../../types/admin/manual';

interface ManualFileListProps {
  manuals?: Manual[];
  uploadingFiles?: UploadingFile[];
  onRemoveFile?: (index: number) => void;
  onUpdateDisplayName?: (index: number, newName: string) => void;
  onDeleteManual?: (manualId: string) => void;
  isDeletingManual?: boolean;
  isLoadingManuals?: boolean;
  isDragging?: boolean;
}

function ManualFileList({
  manuals = [],
  uploadingFiles = [],
  onRemoveFile,
  onUpdateDisplayName,
  onDeleteManual,
  isDeletingManual = false,
  isLoadingManuals = false,
  isDragging = false
}: ManualFileListProps) {
  const hasFiles = manuals.length > 0 || uploadingFiles.length > 0;
  const [editingIndex, setEditingIndex] = useState<number | null>(null);

  const getStatusBadge = (status: string) => {
    const statusConfig = {
      pending: { text: '대기 중', color: 'bg-gray-100 text-gray-600' },
      indexing: { text: '인덱싱 중', color: 'bg-blue-100 text-blue-600' },
      ready: { text: '준비 완료', color: 'bg-green-100 text-green-600' },
      failed: { text: '실패', color: 'bg-red-100 text-red-600' }
    };

    const config = statusConfig[status as keyof typeof statusConfig] || statusConfig.pending;

    return (
      <span className={`px-2 py-1 rounded text-xs font-medium ${config.color}`}>
        {config.text}
      </span>
    );
  };

  return (
    <div className={`bg-white rounded-xl shadow-sm border-2 ${isDragging ? 'border-blue-400 border-dashed bg-blue-50' : 'border-gray-100'} p-8 mb-6 min-h-[300px] transition-all`}>
      {isLoadingManuals ? (
        <div className="flex flex-col items-center justify-center h-[250px] text-gray-500">
          <p className="text-lg font-medium">매뉴얼 목록을 불러오는 중...</p>
        </div>
      ) : !hasFiles ? (
        <div className="flex flex-col items-center justify-center h-[250px] text-gray-500">
          <Upload className="w-16 h-16 mb-4" strokeWidth={1.5} />
          <p className="text-lg font-medium">PDF 파일을 드래그하거나 클릭하여 업로드하세요</p>
          <p className="text-sm mt-2">또는 아래 "pdf 추가" 버튼을 사용하세요</p>
        </div>
      ) : (
        <div className="space-y-3">
          <h3 className="font-semibold text-gray-700 mb-3">매뉴얼 목록</h3>

          {/* 서버에서 가져온 매뉴얼 */}
          {manuals.map((manual) => (
            <div
              key={manual.manual_id}
              className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
            >
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-gray-700 font-medium">{manual.display_name}</span>
                  {getStatusBadge(manual.status)}
                </div>
                <div className="text-sm text-gray-500 mt-1">
                  파일명: {manual.original_filename}
                </div>
              </div>
              {onDeleteManual && (
                <button
                  onClick={() => onDeleteManual(manual.manual_id)}
                  disabled={isDeletingManual}
                  className="ml-3 px-3 py-1 text-sm text-red-600 hover:bg-red-100 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isDeletingManual ? '삭제 중...' : '삭제'}
                </button>
              )}
            </div>
          ))}

          {/* 업로드 대기 중인 파일 */}
          {uploadingFiles.map((item, index) => (
            <div
              key={index}
              className="flex items-center justify-between p-3 bg-blue-50 rounded-lg border border-blue-200"
            >
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  {editingIndex === index ? (
                    <input
                      type="text"
                      value={item.display_name}
                      onChange={(e) => onUpdateDisplayName?.(index, e.target.value)}
                      onBlur={() => setEditingIndex(null)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') setEditingIndex(null);
                      }}
                      autoFocus
                      className="flex-1 px-2 py-1 bg-white border border-blue-400 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                      placeholder="표시할 이름"
                    />
                  ) : (
                    <>
                      <span className="text-gray-800 font-medium">{item.display_name}</span>
                      <button
                        onClick={() => setEditingIndex(index)}
                        className="p-1 hover:bg-blue-100 rounded transition-colors"
                        title="이름 수정"
                      >
                        <Pencil className="w-4 h-4 text-gray-600" />
                      </button>
                    </>
                  )}
                </div>
                <div className="text-sm text-gray-600">
                  파일명: {item.file.name} ({(item.file.size / 1024 / 1024).toFixed(2)} MB)
                </div>
              </div>
              <button
                onClick={() => onRemoveFile?.(index)}
                className="ml-3 px-3 py-1 text-sm text-red-600 hover:bg-red-100 rounded transition-colors"
              >
                삭제
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default ManualFileList;
