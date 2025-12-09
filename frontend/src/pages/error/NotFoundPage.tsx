import { Link } from 'react-router-dom';
import Button from '../../components/common/Button';

function NotFoundPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <h1 className="text-6xl font-bold text-gray-800 mb-4">404</h1>
        <p className="text-xl text-gray-600 mb-8">페이지를 찾을 수 없습니다.</p>
        <Link to="/">
          <Button variant="primary">홈으로 돌아가기</Button>
        </Link>
      </div>
    </div>
  );
}

export default NotFoundPage;
