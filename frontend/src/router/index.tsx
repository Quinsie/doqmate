import type { RouteObject } from 'react-router-dom';
import PublicLayout from '../layouts/PublicLayout';
import ProtectedLayout from '../layouts/ProtectedLayout';
import NotFoundPage from '../pages/error/NotFoundPage';
import LoginPage from '../pages/auth/LoginPage';
import SignupPage from '../pages/auth/SignupPage';
import FindUsernamePage from '../pages/auth/FindUsernamePage';
import ResetPasswordPage from '../pages/auth/ResetPasswordPage';
import AdminMainPage from '../pages/admin/AdminMainPage';
import AdminListPage from '../pages/admin/settings/AdminListPage';
import ChatbotListPage from '../pages/admin/chatbot/ChatbotListPage';
import ChatbotCreatePage from '../pages/admin/chatbot/ChatbotCreatePage';
import ManualPage from '../pages/admin/manual/ManualPage';
import SignupManagementPage from '../pages/admin/settings/SignupManagementPage';
import ProfileSettingsPage from '../pages/admin/profile/ProfileSettingsPage';
import StatsPage from '../pages/admin/stats/StatsPage';
import ChatPage from '../pages/chat/ChatPage';

// Public Routes: 인증이 필요 없는 라우트
export const publicRoutes: RouteObject[] = [
  {
    path: "/",
    element: <PublicLayout />,
    children: [
      {
        index: true,
        element: <ChatPage />,
      },
      {
        path: "chat/:sessionId?",
        element: <ChatPage />,
      },
      {
        path: "auth",
        children: [
          {
            path: "login",
            element: <LoginPage />,
          },
          {
            path: "signup",
            element: <SignupPage />,
          },
          {
            path: "find-username",
            element: <FindUsernamePage />,
          },
          {
            path: "reset-password",
            element: <ResetPasswordPage />,
          },
        ],
      },
    ],
  },
];

// Protected Routes: 인증이 필요한 라우트
export const protectedRoutes: RouteObject[] = [
  {
    path: "/admin",
    element: <ProtectedLayout />,
    errorElement: <NotFoundPage />,
    children: [
      {
        index: true,
        element: <AdminMainPage />,
      },
      {
        path: "chatbotlist",
        element: <ChatbotListPage />,
      },
      {
        path: "chatbot",
        children: [
          {
            path: "create",
            element: <ChatbotCreatePage />,
          },
          {
            path: ":chatbotId/manual",
            element: <ManualPage />,
          },
        ],
      },
      {
        path: "signup-management",
        element: <SignupManagementPage />,
      },
      {
        path: "admins",
        element: <AdminListPage />,
      },
      {
        path: "profile-settings",
        element: <ProfileSettingsPage />,
      },
      {
        path: "stats",
        element: <StatsPage />,
      },
    ],
  },
];

// 모든 라우트를 결합
export const routes: RouteObject[] = [
  ...publicRoutes,
  ...protectedRoutes,
  {
    path: "*",
    element: <NotFoundPage />,
  },
];
