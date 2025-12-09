import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Bot,
  UserPlus,
  Users,
  BarChart3,
  User,
  ArrowRight,
} from 'lucide-react';
import { ROUTES } from '../../constants/routes';
import { getAdminName } from '../../utils/authStorage';
import { useGetChatbots } from '../../hooks/chatbot/useChatbot';
import { useGetSignups } from '../../hooks/signup/useSignup';
import { useGetOverviewStats } from '../../hooks/admin/useStats';
import WelcomeTitle from '../../components/common/WelcomeTitle';

interface QuickActionCardProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  gradient: string;
  onClick: () => void;
  badge?: number;
}

function QuickActionCard({ icon, title, description, gradient, onClick, badge }: QuickActionCardProps) {
  return (
    <button
      onClick={onClick}
      className="group relative bg-white rounded-2xl shadow-sm border border-gray-100 p-6 text-left hover:shadow-lg hover:border-gray-200 transition-all duration-300 hover:-translate-y-1"
    >
      <div className={`inline-flex items-center justify-center w-14 h-14 rounded-xl bg-gradient-to-br ${gradient} shadow-lg mb-4`}>
        {icon}
      </div>
      {badge !== undefined && badge > 0 && (
        <span className="absolute top-4 right-4 inline-flex items-center justify-center px-2.5 py-1 text-xs font-bold text-white bg-red-500 rounded-full">
          {badge}
        </span>
      )}
      <h3 className="text-lg font-semibold text-gray-900 mb-1 group-hover:text-blue-600 transition-colors">
        {title}
      </h3>
      <p className="text-sm text-gray-500 mb-3">{description}</p>
      <div className="flex items-center text-sm font-medium text-blue-600 opacity-0 group-hover:opacity-100 transition-opacity">
        바로가기 <ArrowRight size={16} className="ml-1" />
      </div>
    </button>
  );
}

interface StatMiniCardProps {
  icon: string;
  label: string;
  value: number;
  color: string;
}

function StatMiniCard({ icon, label, value, color }: StatMiniCardProps) {
  return (
    <div className={`bg-gradient-to-br ${color} rounded-2xl p-5 text-white`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-3xl">{icon}</span>
        <span className="text-3xl font-bold">{value.toLocaleString()}</span>
      </div>
      <p className="text-sm opacity-90">{label}</p>
    </div>
  );
}

function AdminMainPage() {
  const adminName = getAdminName() || '관리자';
  const navigate = useNavigate();

  const { getChatbots } = useGetChatbots();
  const { getSignups } = useGetSignups();
  const { getOverviewStats } = useGetOverviewStats();

  const [stats, setStats] = useState({
    chatbotCount: 0,
    pendingSignups: 0,
    totalQueries: 0,
    isLoading: true,
  });

  useEffect(() => {
    const loadStats = async () => {
      const [chatbotsData, signupsData, overviewData] = await Promise.all([
        getChatbots(),
        getSignups(),
        getOverviewStats(),
      ]);

      setStats({
        chatbotCount: chatbotsData?.chatbots?.length || 0,
        pendingSignups: signupsData?.signups?.length || 0,
        totalQueries: overviewData?.total_queries || 0,
        isLoading: false,
      });
    };

    loadStats();
  }, []);

  const quickActions = [
    {
      icon: <Bot size={28} className="text-white" />,
      title: '챗봇 관리',
      description: '챗봇을 생성하고 관리하세요',
      gradient: 'from-blue-500 to-indigo-600',
      route: ROUTES.ADMIN.CHATBOT_LIST,
    },
    {
      icon: <UserPlus size={28} className="text-white" />,
      title: '가입 신청',
      description: '대기 중인 가입 신청을 처리하세요',
      gradient: 'from-violet-500 to-purple-600',
      route: ROUTES.ADMIN.SIGNUP_MANAGEMENT,
      badge: stats.pendingSignups,
    },
    {
      icon: <Users size={28} className="text-white" />,
      title: '관리자 목록',
      description: '관리자를 조회하고 관리하세요',
      gradient: 'from-orange-500 to-red-600',
      route: ROUTES.ADMIN.ADMIN_LIST,
    },
    {
      icon: <BarChart3 size={28} className="text-white" />,
      title: '통계',
      description: '사용 현황을 분석하세요',
      gradient: 'from-cyan-500 to-teal-600',
      route: ROUTES.ADMIN.STATS,
    },
    {
      icon: <User size={28} className="text-white" />,
      title: '프로필 설정',
      description: '내 정보를 관리하세요',
      gradient: 'from-emerald-500 to-green-600',
      route: ROUTES.ADMIN.SETTINGS,
    },
  ];

  return (
    <main className="flex-1 p-8 lg:p-12 overflow-auto">
      <div className="max-w-6xl mx-auto">
        {/* 인사말 섹션 */}
        <WelcomeTitle>{adminName}님 환영합니다.</WelcomeTitle>

        {/* 요약 통계 */}
        {!stats.isLoading && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-10">
            <StatMiniCard
              icon="🤖"
              label="등록된 챗봇"
              value={stats.chatbotCount}
              color="from-blue-500 to-blue-600"
            />
            <StatMiniCard
              icon="📝"
              label="대기 중인 가입 신청"
              value={stats.pendingSignups}
              color="from-violet-500 to-purple-600"
            />
            <StatMiniCard
              icon="💬"
              label="전체 질의 수"
              value={stats.totalQueries}
              color="from-cyan-500 to-teal-600"
            />
          </div>
        )}

        {/* 알림 배너 */}
        {stats.pendingSignups > 0 && (
          <div
            onClick={() => navigate(ROUTES.ADMIN.SIGNUP_MANAGEMENT)}
            className="mb-8 p-4 bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200 rounded-xl flex items-center justify-between cursor-pointer hover:from-amber-100 hover:to-orange-100 transition-colors"
          >
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-amber-100 rounded-full flex items-center justify-center">
                <UserPlus size={20} className="text-amber-600" />
              </div>
              <div>
                <p className="font-medium text-amber-900">
                  대기 중인 가입 신청이 {stats.pendingSignups}건 있습니다
                </p>
                <p className="text-sm text-amber-700">클릭하여 확인하세요</p>
              </div>
            </div>
            <ArrowRight size={20} className="text-amber-600" />
          </div>
        )}

        {/* 빠른 액션 */}
        <div className="mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">빠른 액션</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {quickActions.map((action) => (
              <QuickActionCard
                key={action.route}
                icon={action.icon}
                title={action.title}
                description={action.description}
                gradient={action.gradient}
                onClick={() => navigate(action.route)}
                badge={action.badge}
              />
            ))}
          </div>
        </div>
      </div>
    </main>
  );
}

export default AdminMainPage;
