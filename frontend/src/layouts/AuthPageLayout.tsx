import type { ReactNode } from 'react';
import Logo from '../components/common/Logo';
import Container from '../components/common/Container';

interface AuthPageLayoutProps {
  title: string;
  subtitle?: string;
  children: ReactNode;
}

function AuthPageLayout({ title, subtitle, children }: AuthPageLayoutProps) {
  return (
    <Container fullHeight centered maxWidth="md" padding="medium" shadow="lg" rounded="2xl">
      <div className="text-center mb-8">
        <Logo className="justify-center mb-4" fontSize={30} clickable={true} />
        <h1 className="text-2xl font-bold text-gray-800">{title}</h1>
        {subtitle && <p className="text-sm text-gray-500 mt-2">{subtitle}</p>}
      </div>
      {children}
    </Container>
  );
}

export default AuthPageLayout;
