import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Button from '../../components/common/Button';
import Input from '../../components/common/Input';
import PasswordInput from '../../components/common/PasswordInput';
import TextLink from '../../components/common/TextLink';
import AuthPageLayout from '../../layouts/AuthPageLayout';
import { ROUTES } from '../../constants/routes';
import { useCreateSignup, useCheckUsername } from '../../hooks/signup/useSignup';

function SignupPage() {
  const navigate = useNavigate();
  const { checkUsername, isLoading: isCheckingUsername } = useCheckUsername();
  const { createSignup, isLoading: isSubmitting } = useCreateSignup();

  const [formData, setFormData] = useState({
    username: '',
    password: '',
    confirmPassword: '',
    name: '',
  });
  const [isUsernameChecked, setIsUsernameChecked] = useState(false);
  const [isUsernameAvailable, setIsUsernameAvailable] = useState(false);
  const [errors, setErrors] = useState<{ [key: string]: string }>({});

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));

    // 아이디 변경 시 중복 확인 초기화
    if (name === 'username') {
      setIsUsernameChecked(false);
      setIsUsernameAvailable(false);
    }

    // 비밀번호 확인 실시간 검증
    if (name === 'confirmPassword' && value) {
      if (formData.password !== value) {
        setErrors(prev => ({ ...prev, confirmPassword: '비밀번호가 일치하지 않습니다' }));
      } else {
        setErrors(prev => ({ ...prev, confirmPassword: '' }));
      }
    }

    // 비밀번호 변경 시 비밀번호 확인란도 재검증
    if (name === 'password' && formData.confirmPassword) {
      if (value !== formData.confirmPassword) {
        setErrors(prev => ({ ...prev, confirmPassword: '비밀번호가 일치하지 않습니다' }));
      } else {
        setErrors(prev => ({ ...prev, confirmPassword: '' }));
      }
    }

    // 에러 메시지 초기화 (비밀번호 확인란 제외)
    if (errors[name] && name !== 'confirmPassword') {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const handleUsernameCheck = async () => {
    if (!formData.username) {
      setErrors(prev => ({ ...prev, username: '아이디를 입력해주세요' }));
      return;
    }

    const result = await checkUsername(formData.username);

    if (result) {
      setIsUsernameAvailable(result.is_available);
      setIsUsernameChecked(true);

      if (!result.is_available) {
        setErrors(prev => ({ ...prev, username: '이미 사용 중인 아이디입니다' }));
      } else {
        setErrors(prev => ({ ...prev, username: '' }));
      }
    } else {
      setErrors(prev => ({ ...prev, username: '중복 확인에 실패했습니다' }));
    }
  };

  const validateForm = (): boolean => {
    const newErrors: { [key: string]: string } = {};

    if (!formData.username) {
      newErrors.username = '아이디를 입력해주세요';
    } else if (!isUsernameChecked) {
      newErrors.username = '아이디 중복 확인을 해주세요';
    } else if (!isUsernameAvailable) {
      newErrors.username = '사용할 수 없는 아이디입니다';
    }

    if (!formData.password) {
      newErrors.password = '비밀번호를 입력해주세요';
    } else if (formData.password.length < 4) {
      newErrors.password = '비밀번호는 4자 이상이어야 합니다';
    }

    if (!formData.confirmPassword) {
      newErrors.confirmPassword = '비밀번호 확인을 입력해주세요';
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = '비밀번호가 일치하지 않습니다';
    }

    if (!formData.name) {
      newErrors.name = '이름을 입력해주세요';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    const result = await createSignup({
      username: formData.username,
      password: formData.password,
      name: formData.name,
    });

    if (result) {
      alert('가입 신청이 완료되었습니다.\n관리자 승인 후 로그인이 가능합니다.');
      navigate(ROUTES.AUTH.LOGIN);
    } else {
      alert('가입 신청에 실패했습니다. 다시 시도해주세요.');
    }
  };

  return (
    <AuthPageLayout
      title="회원가입"
      subtitle="관리자 승인 후 사용 가능합니다"
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* 아이디 */}
        <div>
          <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-1">
            아이디 *
          </label>
          <div className="flex gap-2 items-start">
            <div className="flex-1">
              <Input
                type="text"
                id="username"
                name="username"
                value={formData.username}
                onChange={handleInputChange}
                error={errors.username}
                success={isUsernameChecked && isUsernameAvailable ? '✓ 사용 가능한 아이디입니다' : undefined}
                placeholder="아이디 입력"
              />
            </div>
            <Button
              type="button"
              variant="outline"
              size="small"
              onClick={handleUsernameCheck}
              disabled={isCheckingUsername || !formData.username}
              className="whitespace-nowrap"
            >
              {isCheckingUsername ? '확인 중...' : '중복 확인'}
            </Button>
          </div>
        </div>

        {/* 비밀번호 */}
        <PasswordInput
          id="password"
          name="password"
          value={formData.password}
          onChange={handleInputChange}
          label="비밀번호"
          error={errors.password}
          placeholder="비밀번호 입력 (4자 이상)"
          required
        />

        {/* 비밀번호 확인 */}
        <PasswordInput
          id="confirmPassword"
          name="confirmPassword"
          value={formData.confirmPassword}
          onChange={handleInputChange}
          label="비밀번호 확인"
          error={errors.confirmPassword}
          placeholder="비밀번호 재입력"
          required
        />

        {/* 이름 */}
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

        {/* 가입 신청 버튼 */}
        <div className="pt-4">
          <Button
            type="submit"
            variant="primary"
            className="w-full"
            disabled={isSubmitting}
          >
            {isSubmitting ? '신청 중...' : '가입 신청'}
          </Button>
        </div>

        {/* 로그인 안내 */}
        <div className="text-center text-sm text-gray-600 pt-2">
          이미 계정이 있으신가요?{' '}
          <TextLink color="blue" onClick={() => navigate(ROUTES.AUTH.LOGIN)}>
            로그인 하기
          </TextLink>
        </div>
      </form>
    </AuthPageLayout>
  );
}

export default SignupPage;
