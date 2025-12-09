import { MonitorCog } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import Logo from '../common/Logo';
import { ROUTES } from '../../constants/routes';
import { isAuthenticated } from '../../utils/permissions';

function Header() {
  const navigate = useNavigate();
  const isLoggedIn = isAuthenticated();

  return (
    <header className="px-8 py-5 flex items-center justify-between">
      {/* 왼쪽: 로고 */}
      <div className="flex items-center">
        <Logo clickable={true}/>
      </div>

      {/* 가운데: 페이지 타이틀 */}
      {/* <div className="flex-1 text-center">
        {title && <h2 className="text-[25px] font-bold text-gray-800">{title}</h2>}
      </div> */}

      {/* 오른쪽: 액션 버튼들 */}
      <div className="flex gap-3">
        {isLoggedIn && (
          <button
            onClick={() => navigate(ROUTES.ADMIN.MAIN)}
            className=" hover:bg-gray-100 rounded-lg transition-colors cursor-pointer"
            aria-label="관리자 페이지"
          >
            <MonitorCog size={24} className="text-blue-500" />
          </button>
        )}
      </div>
    </header>
  );
}

export default Header;
