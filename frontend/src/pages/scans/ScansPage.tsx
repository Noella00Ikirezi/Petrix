import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Plus, Search, Scan, Play, Square, Trash2, Clock,
  CheckCircle, XCircle, Loader2, ChevronDown, ChevronUp,
  Globe, Shield, AlertTriangle, Info,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { scansApi } from '@/api/client';

export default function ScansPage() {
  const [search, setSearch] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['scans'],
    queryFn: () => scansApi.list(),
    refetchInterval: 5000,
  });

  const startMutation = useMutation({
    mutationFn: scansApi.start,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['scans'] }); toast.success('Scan démarré'); },
    onError: () => toast.error('Échec du démarrage'),
  });

  const cancelMutation = useMutation({
    mutationFn: scansApi.cancel,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['scans'] }); toast.success('Scan annulé'); },
    onError: () => toast.error('Échec de l\'annulation'),
  });

  const deleteMutation = useMutation({
    mutationFn: scansApi.delete,
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['scans'] }); toast.success('Scan supprimé'); },
    onError: () => toast.error('Échec de la suppression'),
  });

  const scans = data?.items || [];
  const filtered = scans.filter((s: ScanItem) =>
    s.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Scans réseau</h1>
          <p className="text-gray-600 dark:text-gray-400">
            Découverte d'hôtes, scan de ports et détection de vulnérabilités
          </p>
        </div>
        <button onClick={() => setShowCreateModal(true)} className="btn btn-primary btn-md">
          <Plus className="mr-2 h-4 w-4" /> Nouveau scan
        </button>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
        <input
          type="text"
          placeholder="Rechercher un scan..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="input pl-10"
        />
      </div>

      <div className="space-y-4">
        {isLoading ? (
          <div className="flex h-64 items-center justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-500 border-t-transparent" />
          </div>
        ) : filtered.length === 0 ? (
          <div className="card flex h-64 flex-col items-center justify-center text-gray-500">
            <Scan className="mb-2 h-12 w-12" />
            <p>Aucun scan — lancez votre premier audit réseau</p>
            <button onClick={() => setShowCreateModal(true)} className="btn btn-primary btn-sm mt-4">
              Créer un scan
            </button>
          </div>
        ) : (
          filtered.map((scan: ScanItem) => (
            <ScanCard
              key={scan.id}
              scan={scan}
              onStart={() => startMutation.mutate(scan.id)}
              onCancel={() => cancelMutation.mutate(scan.id)}
              onDelete={() => deleteMutation.mutate(scan.id)}
            />
          ))
        )}
      </div>

      {showCreateModal && <CreateScanModal onClose={() => setShowCreateModal(false)} />}
    </div>
  );
}

interface ScanItem {
  id: string;
  name: string;
  scan_type: string;
  status: string;
  progress: number;
  grade: string | null;
  score: number | null;
  findings_summary: { critical: number; high: number; medium: number; low: number; info: number };
  current_phase: string | null;
  error_message: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  duration_seconds: number | null;
}

function ScanCard({ scan, onStart, onCancel, onDelete }: {
  scan: ScanItem;
  onStart: () => void;
  onCancel: () => void;
  onDelete: () => void;
}) {
  const [showFindings, setShowFindings] = useState(false);
  const isRunning = scan.status === 'running';
  const isPending = scan.status === 'pending';
  const isCompleted = scan.status === 'completed';
  const isFailed = scan.status === 'failed';

  const { data: findingsData, isLoading: findingsLoading } = useQuery({
    queryKey: ['scan-findings', scan.id],
    queryFn: () => scansApi.findings(scan.id),
    enabled: showFindings && (isCompleted || isRunning),
  });

  const totalFindings = isCompleted
    ? Object.values(scan.findings_summary || {}).reduce((a, b) => a + b, 0)
    : 0;

  return (
    <div className="card">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-4">
          <div className={`rounded-lg p-3 ${
            isCompleted ? 'bg-green-100 text-green-600 dark:bg-green-900 dark:text-green-400'
            : isRunning ? 'bg-blue-100 text-blue-600 dark:bg-blue-900 dark:text-blue-400'
            : isFailed ? 'bg-red-100 text-red-600 dark:bg-red-900 dark:text-red-400'
            : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
          }`}>
            {isRunning ? <Loader2 className="h-6 w-6 animate-spin" />
              : isCompleted ? <CheckCircle className="h-6 w-6" />
              : isFailed ? <XCircle className="h-6 w-6" />
              : <Clock className="h-6 w-6" />}
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 dark:text-white">{scan.name}</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Type: <span className="capitalize">{scan.scan_type}</span>
              {' · '}Créé le {new Date(scan.created_at).toLocaleString('fr')}
              {scan.duration_seconds && ` · Durée: ${Math.round(scan.duration_seconds)}s`}
            </p>
            {isRunning && scan.current_phase && (
              <p className="mt-1 text-sm font-medium text-blue-600 dark:text-blue-400">
                Phase en cours : {scan.current_phase}
              </p>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          {scan.grade && <GradeBadge grade={scan.grade} />}
          <StatusBadge status={scan.status} />
          {isPending && (
            <button onClick={onStart} className="btn btn-primary btn-sm" title="Démarrer">
              <Play className="h-4 w-4" />
            </button>
          )}
          {isRunning && (
            <button onClick={onCancel} className="btn btn-secondary btn-sm" title="Annuler">
              <Square className="h-4 w-4" />
            </button>
          )}
          {!isRunning && (
            <button
              onClick={onDelete}
              className="btn btn-secondary btn-sm text-red-600 hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-900/20"
              title="Supprimer"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>

      {/* Progress bar */}
      {isRunning && (
        <div className="mt-4">
          <div className="mb-1 flex justify-between text-sm">
            <span className="text-gray-600 dark:text-gray-400">Progression</span>
            <span className="font-medium text-gray-900 dark:text-white">{scan.progress}%</span>
          </div>
          <div className="h-2 w-full rounded-full bg-gray-200 dark:bg-gray-700">
            <div
              className="h-2 rounded-full bg-primary-600 transition-all duration-500"
              style={{ width: `${scan.progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Summary + findings toggle */}
      {isCompleted && (
        <div className="mt-4 border-t border-gray-100 pt-4 dark:border-gray-700">
          <div className="flex items-center justify-between">
            <div className="flex gap-4">
              <FindingCount label="Critique" count={scan.findings_summary?.critical ?? 0} color="red" />
              <FindingCount label="Élevé" count={scan.findings_summary?.high ?? 0} color="orange" />
              <FindingCount label="Moyen" count={scan.findings_summary?.medium ?? 0} color="yellow" />
              <FindingCount label="Faible" count={scan.findings_summary?.low ?? 0} color="green" />
              {(scan.findings_summary?.info ?? 0) > 0 && (
                <FindingCount label="Info" count={scan.findings_summary.info} color="gray" />
              )}
            </div>
            <button
              onClick={() => setShowFindings(!showFindings)}
              className="flex items-center gap-1 text-sm text-primary-600 hover:text-primary-700 dark:text-primary-400"
            >
              {showFindings ? 'Masquer' : totalFindings > 0 ? 'Voir les détails' : 'Voir les hôtes'}
              {showFindings ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </button>
          </div>

          {/* Findings detail panel */}
          {showFindings && (
            <div className="mt-4">
              {findingsLoading ? (
                <div className="flex items-center gap-2 text-sm text-gray-500">
                  <Loader2 className="h-4 w-4 animate-spin" /> Chargement des résultats...
                </div>
              ) : (
                <FindingsPanel data={findingsData} />
              )}
            </div>
          )}
        </div>
      )}

      {/* Agent scan running — partial results */}
      {isRunning && scan.current_phase === 'agent_scanning' && (
        <div className="mt-4 border-t border-gray-100 pt-4 dark:border-gray-700">
          <button
            onClick={() => setShowFindings(!showFindings)}
            className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700 dark:text-blue-400"
          >
            {showFindings ? 'Masquer' : 'Résultats partiels disponibles'}
            {showFindings ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </button>
          {showFindings && (
            <div className="mt-4">
              {findingsLoading ? (
                <div className="flex items-center gap-2 text-sm text-gray-500">
                  <Loader2 className="h-4 w-4 animate-spin" /> Chargement...
                </div>
              ) : (
                <FindingsPanel data={findingsData} />
              )}
            </div>
          )}
        </div>
      )}

      {/* Error */}
      {isFailed && (scan.error_message || scan.current_phase) && (
        <div className="mt-3 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700 dark:bg-red-900/20 dark:text-red-400">
          {scan.error_message || scan.current_phase}
        </div>
      )}
    </div>
  );
}

function FindingsPanel({ data }: { data: { hosts: HostResult[]; findings: Finding[] } | undefined }) {
  if (!data) return <p className="text-sm text-gray-500">Aucun résultat disponible</p>;

  const { hosts = [], findings = [] } = data;

  const bySeverity = (sev: string) => findings.filter((f) => f.severity === sev);
  const criticalFindings = bySeverity('critical');
  const highFindings = bySeverity('high');
  const otherFindings = findings.filter((f) => !['critical', 'high'].includes(f.severity));

  return (
    <div className="space-y-4">
      {/* Discovered hosts */}
      {hosts.length > 0 && (
        <div>
          <h4 className="mb-2 flex items-center gap-2 text-sm font-semibold text-gray-700 dark:text-gray-300">
            <Globe className="h-4 w-4" /> {hosts.length} hôte(s) découvert(s)
          </h4>
          <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
            {hosts.map((host, i) => (
              <div key={i} className="rounded-md border border-gray-200 bg-gray-50 p-3 dark:border-gray-700 dark:bg-gray-800">
                <p className="font-mono text-sm font-medium text-gray-900 dark:text-white">
                  {host.ip}
                  {host.hostname && <span className="ml-2 font-normal text-gray-500">({host.hostname})</span>}
                </p>
                {host.os && <p className="text-xs text-gray-500">OS: {host.os}</p>}
                {host.open_ports && host.open_ports.length > 0 && (
                  <div className="mt-2 space-y-1">
                    {host.open_ports.map((p, j) => (
                      <div key={j} className="text-xs">
                        <div className="flex flex-wrap items-center gap-1">
                          <span className={`rounded px-1.5 py-0.5 font-mono font-medium ${
                            p.severity === 'critical' ? 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300'
                            : p.severity === 'high' ? 'bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300'
                            : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
                          }`}>
                            {p.port}/{p.protocol}
                          </span>
                          <span className="text-gray-600 dark:text-gray-400">{p.service}</span>
                          {p.product && <span className="text-gray-400">{p.product}</span>}
                          {p.http_title && <span className="italic text-blue-600 dark:text-blue-400">"{p.http_title}"</span>}
                          {p.ssl_subject && <span className="text-green-600 dark:text-green-400">🔒 {p.ssl_subject}</span>}
                        </div>
                        {p.banner && <p className="ml-1 font-mono text-gray-400">↳ {p.banner}</p>}
                        {p.ssh_keys && p.ssh_keys.length > 0 && (
                          <p className="ml-1 text-purple-600 dark:text-purple-400">↳ SSH keys: {p.ssh_keys.map(k => k.type).join(', ')}</p>
                        )}
                        {p.extra && p.extra.map((e, k) => (
                          <p key={k} className="ml-1 text-red-500">⚠ {e}</p>
                        ))}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Critical & High findings */}
      {(criticalFindings.length > 0 || highFindings.length > 0) && (
        <div>
          <h4 className="mb-2 flex items-center gap-2 text-sm font-semibold text-red-700 dark:text-red-400">
            <AlertTriangle className="h-4 w-4" /> Findings critiques / élevés
          </h4>
          <div className="space-y-2">
            {[...criticalFindings, ...highFindings].map((f, i) => (
              <FindingRow key={i} finding={f} />
            ))}
          </div>
        </div>
      )}

      {/* Other findings */}
      {otherFindings.length > 0 && (
        <div>
          <h4 className="mb-2 flex items-center gap-2 text-sm font-semibold text-gray-700 dark:text-gray-300">
            <Info className="h-4 w-4" /> Autres findings ({otherFindings.length})
          </h4>
          <div className="space-y-2">
            {otherFindings.map((f, i) => (
              <FindingRow key={i} finding={f} />
            ))}
          </div>
        </div>
      )}

      {hosts.length === 0 && findings.length === 0 && (
        <p className="text-sm text-gray-500">Aucun hôte ou finding trouvé.</p>
      )}
    </div>
  );
}

interface HostResult {
  ip: string;
  hostname?: string;
  os?: string;
  open_ports: {
    port: number;
    protocol: string;
    service: string;
    product?: string;
    banner?: string;
    http_title?: string;
    http_headers?: Record<string, string>;
    ssl_subject?: string;
    ssl_expiry?: string;
    ssh_keys?: { type: string; key: string }[];
    extra?: string[];
    severity: string;
  }[];
}

interface Finding {
  host: string;
  severity: string;
  title: string;
  description?: string;
  cve?: string;
  cvss?: number;
  source?: string;
  hardening?: { check_id: string; label: string; module: string } | null;
}

function FindingRow({ finding }: { finding: Finding }) {
  const severityStyles: Record<string, string> = {
    critical: 'border-l-red-500 bg-red-50 dark:bg-red-900/10',
    high:     'border-l-orange-500 bg-orange-50 dark:bg-orange-900/10',
    medium:   'border-l-yellow-500 bg-yellow-50 dark:bg-yellow-900/10',
    low:      'border-l-green-500 bg-green-50 dark:bg-green-900/10',
    info:     'border-l-blue-500 bg-blue-50 dark:bg-blue-900/10',
  };
  const badgeStyles: Record<string, string> = {
    critical: 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300',
    high:     'bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300',
    medium:   'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300',
    low:      'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300',
    info:     'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300',
  };

  return (
    <div className={`rounded-md border-l-4 p-3 ${severityStyles[finding.severity] || ''}`}>
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className={`rounded px-1.5 py-0.5 text-xs font-medium uppercase ${badgeStyles[finding.severity] || ''}`}>
              {finding.severity}
            </span>
            {finding.cve && (
              <span className="font-mono text-xs text-gray-500">{finding.cve}</span>
            )}
          </div>
          <p className="mt-1 text-sm font-medium text-gray-900 dark:text-white">{finding.title}</p>
          {finding.description && (
            <p className="mt-0.5 text-xs text-gray-500 dark:text-gray-400">{finding.description}</p>
          )}
          {finding.hardening && (
            <p className="mt-1 flex items-center gap-1 text-xs text-amber-700 dark:text-amber-400">
              <Shield className="h-3 w-3" />
              Hardening : {finding.hardening.label}
            </p>
          )}
        </div>
        <span className="shrink-0 font-mono text-xs text-gray-400">{finding.host}</span>
      </div>
    </div>
  );
}

function FindingCount({ label, count, color }: {
  label: string; count: number; color: 'red' | 'orange' | 'yellow' | 'green' | 'gray';
}) {
  const colors = {
    red:    'text-red-600 dark:text-red-400',
    orange: 'text-orange-600 dark:text-orange-400',
    yellow: 'text-yellow-600 dark:text-yellow-400',
    green:  'text-green-600 dark:text-green-400',
    gray:   'text-gray-500 dark:text-gray-400',
  };
  return (
    <div className="text-center">
      <div className={`text-2xl font-bold ${colors[color]}`}>{count}</div>
      <div className="text-xs text-gray-500 dark:text-gray-400">{label}</div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    completed: 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300',
    running:   'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300',
    pending:   'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300',
    failed:    'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300',
    cancelled: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
  };
  const labels: Record<string, string> = {
    completed: 'Terminé', running: 'En cours', pending: 'En attente',
    failed: 'Échec', cancelled: 'Annulé',
  };
  return <span className={`badge ${styles[status] || ''}`}>{labels[status] || status}</span>;
}

function GradeBadge({ grade }: { grade: string | null }) {
  if (!grade) return null;
  const styles: Record<string, string> = {
    A: 'bg-green-500 text-white', B: 'bg-lime-500 text-white',
    C: 'bg-yellow-500 text-white', D: 'bg-orange-500 text-white', F: 'bg-red-500 text-white',
  };
  return <span className={`badge text-lg font-bold ${styles[grade] || ''}`}>{grade}</span>;
}

function CreateScanModal({ onClose }: { onClose: () => void }) {
  const [formData, setFormData] = useState({ name: '', scan_type: 'discovery', target: '' });
  const queryClient = useQueryClient();

  const createMutation = useMutation({
    mutationFn: scansApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scans'] });
      toast.success('Scan créé');
      onClose();
    },
    onError: () => toast.error('Échec de la création'),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const target = formData.target.trim();
    if (!target) {
      toast.error('Veuillez spécifier une cible (IP, subnet ou hostname)');
      return;
    }
    const type = target.includes('/') ? 'subnet'
      : /^\d{1,3}(\.\d{1,3}){3}$/.test(target) ? 'ip'
      : 'hostname';
    createMutation.mutate({
      name: formData.name,
      scan_type: formData.scan_type,
      targets: [{ type, value: target }],
    });
  };

  const target = formData.target.trim();
  const targetHint = target
    ? target.includes('/') ? 'Plage réseau (CIDR) — tous les hôtes actifs seront scannés'
      : /^\d{1,3}(\.\d{1,3}){3}$/.test(target) ? 'Adresse IP unique'
      : 'Hostname'
    : '';

  const scanTypeHint: Record<string, string> = {
    discovery:   'Découverte des hôtes actifs sur la cible (ping/ARP)',
    compliance:  'Découverte + scan de ports ouverts (sans détection CVE)',
    vulnerability: 'Découverte + ports + détection de CVEs',
    full:        'Audit complet : découverte, ports, CVEs et hardening SSH',
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl dark:bg-gray-800">
        <h2 className="mb-4 text-xl font-bold text-gray-900 dark:text-white">Nouveau scan réseau</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="label">Nom du scan</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="input mt-1"
              placeholder="Audit réseau – Juin 2026"
              required
            />
          </div>

          <div>
            <label className="label">Mode</label>
            <select
              value={formData.scan_type}
              onChange={(e) => setFormData({ ...formData, scan_type: e.target.value })}
              className="input mt-1"
            >
              <option value="discovery">Découverte — hôtes actifs</option>
              <option value="compliance">Scan de ports</option>
              <option value="vulnerability">Ports + CVEs</option>
              <option value="full">Audit complet</option>
            </select>
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
              {scanTypeHint[formData.scan_type]}
            </p>
          </div>

          <div>
            <label className="label">Cible à auditer</label>
            <input
              type="text"
              value={formData.target}
              onChange={(e) => setFormData({ ...formData, target: e.target.value })}
              className="input mt-1"
              placeholder="192.168.10.0/24 ou 192.168.10.50 ou serveur.local"
              required
            />
            {targetHint && (
              <p className="mt-1 text-xs text-primary-600 dark:text-primary-400">{targetHint}</p>
            )}
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose} className="btn btn-secondary btn-md">Annuler</button>
            <button type="submit" disabled={createMutation.isPending} className="btn btn-primary btn-md">
              {createMutation.isPending ? 'Création...' : 'Lancer le scan'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
