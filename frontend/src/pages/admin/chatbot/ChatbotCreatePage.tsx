import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Bot, Sparkles, Settings } from 'lucide-react';
import Input from '../../../components/common/Input';
import Textarea from '../../../components/common/Textarea';
import ToggleSwitch from '../../../components/common/ToggleSwitch';
import Button from '../../../components/common/Button';
import PageHero from '../../../components/common/PageHero';
import SectionTitle from '../../../components/common/SectionTitle';
import { ROUTES } from '../../../constants/routes';
import { useCreateChatbot } from '../../../hooks/chatbot/useChatbot';
import type { CreateChatbotRequest } from '../../../types/admin/chatbot';

function ChatbotCreatePage() {
  const navigate = useNavigate();
  const { createChatbot, isLoading } = useCreateChatbot();

  const [formData, setFormData] = useState<CreateChatbotRequest>({
    name: '',
    description: '',
    is_public: true,
    tag: '',
  });

  const [errors, setErrors] = useState<{ [key: string]: string }>({});

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));

    if (errors[name]) {
      setErrors((prev) => ({ ...prev, [name]: '' }));
    }
  };

  const handleToggleChange = (value: boolean) => {
    setFormData((prev) => ({ ...prev, is_public: value }));
  };

  const validateForm = (): boolean => {
    const newErrors: { [key: string]: string } = {};

    if (!formData.name.trim()) {
      newErrors.name = '챗봇 이름을 입력해주세요.';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    const result = await createChatbot(formData);

    if (result) {
      alert('챗봇이 생성되었습니다.');
      navigate(ROUTES.ADMIN.CHATBOT_LIST);
    } else {
      alert('챗봇 생성 중 오류가 발생했습니다. 다시 시도해주세요.');
    }
  };

  const handleCancel = () => {
    navigate(ROUTES.ADMIN.CHATBOT_LIST);
  };

  return (
    <main className="flex-1 p-8 lg:p-12">
      <div className="max-w-3xl mx-auto">
        <PageHero
          icon={<Bot size={40} className="text-white" />}
          title="새 챗봇 만들기"
        />

        <form onSubmit={handleSubmit} className="space-y-10">
          {/* Section 1: Basic Info */}
          <section>
            <SectionTitle
              icon={<Sparkles size={16} className="text-blue-600" />}
              iconBgColor="bg-blue-100"
            >
              기본 정보
            </SectionTitle>

            <div className="space-y-6 pl-11">
              <Input
                label="챗봇 이름"
                name="name"
                type="text"
                value={formData.name}
                onChange={handleInputChange}
                error={errors.name}
                placeholder="예: 사내 매뉴얼 챗봇"
                required
              />

              <Textarea
                label="설명"
                id="description"
                name="description"
                value={formData.description}
                onChange={handleInputChange}
                placeholder="이 챗봇이 어떤 역할을 하는지 설명해주세요"
                rows={3}
              />

              <Input
                label="태그"
                name="tag"
                type="text"
                value={formData.tag || ''}
                onChange={handleInputChange}
                placeholder="예: 고객지원, 사내용"
              />
            </div>
          </section>

          <div className="border-t border-gray-200" />

          {/* Section 2: Settings */}
          <section>
            <SectionTitle
              icon={<Settings size={16} className="text-purple-600" />}
              iconBgColor="bg-purple-100"
            >
              공개 설정
            </SectionTitle>

            <div className="pl-11">
              <div className="flex items-center justify-between p-5 rounded-2xl bg-gradient-to-r from-gray-50 to-gray-100/50 border border-gray-200">
                <div>
                  <div className="font-medium text-gray-900 mb-1">공개 여부</div>
                  <p className="text-sm text-gray-500">
                    {formData.is_public
                      ? '모든 사용자가 이 챗봇을 사용할 수 있습니다'
                      : '관리자만 이 챗봇을 사용할 수 있습니다'}
                  </p>
                </div>
                <div className="flex items-center gap-3">
                  <span className={`
                    px-3 py-1 rounded-full text-sm font-medium transition-all
                    ${formData.is_public
                      ? 'bg-blue-100 text-blue-700'
                      : 'bg-gray-200 text-gray-600'}
                  `}>
                    {formData.is_public ? '공개' : '비공개'}
                  </span>
                  <ToggleSwitch
                    checked={formData.is_public ?? true}
                    onChange={handleToggleChange}
                  />
                </div>
              </div>
            </div>
          </section>

          {/* Action Buttons */}
          <div className="flex justify-end gap-4 pt-6">
            <Button
              type="button"
              variant="outline"
              size="large"
              onClick={handleCancel}
              disabled={isLoading}
            >
              취소
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="large"
              disabled={isLoading}
            >
              {isLoading ? '생성 중...' : '챗봇 생성'}
            </Button>
          </div>
        </form>
      </div>
    </main>
  );
}

export default ChatbotCreatePage;
