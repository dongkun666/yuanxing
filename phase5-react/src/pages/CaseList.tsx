import { useState, useEffect } from 'react';
import Layout from '../components/layout/Layout';
import Table from '../components/data/Table';
import Card from '../components/data/Card';
import Button from '../components/common/Button';
import Input from '../components/common/Input';
import Modal from '../components/common/Modal';
import { caseApi } from '../api';
import { useCacheStore } from '../store';
import type { Case, CaseRole, CaseStatus } from '../types';

const STATUS_BADGE: Record<CaseStatus, string> = {
  '进行中': 'bg-brand-tint text-brand',
  '待开庭': 'bg-warning-tint text-orange-700',
  '已归档': 'bg-success-tint text-success',
  '仲裁中': 'bg-wiki-tint text-wiki',
};

const ROLE_LABEL: Record<CaseRole, string> = {
  '代理原告': '原告',
  '代理被告': '被告',
  '第三方': '第三方',
};

export default function CaseList() {
  const [cases, setCases] = useState<Case[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<CaseStatus | 'all'>('all');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newCase, setNewCase] = useState({
    name: '',
    role: '代理原告' as CaseRole,
    filedAt: new Date().toISOString().split('T')[0],
  });

  const { setCases: setCachedCases, getCases: getCachedCases, clearAll } = useCacheStore();

  useEffect(() => {
    const cached = getCachedCases('all');
    if (cached) {
      setCases(cached);
    } else {
      fetchCases();
    }
  }, []);

  const fetchCases = async () => {
    try {
      const response = await caseApi.list();
      setCases(response.data);
      setCachedCases('all', response.data);
    } catch (error) {
      console.error('Failed to fetch cases:', error);
    }
  };

  const handleSearch = () => {
    if (searchTerm.trim()) {
      caseApi.search(searchTerm.trim()).then(setCases);
    } else {
      fetchCases();
    }
  };

  const handleCreate = async () => {
    if (!newCase.name.trim()) return;
    try {
      await caseApi.create(newCase);
      setShowCreateModal(false);
      setNewCase({ name: '', role: '代理原告', filedAt: new Date().toISOString().split('T')[0] });
      clearAll();
      fetchCases();
    } catch (error) {
      console.error('Failed to create case:', error);
    }
  };

  const handleRowClick = (row: Case) => {
    console.log('Case clicked:', row.id);
  };

  const filteredCases = cases.filter((c) => {
    const matchesSearch = searchTerm ? c.name.toLowerCase().includes(searchTerm.toLowerCase()) : true;
    const matchesStatus = statusFilter === 'all' ? true : c.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const columns = [
    { key: 'name', label: '案件名称', width: '40%', render: (value: unknown) => (
      <span className="font-medium text-brand truncate">{String(value)}</span>
    )},
    { key: 'role', label: '角色', width: '15%', render: (value: unknown) => (
      <span className="text-fg-secondary">{ROLE_LABEL[value as CaseRole]}</span>
    )},
    { key: 'filedAt', label: '立案日期', width: '20%' },
    { key: 'status', label: '状态', width: '25%', render: (value: unknown) => (
      <span className={`${STATUS_BADGE[value as CaseStatus]} text-[10px] font-medium px-2 py-0.5 rounded-full`}>
        {String(value)}
      </span>
    )},
  ];

  return (
    <Layout title="案件列表" subtitle="管理您的所有案件">
      <div className="p-4 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Input
              type="text"
              placeholder="搜索案件名称..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              icon="mdi:search"
              className="w-64"
            />
            <Button variant="secondary" onClick={handleSearch}>
              搜索
            </Button>
          </div>
          <div className="flex items-center gap-3">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value as CaseStatus | 'all')}
              className="px-3 py-2 bg-bg-subtle border border-bg-border rounded-lg text-sm focus:outline-none focus:border-brand"
            >
              <option value="all">全部状态</option>
              <option value="进行中">进行中</option>
              <option value="待开庭">待开庭</option>
              <option value="已归档">已归档</option>
              <option value="仲裁中">仲裁中</option>
            </select>
            <Button onClick={() => setShowCreateModal(true)} icon="mdi:plus">
              新建案件
            </Button>
          </div>
        </div>

        <Card>
          <Table<Case>
            columns={columns}
            data={filteredCases}
            onRowClick={handleRowClick}
            emptyText="暂无案件"
          />
        </Card>

        <Modal
          isOpen={showCreateModal}
          onClose={() => setShowCreateModal(false)}
          title="新建案件"
          footer={
            <>
              <Button variant="secondary" onClick={() => setShowCreateModal(false)}>
                取消
              </Button>
              <Button onClick={handleCreate} disabled={!newCase.name.trim()}>
                创建
              </Button>
            </>
          }
        >
          <div className="space-y-4">
            <Input
              label="案件名称"
              value={newCase.name}
              onChange={(e) => setNewCase({ ...newCase, name: e.target.value })}
              placeholder="请输入案件名称"
            />
            <div>
              <label className="block text-xs text-fg-secondary font-medium mb-1.5">
                角色
              </label>
              <select
                value={newCase.role}
                onChange={(e) => setNewCase({ ...newCase, role: e.target.value as CaseRole })}
                className="w-full px-4 py-2.5 bg-bg-subtle border border-bg-border rounded-lg text-sm focus:outline-none focus:border-brand"
              >
                <option value="代理原告">代理原告</option>
                <option value="代理被告">代理被告</option>
                <option value="第三方">第三方</option>
              </select>
            </div>
            <Input
              label="立案日期"
              type="date"
              value={newCase.filedAt}
              onChange={(e) => setNewCase({ ...newCase, filedAt: e.target.value })}
            />
          </div>
        </Modal>
      </div>
    </Layout>
  );
}