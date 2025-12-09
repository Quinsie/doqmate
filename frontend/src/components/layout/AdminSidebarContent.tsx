import { useNavigate } from 'react-router-dom';
import ProfileCard from '../admin/profile/ProfileCard';
import Dropdown from '../common/Dropdown';
import NavItem from './NavItem';
import SubMenuItem from './SubMenuItem';
import { ROUTES } from '../../constants/routes';
import { getAdminName, getAccessToken } from '../../utils/authStorage';

interface AdminSidebarContentProps {
  isCollapsed: boolean;
}

function AdminSidebarContent({ isCollapsed }: AdminSidebarContentProps) {
  const navigate = useNavigate();
  const adminName = getAdminName();
  const isLoggedIn = !!getAccessToken();

  return (
    <>
      <div className={`transition-opacity duration-300 ${isCollapsed ? 'opacity-0 pointer-events-none' : 'opacity-100'}`}>
        {!isCollapsed && (
          <ProfileCard
            userName={adminName || '관리자'}
            isLoggedIn={isLoggedIn}
          />
        )}
      </div>

      <nav className="mt-4 flex-1">
        <NavItem
          icon="📌"
          label="대시보드"
          isCollapsed={isCollapsed}
          onClick={() => navigate(ROUTES.ADMIN.MAIN)}
        />

        <Dropdown
          isCollapsed={isCollapsed}
          collapsedNavigateTo={ROUTES.ADMIN.CHATBOT_LIST}
          trigger={
            <NavItem
              icon="🤖"
              label="챗봇 리스트"
              hasDropdown={true}
            />
          }
        >
          <SubMenuItem label="챗봇 목록 보기" onClick={() => navigate(ROUTES.ADMIN.CHATBOT_LIST)} />
          <SubMenuItem label="챗봇 생성" onClick={() => navigate(ROUTES.ADMIN.CHATBOT_CREATE)} />
        </Dropdown>

        <NavItem
          icon="📊"
          label="통계"
          isCollapsed={isCollapsed}
          onClick={() => navigate(ROUTES.ADMIN.STATS)}
        />

        <Dropdown
          isCollapsed={isCollapsed}
          collapsedNavigateTo={ROUTES.ADMIN.SIGNUP_MANAGEMENT}
          trigger={
            <NavItem
              icon="⚙️"
              label="설정"
              hasDropdown={true}
            />
          }
        >
          <SubMenuItem label="가입 신청 관리" onClick={() => navigate(ROUTES.ADMIN.SIGNUP_MANAGEMENT)} />
          <SubMenuItem label="관리자 목록" onClick={() => navigate(ROUTES.ADMIN.ADMIN_LIST)}/>
          <SubMenuItem label="프로필 설정" onClick={() => navigate(ROUTES.ADMIN.SETTINGS)} />
        </Dropdown>
      </nav>
    </>
  );
}

export default AdminSidebarContent;
