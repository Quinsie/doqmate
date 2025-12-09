import { useState, useEffect } from 'react';
import { UserPlus } from 'lucide-react';
import type { Signup } from '../../../types/auth/signup';
import { Table } from '../../../components/common/Table';
import type { TableColumn } from '../../../components/common/Table';
import Button from '../../../components/common/Button';
import PageHero from '../../../components/common/PageHero';
import Modal from '../../../components/common/Modal';
import { useGetSignups, useApproveSignup, useRejectSignup } from '../../../hooks/signup/useSignup';

function SignupManagementPage() {
  const [signups, setSignups] = useState<Signup[]>([]);
  const [selectedSignup, setSelectedSignup] = useState<Signup | null>(null);
  const [showApproveModal, setShowApproveModal] = useState(false);
  const [showRejectModal, setShowRejectModal] = useState(false);

  const { getSignups, isLoading: isLoadingList } = useGetSignups();
  const { approveSignup, isLoading: isApproving } = useApproveSignup();
  const { rejectSignup, isLoading: isRejecting } = useRejectSignup();

  useEffect(() => {
    loadSignups();
  }, []);

  const loadSignups = async () => {
    const data = await getSignups();
    if (data && data.signups) {
      setSignups(data.signups);
    } else {
      setSignups([]);
    }
  };

  const handleApprove = async () => {
    if (!selectedSignup) return;

    const success = await approveSignup(selectedSignup.signup_id);

    if (success) {
      alert(`${selectedSignup.name}님의 가입이 승인되었습니다.`);
      await loadSignups();
    } else {
      alert('가입 승인에 실패했습니다.');
    }

    setShowApproveModal(false);
    setSelectedSignup(null);
  };

  const handleReject = async () => {
    if (!selectedSignup) return;

    const success = await rejectSignup(selectedSignup.signup_id);

    if (success) {
      alert(`${selectedSignup.name}님의 가입 신청이 반려되었습니다.`);
      await loadSignups();
    } else {
      alert('가입 반려에 실패했습니다.');
    }

    setShowRejectModal(false);
    setSelectedSignup(null);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString('ko-KR', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const columns: TableColumn<Signup>[] = [
    {
      key: 'index',
      label: 'No.',
      align: 'center',
      render: (_, __, index) => (
        <span className="text-gray-600 font-medium">{index + 1}</span>
      ),
    },
    {
      key: 'username',
      label: '아이디',
      align: 'center',
      render: (value) => (
        <span className="text-gray-800 font-semibold">{value as string}</span>
      ),
    },
    {
      key: 'name',
      label: '이름',
      align: 'center',
      render: (value) => (
        <span className="text-gray-800">{value as string}</span>
      ),
    },
    {
      key: 'created_at',
      label: '신청일시',
      align: 'center',
      render: (value) => (
        <span className="text-gray-600">{formatDate(value as string)}</span>
      ),
    },
    {
      key: 'actions',
      label: '관리',
      align: 'center',
      render: (_, row) => (
        <div className="flex items-center justify-center gap-2">
          <Button
            variant="primary"
            size="small"
            onClick={(e) => {
              e.stopPropagation();
              setSelectedSignup(row);
              setShowApproveModal(true);
            }}
            disabled={isApproving || isRejecting}
          >
            승인
          </Button>
          <Button
            variant="secondary"
            size="small"
            onClick={(e) => {
              e.stopPropagation();
              setSelectedSignup(row);
              setShowRejectModal(true);
            }}
            disabled={isApproving || isRejecting}
          >
            반려
          </Button>
        </div>
      ),
    },
  ];

  return (
    <>
      <main className="flex-1 p-8 lg:p-12">
        <div className="max-w-5xl mx-auto">
          <PageHero
            icon={<UserPlus size={40} className="text-white" />}
            title="가입 신청 관리"
            gradient="from-violet-500 via-violet-600 to-purple-600"
          />

          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <Table
              data={signups}
              columns={columns}
              keyExtractor={(row) => row.signup_id}
              isLoading={isLoadingList}
              emptyMessage="대기 중인 가입 신청이 없습니다."
            />
          </div>
        </div>
      </main>

      <Modal
        isOpen={showApproveModal}
        title="가입 승인"
        message={`${selectedSignup?.name}(${selectedSignup?.username})님의 가입을 승인하시겠습니까?`}
        confirmText="승인"
        cancelText="취소"
        onConfirm={handleApprove}
        onCancel={() => {
          setShowApproveModal(false);
          setSelectedSignup(null);
        }}
      />

      <Modal
        isOpen={showRejectModal}
        title="가입 반려"
        message={`${selectedSignup?.name}(${selectedSignup?.username})님의 가입 신청을 반려하시겠습니까?`}
        confirmText="반려"
        cancelText="취소"
        onConfirm={handleReject}
        onCancel={() => {
          setShowRejectModal(false);
          setSelectedSignup(null);
        }}
      />
    </>
  );
}

export default SignupManagementPage;
