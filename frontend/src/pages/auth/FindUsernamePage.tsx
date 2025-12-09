import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Button from '../../components/common/Button';
import Input from '../../components/common/Input';
import TextLink from '../../components/common/TextLink';
import AuthPageLayout from '../../layouts/AuthPageLayout';
import TabNavigation from '../../components/auth/TabNavigation';
import ResultBox from '../../components/auth/ResultBox';
import { useFindUsername } from '../../hooks/auth/useAuth';
import { ROUTES } from '../../constants/routes';

function FindUsernamePage() {
  const navigate = useNavigate();
  const { findUsername, isLoading, result } = useFindUsername();
  const [name, setName] = useState('');
  const [error, setError] = useState('');

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setName(e.target.value);
    if (error) {
      setError('');
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!name) {
      setError('이름을 입력해주세요');
      return;
    }

    try {
      await findUsername(name);
    } catch (err) {
      setError('아이디 찾기에 실패했습니다. 다시 시도해주세요.');
    }
  };

  return (
    <AuthPageLayout
      title="아이디 찾기"
      subtitle="가입 시 입력한 이름을 입력해주세요"
    >
      <TabNavigation
        tabs={[
          { label: '아이디 찾기', isActive: true, onClick: () => {} },
          { label: '비밀번호 찾기', isActive: false, onClick: () => navigate(ROUTES.AUTH.RESET_PASSWORD) },
        ]}
      />

      <form onSubmit={handleSubmit} className="space-y-4">
        <Input
          type="text"
          id="name"
          name="name"
          value={name}
          onChange={handleInputChange}
          label="이름"
          error={error}
          placeholder="이름 입력"
          required
        />

        {result && result.length > 0 && (
          <ResultBox type="info">
            <p className="text-sm font-medium text-gray-700 mb-2">찾은 아이디 목록:</p>
            <ul className="space-y-1">
              {result.map((username, index) => (
                <li key={index} className="text-sm text-gray-800">
                  {username}
                </li>
              ))}
            </ul>
          </ResultBox>
        )}

        {result && result.length === 0 && (
          <ResultBox type="warning">
            <p className="text-sm text-gray-700">해당 이름으로 가입된 계정을 찾을 수 없습니다.</p>
          </ResultBox>
        )}

        <div className="pt-4">
          <Button
            type="submit"
            variant="primary"
            className="w-full"
            disabled={isLoading}
          >
            {isLoading ? '찾는 중...' : '아이디 찾기'}
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

export default FindUsernamePage;
