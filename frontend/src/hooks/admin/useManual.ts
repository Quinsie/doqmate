import { useState } from 'react';
import { apiClient } from '../../api/client';
import type {
  Manual,
  ManualListResponseData,
  UploadManualFormData,
} from '../../types/admin/manual';
import type { ApiResponse } from '../../types/api';

/**
 * 챗봇에 매뉴얼(PDF) 업로드하는 훅
 * 엔드포인트: POST /api/set/manuals?chatbot_id={chatbot_id}
 */
export function useUploadManual() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const uploadManual = async (
    chatbotId: string,
    uploadData: UploadManualFormData
  ): Promise<Manual | null> => {
    setIsLoading(true);
    setError(null);

    try {
      // multipart/form-data 업로드를 위한 FormData 생성
      const formData = new FormData();
      formData.append('file', uploadData.file);
      formData.append('display_name', uploadData.display_name);

      const response = await apiClient.post<ApiResponse<Manual>>(
        `/set/manuals?chatbot_id=${encodeURIComponent(chatbotId)}`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      if (response.data.success && response.data.data) {
        return response.data.data;
      }

      const errorMessage =
        response.data.error?.message || '매뉴얼 업로드에 실패했습니다';
      setError(errorMessage);
      return null;
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : '매뉴얼 업로드에 실패했습니다';
      setError(errorMessage);
      console.error('Manual upload failed:', err);
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    uploadManual,
    isLoading,
    error,
  };
}

/**
 * 챗봇의 매뉴얼 목록 조회하는 훅
 * 엔드포인트: GET /api/set/manuals?chatbot_id={chatbot_id}
 */
export function useGetManuals() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const getManuals = async (
    chatbotId: string
  ): Promise<ManualListResponseData | null> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiClient.get<
        ApiResponse<ManualListResponseData>
      >(`/set/manuals?chatbot_id=${encodeURIComponent(chatbotId)}`);

      if (response.data.success && response.data.data) {
        return response.data.data;
      }

      const errorMessage =
        response.data.error?.message || '매뉴얼 목록 조회에 실패했습니다';
      setError(errorMessage);
      return null;
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : '매뉴얼 목록 조회에 실패했습니다';
      setError(errorMessage);
      console.error('Manual list fetch failed:', err);
      return null;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    getManuals,
    isLoading,
    error,
  };
}

/**
 * 매뉴얼 삭제하는 훅
 * 엔드포인트: DELETE /api/set/manuals/{manual_id}
 */
export function useDeleteManual() {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const deleteManual = async (manualId: string): Promise<boolean> => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await apiClient.delete<ApiResponse<void>>(
        `/set/manuals/${encodeURIComponent(manualId)}`
      );

      if (response.data.success) {
        return true;
      }

      const errorMessage =
        response.data.error?.message || '매뉴얼 삭제에 실패했습니다';
      setError(errorMessage);
      return false;
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : '매뉴얼 삭제에 실패했습니다';
      setError(errorMessage);
      console.error('Manual deletion failed:', err);
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  return {
    deleteManual,
    isLoading,
    error,
  };
}
