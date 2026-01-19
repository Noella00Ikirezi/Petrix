import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Search, Server, Trash2, Edit } from 'lucide-react';
import toast from 'react-hot-toast';
import { assetsApi } from '@/api/client';

export default function AssetsPage() {
  const [search, setSearch] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['assets', search],
    queryFn: () => assetsApi.list({ search: search || undefined }),
  });

  const deleteMutation = useMutation({
    mutationFn: assetsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assets'] });
      toast.success('Asset deleted');
    },
    onError: () => toast.error('Failed to delete asset'),
  });

  const assets = data?.items || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Assets
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Manage your IT infrastructure inventory
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="btn btn-primary btn-md"
        >
          <Plus className="mr-2 h-4 w-4" />
          Add Asset
        </button>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
        <input
          type="text"
          placeholder="Search assets..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="input pl-10"
        />
      </div>

      {/* Table */}
      <div className="card overflow-hidden p-0">
        {isLoading ? (
          <div className="flex h-64 items-center justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-500 border-t-transparent" />
          </div>
        ) : assets.length === 0 ? (
          <div className="flex h-64 flex-col items-center justify-center text-gray-500">
            <Server className="mb-2 h-12 w-12" />
            <p>No assets found</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="btn btn-primary btn-sm mt-4"
            >
              Add your first asset
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                    IP Address
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                    Criticality
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                    Vulns
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 bg-white dark:divide-gray-700 dark:bg-gray-800">
                {assets.map((asset: Asset) => (
                  <tr key={asset.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                    <td className="whitespace-nowrap px-6 py-4">
                      <div className="flex items-center">
                        <Server className="mr-3 h-5 w-5 text-gray-400" />
                        <div>
                          <div className="font-medium text-gray-900 dark:text-white">
                            {asset.name}
                          </div>
                          <div className="text-sm text-gray-500 dark:text-gray-400">
                            {asset.hostname || asset.fqdn || '-'}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-900 dark:text-white">
                      {asset.asset_type}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-900 dark:text-white">
                      {asset.ip_address || '-'}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4">
                      <StatusBadge status={asset.status} />
                    </td>
                    <td className="whitespace-nowrap px-6 py-4">
                      <CriticalityBadge criticality={asset.criticality} />
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-900 dark:text-white">
                      {asset.vulnerability_count}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-right">
                      <button className="mr-2 rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-gray-700">
                        <Edit className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => {
                          if (confirm('Delete this asset?')) {
                            deleteMutation.mutate(asset.id);
                          }
                        }}
                        className="rounded p-1 text-gray-400 hover:bg-red-100 hover:text-red-600 dark:hover:bg-red-900"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Create modal placeholder */}
      {showCreateModal && (
        <CreateAssetModal onClose={() => setShowCreateModal(false)} />
      )}
    </div>
  );
}

interface Asset {
  id: string;
  name: string;
  asset_type: string;
  status: string;
  criticality: string;
  ip_address: string | null;
  hostname: string | null;
  fqdn: string | null;
  vulnerability_count: number;
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    active: 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300',
    inactive: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
    maintenance: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300',
    decommissioned: 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300',
  };

  return <span className={`badge ${styles[status] || ''}`}>{status}</span>;
}

function CriticalityBadge({ criticality }: { criticality: string }) {
  const styles: Record<string, string> = {
    critical: 'badge-critical',
    high: 'badge-high',
    medium: 'badge-medium',
    low: 'badge-low',
    info: 'badge-info',
  };

  return <span className={`badge ${styles[criticality] || ''}`}>{criticality}</span>;
}

function CreateAssetModal({ onClose }: { onClose: () => void }) {
  const [formData, setFormData] = useState({
    name: '',
    asset_type: 'server',
    ip_address: '',
    hostname: '',
    criticality: 'medium',
  });
  const queryClient = useQueryClient();

  const createMutation = useMutation({
    mutationFn: assetsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assets'] });
      toast.success('Asset created');
      onClose();
    },
    onError: () => toast.error('Failed to create asset'),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate(formData);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-lg bg-white p-6 dark:bg-gray-800">
        <h2 className="mb-4 text-xl font-bold text-gray-900 dark:text-white">
          Add New Asset
        </h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="label">Name</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="input mt-1"
              required
            />
          </div>
          <div>
            <label className="label">Type</label>
            <select
              value={formData.asset_type}
              onChange={(e) => setFormData({ ...formData, asset_type: e.target.value })}
              className="input mt-1"
            >
              <option value="server">Server</option>
              <option value="workstation">Workstation</option>
              <option value="network">Network Device</option>
              <option value="cloud_instance">Cloud Instance</option>
              <option value="container">Container</option>
              <option value="database">Database</option>
              <option value="application">Application</option>
              <option value="iot">IoT Device</option>
              <option value="other">Other</option>
            </select>
          </div>
          <div>
            <label className="label">IP Address</label>
            <input
              type="text"
              value={formData.ip_address}
              onChange={(e) => setFormData({ ...formData, ip_address: e.target.value })}
              className="input mt-1"
              placeholder="192.168.1.1"
            />
          </div>
          <div>
            <label className="label">Hostname</label>
            <input
              type="text"
              value={formData.hostname}
              onChange={(e) => setFormData({ ...formData, hostname: e.target.value })}
              className="input mt-1"
              placeholder="server-01"
            />
          </div>
          <div>
            <label className="label">Criticality</label>
            <select
              value={formData.criticality}
              onChange={(e) => setFormData({ ...formData, criticality: e.target.value })}
              className="input mt-1"
            >
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
              <option value="info">Info</option>
            </select>
          </div>
          <div className="flex justify-end gap-3 pt-4">
            <button type="button" onClick={onClose} className="btn btn-secondary btn-md">
              Cancel
            </button>
            <button
              type="submit"
              disabled={createMutation.isPending}
              className="btn btn-primary btn-md"
            >
              {createMutation.isPending ? 'Creating...' : 'Create Asset'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
