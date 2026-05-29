import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ShieldCheck,
  Server,
  Play,
  Trash2,
  Loader2,
  CheckCircle,
  XCircle,
  Clock,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Plus,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { hardeningApi } from '@/api/client';

type Target = {
  id: string;
  name: string;
  host: string;
  port: number;
  username: string;
  os_type: string;
  description?: string;
  tags?: string[];
  created_at: string;
};

type Session = {
  id: string;
  target_id: string;
  target_name: string;
  target_host: string;
  status: string;
  current_module?: string;
  progress: number;
  score?: number;
  grade?: string;
  findings_summary?: Record<string, number>;
  total_findings: number;
  total_checks: number;
  passed_checks: number;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  duration_seconds?: number;
};

type Finding = {
  id: string;
  check_id: string;
  check_name: string;
  module: string;
  description: string;
  severity: string;
  found: string;
  expected: string;
  remediation?: string;
  status: string;
};

const SEVERITY_COLORS: Record<string, string> = {
  CRITICAL: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
  HIGH: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400',
  MEDIUM: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
  LOW: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
  INFO: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
};

const GRADE_COLORS: Record<string, string> = {
  A: 'text-green-600 dark:text-green-400',
  B: 'text-lime-600 dark:text-lime-400',
  C: 'text-yellow-600 dark:text-yellow-400',
  D: 'text-orange-600 dark:text-orange-400',
  F: 'text-red-600 dark:text-red-400',
};

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { icon: React.ReactNode; cls: string }> = {
    pending: { icon: <Clock className="h-3 w-3" />, cls: 'text-gray-500' },
    connecting: { icon: <Loader2 className="h-3 w-3 animate-spin" />, cls: 'text-blue-500' },
    auditing: { icon: <Loader2 className="h-3 w-3 animate-spin" />, cls: 'text-blue-500' },
    completed: { icon: <CheckCircle className="h-3 w-3" />, cls: 'text-green-500' },
    failed: { icon: <XCircle className="h-3 w-3" />, cls: 'text-red-500' },
  };
  const { icon, cls } = map[status] ?? { icon: null, cls: '' };
  return (
    <span className={`flex items-center gap-1 text-xs font-medium capitalize ${cls}`}>
      {icon}
      {status}
    </span>
  );
}

function TargetModal({ onClose, onCreated }: { onClose: () => void; onCreated: () => void }) {
  const [form, setForm] = useState({
    name: '', host: '', port: 22, username: 'root',
    os_type: 'linux', password: '', description: '',
  });

  const createTarget = useMutation({
    mutationFn: () => hardeningApi.createTarget({
      name: form.name,
      host: form.host,
      port: form.port,
      username: form.username,
      os_type: form.os_type,
      password: form.password || undefined,
      description: form.description || undefined,
    }),
    onSuccess: () => {
      toast.success('Target created');
      onCreated();
      onClose();
    },
    onError: () => toast.error('Failed to create target'),
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl dark:bg-gray-800">
        <h2 className="mb-4 text-lg font-semibold dark:text-white">Add Hardening Target</h2>
        <div className="space-y-3">
          <input className="input w-full" placeholder="Name *" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} />
          <input className="input w-full" placeholder="Host / IP *" value={form.host} onChange={e => setForm(f => ({ ...f, host: e.target.value }))} />
          <div className="flex gap-2">
            <input className="input w-20" type="number" placeholder="Port" value={form.port} onChange={e => setForm(f => ({ ...f, port: parseInt(e.target.value) || 22 }))} />
            <input className="input flex-1" placeholder="Username" value={form.username} onChange={e => setForm(f => ({ ...f, username: e.target.value }))} />
          </div>
          <input className="input w-full" type="password" placeholder="SSH Password (leave empty if key auth)" value={form.password} onChange={e => setForm(f => ({ ...f, password: e.target.value }))} />
          <select className="input w-full" value={form.os_type} onChange={e => setForm(f => ({ ...f, os_type: e.target.value }))}>
            <option value="linux">Linux</option>
            <option value="macos_intel" disabled>macOS Intel (coming soon)</option>
            <option value="windows_server" disabled>Windows Server (coming soon)</option>
          </select>
          <input className="input w-full" placeholder="Description (optional)" value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} />
        </div>
        <div className="mt-5 flex justify-end gap-2">
          <button className="btn btn-secondary btn-sm" onClick={onClose}>Cancel</button>
          <button
            className="btn btn-primary btn-sm"
            disabled={!form.name || !form.host || createTarget.isPending}
            onClick={() => createTarget.mutate()}
          >
            {createTarget.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Create'}
          </button>
        </div>
      </div>
    </div>
  );
}

function SessionModal({
  targets,
  onClose,
  onCreated,
}: {
  targets: Target[];
  onClose: () => void;
  onCreated: () => void;
}) {
  const [targetId, setTargetId] = useState(targets[0]?.id ?? '');
  const [modules, setModules] = useState<string[]>(['ssh', 'users', 'kernel', 'firewall', 'services']);

  const createSession = useMutation({
    mutationFn: () => hardeningApi.createSession({ target_id: targetId, modules }),
    onSuccess: () => {
      toast.success('Audit session launched');
      onCreated();
      onClose();
    },
    onError: () => toast.error('Failed to launch audit'),
  });

  const allModules = [
    { id: 'ssh', label: 'SSH Configuration' },
    { id: 'users', label: 'User Accounts' },
    { id: 'kernel', label: 'Kernel Parameters' },
    { id: 'firewall', label: 'Firewall' },
    { id: 'services', label: 'Services' },
  ];

  const toggle = (id: string) =>
    setModules(prev => prev.includes(id) ? prev.filter(m => m !== id) : [...prev, id]);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl dark:bg-gray-800">
        <h2 className="mb-4 text-lg font-semibold dark:text-white">Launch Hardening Audit</h2>
        {targets.length === 0 ? (
          <p className="text-sm text-gray-500">No targets yet — add a target first.</p>
        ) : (
          <div className="space-y-4">
            <div>
              <label className="mb-1 block text-sm font-medium dark:text-gray-300">Target</label>
              <select className="input w-full" value={targetId} onChange={e => setTargetId(e.target.value)}>
                {targets.map(t => (
                  <option key={t.id} value={t.id}>{t.name} ({t.host})</option>
                ))}
              </select>
            </div>
            <div>
              <label className="mb-2 block text-sm font-medium dark:text-gray-300">Modules</label>
              <div className="space-y-2">
                {allModules.map(m => (
                  <label key={m.id} className="flex cursor-pointer items-center gap-2">
                    <input
                      type="checkbox"
                      checked={modules.includes(m.id)}
                      onChange={() => toggle(m.id)}
                      className="rounded"
                    />
                    <span className="text-sm dark:text-gray-300">{m.label}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>
        )}
        <div className="mt-5 flex justify-end gap-2">
          <button className="btn btn-secondary btn-sm" onClick={onClose}>Cancel</button>
          {targets.length > 0 && (
            <button
              className="btn btn-primary btn-sm"
              disabled={modules.length === 0 || createSession.isPending}
              onClick={() => createSession.mutate()}
            >
              {createSession.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : 'Launch Audit'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

function SessionCard({ session }: { session: Session }) {
  const [expanded, setExpanded] = useState(false);
  const { data: findings } = useQuery<Finding[]>({
    queryKey: ['hardening-findings', session.id],
    queryFn: () => hardeningApi.getFindings(session.id),
    enabled: expanded && session.status === 'completed',
  });

  const summary = session.findings_summary ?? {};

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="font-medium dark:text-white">{session.target_name}</span>
            <StatusBadge status={session.status} />
            {session.grade && (
              <span className={`text-xl font-bold ${GRADE_COLORS[session.grade] ?? ''}`}>
                {session.grade}
              </span>
            )}
          </div>
          <p className="text-sm text-gray-500">{session.target_host}</p>
          {session.status === 'auditing' && (
            <div className="mt-2 space-y-1">
              <div className="flex justify-between text-xs text-gray-500">
                <span>{session.current_module ?? 'running…'}</span>
                <span>{session.progress}%</span>
              </div>
              <div className="h-1.5 w-full rounded-full bg-gray-200 dark:bg-gray-700">
                <div
                  className="h-1.5 rounded-full bg-primary-500 transition-all"
                  style={{ width: `${session.progress}%` }}
                />
              </div>
            </div>
          )}
          {session.status === 'completed' && (
            <div className="mt-2 flex flex-wrap gap-2">
              {session.score !== undefined && (
                <span className="text-sm font-medium dark:text-gray-300">
                  Score: <strong>{session.score}/100</strong>
                </span>
              )}
              {Object.entries(summary).map(([sev, count]) =>
                count > 0 ? (
                  <span key={sev} className={`rounded px-2 py-0.5 text-xs font-medium ${SEVERITY_COLORS[sev] ?? ''}`}>
                    {count} {sev}
                  </span>
                ) : null
              )}
              <span className="text-xs text-gray-400">
                {session.passed_checks}/{session.total_checks} checks passed
              </span>
            </div>
          )}
          {session.status === 'failed' && session.error_message && (
            <p className="mt-1 text-xs text-red-500">{session.error_message}</p>
          )}
        </div>
        {session.status === 'completed' && (
          <button
            onClick={() => setExpanded(e => !e)}
            className="flex items-center gap-1 text-xs text-primary-600 hover:underline dark:text-primary-400"
          >
            {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            Findings
          </button>
        )}
      </div>

      {expanded && findings && findings.length > 0 && (
        <div className="mt-4 space-y-2 border-t border-gray-100 pt-4 dark:border-gray-700">
          {findings.map(f => (
            <div key={f.id} className="rounded-md border border-gray-100 p-3 dark:border-gray-700">
              <div className="flex items-start justify-between gap-2">
                <div className="space-y-0.5">
                  <div className="flex items-center gap-2">
                    <span className={`rounded px-1.5 py-0.5 text-xs font-bold ${SEVERITY_COLORS[f.severity] ?? ''}`}>
                      {f.severity}
                    </span>
                    <span className="text-xs font-mono text-gray-500">{f.check_id}</span>
                    <span className="text-xs font-medium dark:text-gray-300">{f.check_name}</span>
                  </div>
                  <p className="text-xs text-gray-600 dark:text-gray-400">{f.description}</p>
                  <p className="text-xs text-gray-500">
                    Found: <code className="rounded bg-gray-100 px-1 dark:bg-gray-700">{f.found}</code>
                    {' → '}Expected: <code className="rounded bg-gray-100 px-1 dark:bg-gray-700">{f.expected}</code>
                  </p>
                  {f.remediation && (
                    <details className="mt-1">
                      <summary className="cursor-pointer text-xs text-primary-600 dark:text-primary-400">
                        Remediation
                      </summary>
                      <pre className="mt-1 overflow-auto rounded bg-gray-50 p-2 text-xs dark:bg-gray-900">{f.remediation}</pre>
                    </details>
                  )}
                </div>
                <span className="shrink-0 rounded px-1.5 py-0.5 text-xs text-gray-400 dark:bg-gray-700">
                  {f.module}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
      {expanded && findings && findings.length === 0 && (
        <div className="mt-4 flex items-center gap-2 border-t border-gray-100 pt-4 text-sm text-green-600 dark:border-gray-700 dark:text-green-400">
          <CheckCircle className="h-4 w-4" />
          No findings — all checks passed!
        </div>
      )}
    </div>
  );
}

export default function HardeningPage() {
  const [tab, setTab] = useState<'sessions' | 'targets'>('sessions');
  const [showTargetModal, setShowTargetModal] = useState(false);
  const [showSessionModal, setShowSessionModal] = useState(false);
  const queryClient = useQueryClient();

  const { data: targets = [], isLoading: loadingTargets } = useQuery<Target[]>({
    queryKey: ['hardening-targets'],
    queryFn: hardeningApi.listTargets,
  });

  const { data: sessions = [], isLoading: loadingSessions } = useQuery<Session[]>({
    queryKey: ['hardening-sessions'],
    queryFn: hardeningApi.listSessions,
    refetchInterval: (query) => {
      const data = query.state.data as Session[] | undefined;
      const hasActive = data?.some(s => ['pending', 'connecting', 'auditing'].includes(s.status));
      return hasActive ? 3000 : false;
    },
  });

  const deleteTarget = useMutation({
    mutationFn: hardeningApi.deleteTarget,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['hardening-targets'] });
      toast.success('Target deleted');
    },
  });

  const refresh = () => {
    queryClient.invalidateQueries({ queryKey: ['hardening-targets'] });
    queryClient.invalidateQueries({ queryKey: ['hardening-sessions'] });
  };

  const completedSessions = sessions.filter(s => s.status === 'completed');
  const avgScore =
    completedSessions.length > 0
      ? Math.round(completedSessions.reduce((acc, s) => acc + (s.score ?? 0), 0) / completedSessions.length)
      : null;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Hardening (HCO)
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            SSH-based security hardening audits — CIS Benchmark compliance checks
          </p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => setShowTargetModal(true)} className="btn btn-secondary btn-md">
            <Plus className="mr-2 h-4 w-4" />
            Add Target
          </button>
          <button onClick={() => setShowSessionModal(true)} className="btn btn-primary btn-md">
            <Play className="mr-2 h-4 w-4" />
            Launch Audit
          </button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div className="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
          <p className="text-sm text-gray-500">Targets</p>
          <p className="text-2xl font-bold dark:text-white">{targets.length}</p>
        </div>
        <div className="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
          <p className="text-sm text-gray-500">Audits Run</p>
          <p className="text-2xl font-bold dark:text-white">{completedSessions.length}</p>
        </div>
        <div className="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
          <p className="text-sm text-gray-500">Avg Score</p>
          <p className="text-2xl font-bold dark:text-white">{avgScore !== null ? `${avgScore}/100` : '—'}</p>
        </div>
        <div className="rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
          <p className="text-sm text-gray-500">Total Findings</p>
          <p className="text-2xl font-bold dark:text-white">
            {sessions.reduce((acc, s) => acc + s.total_findings, 0)}
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-4 border-b border-gray-200 dark:border-gray-700">
        {(['sessions', 'targets'] as const).map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`pb-3 text-sm font-medium capitalize transition-colors ${
              tab === t
                ? 'border-b-2 border-primary-600 text-primary-600'
                : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300'
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {/* Sessions Tab */}
      {tab === 'sessions' && (
        <div className="space-y-3">
          {loadingSessions ? (
            <div className="flex justify-center py-12">
              <Loader2 className="h-6 w-6 animate-spin text-primary-500" />
            </div>
          ) : sessions.length === 0 ? (
            <div className="flex flex-col items-center gap-3 py-16 text-gray-400">
              <ShieldCheck className="h-12 w-12 opacity-30" />
              <p>No audits yet — launch your first hardening audit.</p>
            </div>
          ) : (
            sessions.map(s => <SessionCard key={s.id} session={s} />)
          )}
        </div>
      )}

      {/* Targets Tab */}
      {tab === 'targets' && (
        <div className="space-y-3">
          {loadingTargets ? (
            <div className="flex justify-center py-12">
              <Loader2 className="h-6 w-6 animate-spin text-primary-500" />
            </div>
          ) : targets.length === 0 ? (
            <div className="flex flex-col items-center gap-3 py-16 text-gray-400">
              <Server className="h-12 w-12 opacity-30" />
              <p>No targets yet — add a server to audit.</p>
            </div>
          ) : (
            targets.map(t => (
              <div
                key={t.id}
                className="flex items-center justify-between rounded-lg border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800"
              >
                <div className="space-y-0.5">
                  <p className="font-medium dark:text-white">{t.name}</p>
                  <p className="text-sm text-gray-500">
                    {t.username}@{t.host}:{t.port} — {t.os_type}
                  </p>
                  {t.description && (
                    <p className="text-xs text-gray-400">{t.description}</p>
                  )}
                </div>
                <button
                  onClick={() => deleteTarget.mutate(t.id)}
                  className="text-gray-400 hover:text-red-500"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            ))
          )}
        </div>
      )}

      {showTargetModal && (
        <TargetModal onClose={() => setShowTargetModal(false)} onCreated={refresh} />
      )}
      {showSessionModal && (
        <SessionModal targets={targets} onClose={() => setShowSessionModal(false)} onCreated={refresh} />
      )}
    </div>
  );
}
