import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Plus, Search, Server, Trash2, Shield } from 'lucide-react';
import toast from 'react-hot-toast';
import { assetsApi, hardeningApi } from '@/api/client';

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
      toast.success('Asset supprimé');
    },
    onError: () => toast.error('Échec de la suppression'),
  });

  const assets = data?.items || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Actifs</h1>
          <p className="text-gray-600 dark:text-gray-400">Inventaire de votre parc IT</p>
        </div>
        <button onClick={() => setShowCreateModal(true)} className="btn btn-primary btn-md">
          <Plus className="mr-2 h-4 w-4" />
          Ajouter un actif
        </button>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
        <input
          type="text"
          placeholder="Rechercher un actif..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="input pl-10"
        />
      </div>

      <div className="card overflow-hidden p-0">
        {isLoading ? (
          <div className="flex h-64 items-center justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-500 border-t-transparent" />
          </div>
        ) : assets.length === 0 ? (
          <div className="flex h-64 flex-col items-center justify-center text-gray-500">
            <Server className="mb-2 h-12 w-12" />
            <p>Aucun actif — commencez par en ajouter un</p>
            <button onClick={() => setShowCreateModal(true)} className="btn btn-primary btn-sm mt-4">
              Ajouter un actif
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">Nom</th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">Type</th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">IP / Hostname</th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">Statut</th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">Criticité</th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">Vulns</th>
                  <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 bg-white dark:divide-gray-700 dark:bg-gray-800">
                {assets.map((asset: Asset) => (
                  <tr key={asset.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                    <td className="whitespace-nowrap px-6 py-4">
                      <div className="flex items-center">
                        <Server className="mr-3 h-5 w-5 text-gray-400" />
                        <div>
                          <div className="font-medium text-gray-900 dark:text-white">{asset.name}</div>
                          <div className="text-sm text-gray-500 dark:text-gray-400">{asset.fqdn || '-'}</div>
                        </div>
                      </div>
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-900 dark:text-white">{asset.asset_type}</td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm font-mono text-gray-900 dark:text-white">
                      {asset.ip_address || asset.hostname || '-'}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4"><StatusBadge status={asset.status} /></td>
                    <td className="whitespace-nowrap px-6 py-4"><CriticalityBadge criticality={asset.criticality} /></td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-900 dark:text-white">{asset.vulnerability_count}</td>
                    <td className="whitespace-nowrap px-6 py-4 text-right">
                      <button
                        onClick={() => {
                          if (confirm('Supprimer cet actif ?')) deleteMutation.mutate(asset.id);
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
  const labels: Record<string, string> = { active: 'Actif', inactive: 'Inactif', maintenance: 'Maintenance', decommissioned: 'Déclassé' };
  return <span className={`badge ${styles[status] || ''}`}>{labels[status] || status}</span>;
}

function CriticalityBadge({ criticality }: { criticality: string }) {
  const styles: Record<string, string> = {
    critical: 'badge-critical', high: 'badge-high', medium: 'badge-medium', low: 'badge-low', info: 'badge-info',
  };
  const labels: Record<string, string> = { critical: 'Critique', high: 'Élevé', medium: 'Moyen', low: 'Faible', info: 'Info' };
  return <span className={`badge ${styles[criticality] || ''}`}>{labels[criticality] || criticality}</span>;
}

const OS_BY_TYPE: Record<string, string> = {
  server: 'linux', workstation: 'windows', network: 'other',
  cloud_instance: 'linux', container: 'linux', database: 'linux',
  application: 'other', iot: 'other', other: 'other',
};

function CreateAssetModal({ onClose }: { onClose: () => void }) {
  const [formData, setFormData] = useState({
    name: '',
    asset_type: 'server',
    ip_address: '',
    hostname: '',
    criticality: 'medium',
  });
  const [createHardening, setCreateHardening] = useState(false);
  const [sshUser, setSshUser] = useState('root');
  const [sshPort, setSshPort] = useState('22');
  const queryClient = useQueryClient();

  const createMutation = useMutation({
    mutationFn: async (data: typeof formData) => {
      const asset = await assetsApi.create(data);
      if (createHardening && (data.ip_address || data.hostname)) {
        try {
          await hardeningApi.createTarget({
            name: data.name,
            host: data.ip_address || data.hostname,
            port: parseInt(sshPort) || 22,
            username: sshUser || 'root',
            os_type: OS_BY_TYPE[data.asset_type] || 'linux',
            description: `Créé depuis l'actif "${data.name}"`,
          });
        } catch {
          // Don't fail asset creation if hardening target fails
          toast('Actif créé — la cible hardening a échoué (vérifiez l\'IP)', { icon: '⚠️' });
        }
      }
      return asset;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assets'] });
      toast.success(createHardening ? 'Actif créé + cible hardening ajoutée' : 'Actif créé');
      onClose();
    },
    onError: () => toast.error('Échec de la création'),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate(formData);
  };

  const needsHardeningFields = createHardening && (formData.ip_address || formData.hostname);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-lg bg-white p-6 dark:bg-gray-800 max-h-[90vh] overflow-y-auto">
        <h2 className="mb-4 text-xl font-bold text-gray-900 dark:text-white">Ajouter un actif</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="label">Nom *</label>
            <input type="text" value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="input mt-1" placeholder="Serveur-01" required />
          </div>
          <div>
            <label className="label">Type</label>
            <select value={formData.asset_type}
              onChange={(e) => setFormData({ ...formData, asset_type: e.target.value })}
              className="input mt-1">
              <option value="server">Serveur</option>
              <option value="workstation">Poste de travail</option>
              <option value="network">Équipement réseau</option>
              <option value="cloud_instance">Instance cloud</option>
              <option value="container">Conteneur</option>
              <option value="database">Base de données</option>
              <option value="application">Application</option>
              <option value="iot">IoT</option>
              <option value="other">Autre</option>
            </select>
          </div>
          <div>
            <label className="label">Adresse IP</label>
            <input type="text" value={formData.ip_address}
              onChange={(e) => setFormData({ ...formData, ip_address: e.target.value })}
              className="input mt-1" placeholder="192.168.1.10" />
          </div>
          <div>
            <label className="label">Hostname</label>
            <input type="text" value={formData.hostname}
              onChange={(e) => setFormData({ ...formData, hostname: e.target.value })}
              className="input mt-1" placeholder="serveur-01.local" />
          </div>
          <div>
            <label className="label">Criticité</label>
            <select value={formData.criticality}
              onChange={(e) => setFormData({ ...formData, criticality: e.target.value })}
              className="input mt-1">
              <option value="critical">Critique</option>
              <option value="high">Élevée</option>
              <option value="medium">Moyenne</option>
              <option value="low">Faible</option>
              <option value="info">Info</option>
            </select>
          </div>

          {/* Hardening option */}
          <div className="rounded-lg border border-gray-200 p-4 dark:border-gray-700">
            <label className="flex cursor-pointer items-center gap-3">
              <input type="checkbox" checked={createHardening}
                onChange={(e) => setCreateHardening(e.target.checked)}
                className="h-4 w-4 accent-primary-600" />
              <div className="flex items-center gap-2">
                <Shield className="h-4 w-4 text-purple-600" />
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  Créer une cible hardening (audit SSH)
                </span>
              </div>
            </label>
            {needsHardeningFields && (
              <div className="mt-3 grid grid-cols-2 gap-3">
                <div>
                  <label className="label text-xs">Utilisateur SSH</label>
                  <input type="text" value={sshUser} onChange={(e) => setSshUser(e.target.value)}
                    className="input mt-1 text-sm" placeholder="root" />
                </div>
                <div>
                  <label className="label text-xs">Port SSH</label>
                  <input type="number" value={sshPort} onChange={(e) => setSshPort(e.target.value)}
                    className="input mt-1 text-sm" placeholder="22" />
                </div>
              </div>
            )}
            {createHardening && !formData.ip_address && !formData.hostname && (
              <p className="mt-2 text-xs text-amber-600">Une IP ou un hostname est requis pour le hardening.</p>
            )}
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="btn btn-secondary btn-md">Annuler</button>
            <button type="submit" disabled={createMutation.isPending} className="btn btn-primary btn-md">
              {createMutation.isPending ? 'Création...' : 'Créer'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
