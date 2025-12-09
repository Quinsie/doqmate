import { useState, useEffect } from 'react';
import { Users } from 'lucide-react';
import type { Admin } from '../../../types/auth/auth';
import { Table } from '../../../components/common/Table';
import type { TableColumn } from '../../../components/common/Table';
import Button from '../../../components/common/Button';
import PageHero from '../../../components/common/PageHero';
import Modal from '../../../components/common/Modal';
import { useGetAdmins, useDeleteAdmin } from '../../../hooks/admin/useAdmin';

function AdminListPage() {
  const [admins, setAdmins] = useState<Admin[]>([]);
  const [selectedAdmin, setSelectedAdmin] = useState<Admin | null>(null);
  const [showRemoveModal, setShowRemoveModal] = useState(false);

  const { getAdmins, isLoading: isLoadingAdmins, error: fetchError } = useGetAdmins();
  const { deleteAdmin, isLoading: isDeleting, error: deleteError } = useDeleteAdmin();

  useEffect(() => {
    loadAdmins();
  }, []);

  const loadAdmins = async () => {
    const data = await getAdmins();
    if (data && data.admins) {
      setAdmins(data.admins);
    }
  };

  const handleRemove = async () => {
    if (!selectedAdmin) return;

    const success = await deleteAdmin(selectedAdmin.admin_id);

    if (success) {
      setAdmins(prev => prev.filter(a => a.admin_id !== selectedAdmin.admin_id));
      alert(`${selectedAdmin.name}님이 추방되었습니다.`);
    } else {
      alert(deleteError || '추방에 실패했습니다.');
    }

    setShowRemoveModal(false);
    setSelectedAdmin(null);
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

  const columns: TableColumn<Admin>[] = [
    {
      key: 'index',
      label: 'No.',
      align: 'center',
      render: (_, __, index) => (
        <span className="text-gray-600 font-medium">{index + 1}</span>
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
      key: 'username',
      label: '아이디',
      align: 'center',
      render: (value) => (
        <span className="text-gray-800 font-semibold">{value as string}</span>
      ),
    },
    {
      key: 'created_at',
      label: '가입 일시',
      align: 'center',
      render: (value) => (
        <span className="text-gray-600">
          {value ? formatDate(value as string) : '-'}
        </span>
      ),
    },
    {
      key: 'actions',
      label: '관리',
      align: 'center',
      render: (_, row) => (
        <div className="flex items-center justify-center gap-2">
          <Button
            variant="red"
            size="small"
            onClick={(e) => {
              e.stopPropagation();
              setSelectedAdmin(row);
              setShowRemoveModal(true);
            }}
            disabled={isDeleting}
          >
            추방
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
            icon={<Users size={40} className="text-white" />}
            title="관리자 목록"
            gradient="from-orange-500 via-orange-600 to-red-600"
          />

          {fetchError ? (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-12 text-center">
              <p className="text-red-500">{fetchError}</p>
              <Button className="mt-4" onClick={loadAdmins}>다시 시도</Button>
            </div>
          ) : (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <Table
                data={admins}
                columns={columns}
                keyExtractor={(row) => row.admin_id}
                isLoading={isLoadingAdmins}
                emptyMessage="등록된 관리자가 없습니다."
              />
            </div>
          )}
        </div>
      </main>

      <Modal
        isOpen={showRemoveModal}
        title="관리자 추방"
        message={`${selectedAdmin?.name}(${selectedAdmin?.username})님을 추방하시겠습니까?`}
        confirmText="추방"
        cancelText="취소"
        onConfirm={handleRemove}
        onCancel={() => {
          setShowRemoveModal(false);
          setSelectedAdmin(null);
        }}
      />
    </>
  );
}

export default AdminListPage;
