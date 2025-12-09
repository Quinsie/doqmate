interface WelcomeTitleProps {
  children: React.ReactNode;
}

function WelcomeTitle({ children }: WelcomeTitleProps) {
  return (
    <div className="text-center mb-12">
      <div className="relative inline-block">
        {/* 배경 장식 */}
        <div className="absolute inset-0 bg-gradient-to-r from-blue-400/10 via-purple-400/10 to-blue-400/10 blur-2xl -z-10 transform scale-150"></div>

        {/* 메인 타이틀 */}
        <h1 className="text-3xl md:text-4xl font-bold bg-gradient-to-r from-blue-500 via-purple-500 to-blue-500 bg-clip-text text-transparent leading-relaxed px-4 py-2 animate-gradient">
          {children}
        </h1>

        {/* 하단 장식선 */}
        <div className="mt-4 flex justify-center gap-1">
          <div className="h-1 w-12 bg-gradient-to-r from-transparent via-blue-500 to-transparent rounded-full"></div>
          <div className="h-1 w-12 bg-gradient-to-r from-transparent via-purple-500 to-transparent rounded-full"></div>
          <div className="h-1 w-12 bg-gradient-to-r from-transparent via-blue-500 to-transparent rounded-full"></div>
        </div>
      </div>
    </div>
  );
}

export default WelcomeTitle;
