import { useNavigate } from 'react-router-dom';
import Button from '../../common/Button';
import { ROUTES } from '../../../constants/routes';
import { forceLogout } from '../../../utils/forceLogout';

interface ProfileCardProps {
  userName?: string;
  isLoggedIn?: boolean;
}

function ProfileCard({
  userName = "김갑동",
  isLoggedIn = false,
}: ProfileCardProps) {
  const navigate = useNavigate();

  const handleLogout = () => {
    forceLogout('logout');
  };

  const handleSettings = () => {
    navigate(ROUTES.ADMIN.SETTINGS);
  };

  const handleLogin = () => {
    navigate(ROUTES.AUTH.LOGIN);
  };

  const handleRegister = () => {
    navigate(ROUTES.AUTH.SIGNUP);
  };
  return (
    <div className="bg-gradient-to-r from-blue-400 to-blue-500 rounded-lg p-6 text-white">
      {isLoggedIn ? (
        <>
          <h2 className="text-xl font-bold mb-1">{userName}님</h2>
          <p className="text-sm mb-6">환영합니다.</p>
          <div className="flex justify-end gap-2">
            <Button
              variant="white"
              size="small"
              onClick={handleSettings}
            >
              설정
            </Button>
            <Button
              variant="white"
              size="small"
              onClick={handleLogout}
            >
              로그아웃
            </Button>
          </div>
        </>
      ) : (
        <>
          <h2 className="text-lg font-bold mb-1">관리자 인증이 필요합니다.</h2>
          <p className="text-sm mb-6">로그인하여 서비스를 이용하세요.</p>
          <div className="flex justify-end gap-2">
            <Button
              variant="white"
              size="small"
              onClick={handleLogin}
            >
              로그인
            </Button>
            <Button
              variant="white"
              size="small"
              onClick={handleRegister}
            >
              회원가입
            </Button>
          </div>
        </>
      )}
    </div>
  );
}

export default ProfileCard;
