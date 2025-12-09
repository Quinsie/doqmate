import { useNavigate } from "react-router-dom";
import { ROUTES } from '../../constants/routes';

interface LogoProps {
  fontSize?: number; // px 단위
  className?: string;
  onClick?: () => void;
  clickable?: boolean;
}

function Logo({
  fontSize = 24,
  className = '',
  onClick,
  clickable = true
}: LogoProps) {
  const navigate = useNavigate();

  const handleLogoClick = () => {
    if (!clickable) return;

    if (onClick) {
      onClick();
    } else {
      navigate( ROUTES.HOME);
    }
  };

  return (
    <h1
      className={`
        font-bold
        bg-gradient-to-r from-blue-400 to-blue-500
        bg-clip-text text-transparent
        ${clickable ? 'cursor-pointer' : ''}
        ${className}
      `}
      style={{ fontSize: `${fontSize}px` }}
      onClick={handleLogoClick}
    >
      DoQ-Mate
    </h1>
  );
}

export default Logo;
