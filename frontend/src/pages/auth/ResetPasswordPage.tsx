import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Button from '../../components/common/Button';
import Input from '../../components/common/Input';
import TextLink from '../../components/common/TextLink';
import AuthPageLayout from '../../layouts/AuthPageLayout';
import TabNavigation from '../../components/auth/TabNavigation';
import ResultBox from '../../components/auth/ResultBox';
import { useResetPassword } from '../../hooks/auth/useAuth';
import { ROUTES } from '../../constants/routes';

function ResetPasswordPage() {
  const navigate = useNavigate();
  const { resetPassword, isLoading, tempPassword } = useResetPassword();
  const [formData, setFormData] = useState({
    username: '',
    name: '',
  });
  const [errors, setErrors] = useState<{ [key: string]: string }>({});

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const newErrors: { [key: string]: string } = {};
    if (!formData.username) {
      newErrors.username = '아이디를 입력해주세요';
    }
    if (!formData.name) {
      newErrors.name = '이름을 입력해주세요';
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    try {
      await resetPassword(formData.username, formData.name);
    } catch (err) {
      setErrors({ username: '비밀번호 재설정에 실패했습니다. 아이디와 이름을 확인해주세요.' });
    }
  };

  return (
    <AuthPageLayout
      title="비밀번호 찾기"
      subtitle="가입 시 입력한 아이디와 이름을 입력해주세요"
    >
      <TabNavigation
        tabs={[
          { label: '아이디 찾기', isActive: false, onClick: () => navigate(ROUTES.AUTH.FIND_USERNAME) },
          { label: '비밀번호 찾기', isActive: true, onClick: () => {} },
        ]}
      />

      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          type="text"
          id="username"
          name="username"
          value={formData.username}
          onChange={handleInputChange}
          label="아이디"
          error={errors.username}
          placeholder="아이디 입력"
          required
        />

        <Input
          type="text"
          id="name"
          name="name"
          value={formData.name}
          onChange={handleInputChange}
          label="이름"
          error={errors.name}
          placeholder="이름 입력"
          required
        />

        {tempPassword && (
          <ResultBox type="success">
            <p className="text-sm font-medium text-gray-700 mb-2">임시 비밀번호가 발급되었습니다.</p>
            <p className="text-lg font-bold text-gray-800 mb-2">{tempPassword}</p>
            <p className="text-xs text-gray-600">로그인 후 반드시 비밀번호를 변경해주세요.</p>
          </ResultBox>
        )}

        <div className="pt-4">
          <Button
            type="submit"
            variant="primary"
            className="w-full"
            disabled={isLoading}
          >
            {isLoading ? '처리 중...' : '비밀번호 재설정'}
          </Button>
        </div>

        {/* 로그인 페이지로 */}
        <div className="text-center text-sm text-gray-600 pt-2">
          <TextLink onClick={() => navigate(ROUTES.AUTH.LOGIN)}>
            로그인 페이지로
          </TextLink>
        </div>
      </form>
    </AuthPageLayout>
  );
}

export default ResetPasswordPage;
