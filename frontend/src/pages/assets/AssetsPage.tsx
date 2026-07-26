/**
 * Page de gestion des systèmes audités (périmètre ANSSI-BP-028).
 * Permet d'ajouter des cibles, de télécharger l'agent d'audit adapté à l'OS,
 * d'importer les rapports XML et de consulter le score de conformité par système.
 */
import { useRef, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import {
  Server, Search, FileText, Trash2,
  CheckCircle, XCircle, Clock, AlertTriangle, Minus,
  Monitor, Globe, Shield, FileCode, Download, Terminal,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { hardeningApi } from '@/api/client';

// ─── Types ────────────────────────────────────────────────────────────────────

/** Résumé de la dernière session de durcissement rattachée à une cible. */
interface LatestSession {
  session_id: string;
  status: string;
  score: number | null;
  grade: string | null;
  completed_at: string | null;
  total_checks: number;
  passed_checks: number;
  total_findings: number;
  findings_summary: Record<string, number> | null;
}

/** Cible d'audit (système) avec son historique de sessions et ses métadonnées OS. */
interface Target {
  id: string;
  name: string;
  host: string;
  port: number;
  username: string;
  os_type: string;
  description: string | null;
  tags: string[];
  created_at: string;
  latest_session: LatestSession | null;
  session_count: number;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

const OS_ICONS: Record<string, typeof Monitor> = {
  linux:          Server,
  macos:          Monitor,
  macos_intel:    Monitor,
  macos_silicon:  Monitor,
  windows:        Globe,
};

const OS_LABELS: Record<string, string> = {
  linux:          'Linux',
  macos:          'macOS',
  macos_intel:    'macOS (Intel)',
  macos_silicon:  'macOS (Silicon)',
  windows:        'Windows',
};

// OS type → agent-script OS param mapping
const OS_AGENT: Record<string, string> = {
  linux:          'linux',
  macos:          'macos',
  macos_intel:    'macos',
  macos_silicon:  'macos',
  windows:        'windows',
};

const GRADE_CONFIG: Record<string, { bg: string; text: string; border: string }> = {
  A: { bg: 'bg-green-100',  text: 'text-green-700',  border: 'border-green-300' },
  B: { bg: 'bg-lime-100',   text: 'text-lime-700',   border: 'border-lime-300' },
  C: { bg: 'bg-yellow-100', text: 'text-yellow-700', border: 'border-yellow-300' },
  D: { bg: 'bg-orange-100', text: 'text-orange-700', border: 'border-orange-300' },
  E: { bg: 'bg-red-100',    text: 'text-red-600',    border: 'border-red-300' },
  F: { bg: 'bg-red-200',    text: 'text-red-800',    border: 'border-red-400' },
};

const SCORE_COLOR = (score: number) => {
  if (score >= 80) return 'text-green-600';
  if (score >= 60) return 'text-yellow-600';
  if (score >= 40) return 'text-orange-500';
  return 'text-red-600';
};

/**
 * Renvoie un badge JSX indiquant l'état de la dernière session de la cible.
 * @param s - Dernière session ou null si jamais auditée.
 */
function statusBadge(s: LatestSession | null) {
  if (!s) return (
    <span className="flex items-center gap-1 text-xs text-gray-400">
      <Minus className="h-3.5 w-3.5" /> Jamais audité
    </span>
  );
  if (s.status === 'failed') return (
    <span className="flex items-center gap-1 text-xs text-red-500">
      <XCircle className="h-3.5 w-3.5" /> Échec
    </span>
  );
  if (s.status === 'completed') return (
    <span className="flex items-center gap-1 text-xs text-green-600 dark:text-green-400">
      <CheckCircle className="h-3.5 w-3.5" /> Audité
    </span>
  );
  return (
    <span className="flex items-center gap-1 text-xs text-gray-500">
      <Clock className="h-3.5 w-3.5" /> {s.status}
    </span>
  );
}

function formatDate(iso: string | null) {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' });
}

// ─── Download Only Modal ──────────────────────────────────────────────────────

/**
 * Modale de téléchargement de l'agent d'audit.
 * Demande uniquement le choix d'OS et déclenche le téléchargement du script.
 * La création du système se fait automatiquement lors de l'import XML.
 * @param onClose - Callback de fermeture de la modale.
 */
function DownloadOnlyModal({ onClose }: { onClose: () => void }) {
  const [osType, setOsType] = useState('linux');
  const osAgent = OS_AGENT[osType] ?? 'linux';
  const isWindows = osAgent === 'windows';

  const handleDownload = () => {
    const url = `/api/v1/hardening/agent-script/${osAgent}`;
    const a = document.createElement('a');
    a.href = url;
    a.download = isWindows ? 'petrix_agent_windows.ps1' : `petrix_agent_${osAgent}.sh`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-xl dark:bg-gray-800">
        <h2 className="mb-5 text-lg font-bold text-gray-900 dark:text-white">Télécharger l'agent d'audit</h2>
        <div className="space-y-4">
          <div>
            <label className="label">OS de la cible</label>
            <select className="input" value={osType} onChange={e => setOsType(e.target.value)}>
              <option value="linux">Linux</option>
              <option value="macos_intel">macOS Intel</option>
              <option value="macos_silicon">macOS Apple Silicon</option>
              <option value="windows">Windows</option>
            </select>
          </div>
          <div className="rounded-lg border border-gray-200 bg-gray-50 p-3 dark:border-gray-700 dark:bg-gray-900">
            <p className="text-xs font-semibold text-gray-600 dark:text-gray-400 mb-2 flex items-center gap-1">
              <Terminal className="h-3 w-3" /> Exécuter sur la cible :
            </p>
            <pre className="text-xs font-mono text-gray-700 dark:text-gray-300 whitespace-pre-wrap leading-relaxed">
              {isWindows
                ? `# PowerShell (Administrateur)\n.\\petrix_agent_windows.ps1`
                : `# Terminal (sudo requis)\nsudo bash petrix_agent_${osAgent}.sh`}
            </pre>
            <p className="text-xs text-gray-400 mt-2">
              Le rapport XML généré peut ensuite être importé via "Importer un rapport" — le système sera ajouté automatiquement.
            </p>
          </div>
        </div>
        <div className="mt-6 flex justify-end gap-3">
          <button onClick={onClose} className="btn btn-secondary btn-md">Annuler</button>
          <button onClick={handleDownload} className="btn btn-primary btn-md flex items-center gap-2">
            <Download className="h-4 w-4" /> Télécharger l'agent
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Download Agent Modal ─────────────────────────────────────────────────────

/**
 * Modale guide d'audit en 3 étapes : téléchargement de l'agent, exécution sur la cible,
 * import du rapport XML. Adapte les commandes selon l'OS de la cible (Linux/macOS/Windows).
 * @param target - Cible à auditer.
 * @param onClose - Callback de fermeture.
 */
function DownloadAgentModal({ target, onClose }: { target: Target; onClose: () => void }) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  const osAgent = OS_AGENT[target.os_type] ?? 'linux';
  const isWindows = osAgent === 'windows';

  const importXmlMutation = useMutation({
    mutationFn: (file: File) => hardeningApi.importXml(file),
    onSuccess: (data: any) => {
      queryClient.invalidateQueries({ queryKey: ['systems'] });
      toast.success(`Rapport importé — score ${data.score ?? '?'}/100`);
      onClose();
    },
    onError: () => toast.error("Erreur lors de l'import du rapport XML"),
  });

  const handleDownload = () => {
    const url = `/api/v1/hardening/agent-script/${osAgent}`;
    const a = document.createElement('a');
    a.href = url;
    a.download = isWindows ? 'petrix_agent_windows.ps1' : `petrix_agent_${osAgent}.sh`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-xl dark:bg-gray-800">
        <h2 className="mb-1 text-lg font-bold text-gray-900 dark:text-white">
          Auditer — {target.name}
        </h2>
        <p className="text-sm text-gray-500 dark:text-gray-400 mb-5">
          {OS_LABELS[target.os_type] ?? target.os_type}
        </p>

        {/* Steps */}
        <div className="space-y-4">
          {/* Step 1 */}
          <div className="flex gap-3">
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary-600 text-xs font-bold text-white">1</div>
            <div className="flex-1">
              <p className="text-sm font-semibold text-gray-900 dark:text-white mb-2">Télécharger l'agent d'audit</p>
              <button
                onClick={handleDownload}
                className="flex items-center gap-2 rounded-lg border border-primary-300 bg-primary-50 px-3 py-2 text-sm font-medium text-primary-700 hover:bg-primary-100 dark:border-primary-700 dark:bg-primary-900/20 dark:text-primary-300 transition-colors">
                <Download className="h-4 w-4" />
                {isWindows ? 'petrix_agent_windows.ps1' : `petrix_agent_${osAgent}.sh`}
              </button>
            </div>
          </div>

          {/* Step 2 */}
          <div className="flex gap-3">
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary-600 text-xs font-bold text-white">2</div>
            <div className="flex-1">
              <p className="text-sm font-semibold text-gray-900 dark:text-white mb-2">Exécuter sur le système cible</p>
              <div className="rounded-lg border border-gray-200 bg-gray-50 p-3 dark:border-gray-700 dark:bg-gray-900">
                <pre className="text-xs font-mono text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
                  {isWindows
                    ? `# PowerShell (en tant qu'Administrateur)\n.\\petrix_agent_windows.ps1\n\n# ou avec upload automatique :\n.\\petrix_agent_windows.ps1 -PetrixUrl "http://PETRIX_URL"`
                    : `# Terminal (avec sudo)\nsudo bash petrix_agent_${osAgent}.sh\n\n# ou avec upload automatique :\nsudo bash petrix_agent_${osAgent}.sh http://PETRIX_URL`}
                </pre>
              </div>
              <p className="text-xs text-gray-400 mt-1.5">Le rapport XML est sauvegardé dans <code className="bg-gray-100 dark:bg-gray-700 px-1 rounded">/tmp/</code></p>
            </div>
          </div>

          {/* Step 3 */}
          <div className="flex gap-3">
            <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary-600 text-xs font-bold text-white">3</div>
            <div className="flex-1">
              <p className="text-sm font-semibold text-gray-900 dark:text-white mb-2">Importer le rapport XML</p>
              <input
                ref={fileInputRef}
                type="file"
                accept=".xml"
                className="hidden"
                onChange={e => {
                  const file = e.target.files?.[0];
                  if (file) importXmlMutation.mutate(file);
                  e.target.value = '';
                }}
              />
              <button
                onClick={() => fileInputRef.current?.click()}
                disabled={importXmlMutation.isPending}
                className="flex items-center gap-2 rounded-lg border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-200 dark:hover:bg-gray-700 transition-colors disabled:opacity-50">
                {importXmlMutation.isPending
                  ? <div className="h-4 w-4 animate-spin rounded-full border-2 border-gray-400 border-t-primary-600" />
                  : <FileCode className="h-4 w-4 text-primary-600" />}
                Sélectionner le fichier XML
              </button>
            </div>
          </div>
        </div>

        <div className="mt-6 flex justify-end">
          <button onClick={onClose} className="btn btn-secondary btn-md">Fermer</button>
        </div>
      </div>
    </div>
  );
}

// ─── System Card ──────────────────────────────────────────────────────────────

/**
 * Carte d'un système audité affichant le grade, le score de conformité, le statut
 * et les findings critiques/élevés. Propose les actions Auditer, Rapport et Supprimer.
 */
function SystemCard({ target, onShowAgent, onDelete }: {
  target: Target;
  onShowAgent: (t: Target) => void;
  onDelete: (id: string) => void;
}) {
  const navigate = useNavigate();
  const s = target.latest_session;
  const OsIcon = OS_ICONS[target.os_type] ?? Server;
  const grade = s?.grade ?? null;
  const gradeCfg = grade ? (GRADE_CONFIG[grade] ?? GRADE_CONFIG['F']) : null;
  const score = s?.score ?? null;
  const criticals = s?.findings_summary?.CRITICAL ?? 0;
  const highs = s?.findings_summary?.HIGH ?? 0;

  return (
    <div className="flex flex-col rounded-xl border border-gray-200 bg-white p-5 shadow-sm transition-shadow hover:shadow-md dark:border-gray-700 dark:bg-gray-800">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3 min-w-0">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-gray-100 dark:bg-gray-700">
            <OsIcon className="h-5 w-5 text-gray-500 dark:text-gray-300" />
          </div>
          <div className="min-w-0">
            <p className="truncate font-semibold text-gray-900 dark:text-white">{target.name}</p>
            <p className="truncate text-xs text-gray-400">{OS_LABELS[target.os_type] ?? target.os_type}</p>
          </div>
        </div>

        {/* Grade badge */}
        {gradeCfg && grade ? (
          <div className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border-2 font-bold text-lg ${gradeCfg.bg} ${gradeCfg.text} ${gradeCfg.border}`}>
            {grade}
          </div>
        ) : (
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border-2 border-gray-200 bg-gray-50 text-gray-300 dark:border-gray-600 dark:bg-gray-700 text-lg font-bold">
            —
          </div>
        )}
      </div>

      {/* Score bar */}
      <div className="mt-4">
        {score !== null ? (
          <>
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs text-gray-500">Score de conformité</span>
              <span className={`text-sm font-bold ${SCORE_COLOR(score)}`}>{score.toFixed(0)}/100</span>
            </div>
            <div className="h-2 w-full rounded-full bg-gray-100 dark:bg-gray-700">
              <div
                className={`h-2 rounded-full transition-all ${score >= 80 ? 'bg-green-500' : score >= 60 ? 'bg-yellow-400' : score >= 40 ? 'bg-orange-400' : 'bg-red-500'}`}
                style={{ width: `${score}%` }}
              />
            </div>
          </>
        ) : (
          <div className="h-2 w-full rounded-full bg-gray-100 dark:bg-gray-700" />
        )}
      </div>

      {/* Status + date */}
      <div className="mt-3 flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
        {statusBadge(s)}
        {s?.completed_at && (
          <span className="ml-auto">{formatDate(s.completed_at)}</span>
        )}
      </div>

      {/* Findings highlights */}
      {s?.status === 'completed' && (criticals > 0 || highs > 0) && (
        <div className="mt-3 flex flex-wrap gap-2">
          {criticals > 0 && (
            <span className="flex items-center gap-1 rounded-full bg-red-100 px-2 py-0.5 text-xs font-medium text-red-700 dark:bg-red-900/30 dark:text-red-400">
              <AlertTriangle className="h-3 w-3" /> {criticals} Critique{criticals > 1 ? 's' : ''}
            </span>
          )}
          {highs > 0 && (
            <span className="flex items-center gap-1 rounded-full bg-orange-100 px-2 py-0.5 text-xs font-medium text-orange-700 dark:bg-orange-900/30 dark:text-orange-400">
              {highs} Élevé{highs > 1 ? 's' : ''}
            </span>
          )}
        </div>
      )}

      {/* Actions */}
      <div className="mt-4 flex gap-2 border-t border-gray-100 pt-4 dark:border-gray-700">
        <button
          onClick={() => onShowAgent(target)}
          className="flex flex-1 items-center justify-center gap-1.5 rounded-lg bg-primary-600 px-3 py-2 text-xs font-medium text-white hover:bg-primary-700 transition-colors">
          <Download className="h-3.5 w-3.5" /> Auditer
        </button>
        {s?.session_id && (
          <button
            onClick={() => navigate(`/audit/${s.session_id}`)}
            className="flex flex-1 items-center justify-center gap-1.5 rounded-lg border border-gray-200 px-3 py-2 text-xs font-medium text-gray-600 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-300 dark:hover:bg-gray-700 transition-colors">
            <FileText className="h-3.5 w-3.5" /> Rapport
          </button>
        )}
        <button
          onClick={() => onDelete(target.id)}
          className="flex items-center justify-center rounded-lg border border-gray-200 p-2 text-gray-400 hover:border-red-200 hover:bg-red-50 hover:text-red-500 dark:border-gray-600 dark:hover:bg-red-900/20 transition-colors">
          <Trash2 className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

/**
 * Page principale des systèmes audités.
 * Charge la liste des cibles, affiche les statistiques globales (score moyen, critiques)
 * et gère les flux d'ajout de système et d'import XML global.
 */
export default function AssetsPage() {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [showAdd, setShowAdd] = useState(false);
  const [agentTarget, setAgentTarget] = useState<Target | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const importXmlMutation = useMutation({
    mutationFn: (file: File) => hardeningApi.importXml(file),
    onSuccess: (data: any) => {
      queryClient.invalidateQueries({ queryKey: ['systems'] });
      toast.success(`Rapport importé — ${data.target_name ?? 'système'} · score ${data.score ?? '?'}/100`);
    },
    onError: () => toast.error("Erreur lors de l'import du rapport XML"),
  });

  const { data: targets = [], isLoading } = useQuery<Target[]>({
    queryKey: ['systems'],
    queryFn: hardeningApi.listTargets,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => hardeningApi.deleteTarget(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['systems'] });
      toast.success('Système supprimé');
    },
  });

  const filtered = targets.filter(t =>
    !search ||
    t.name.toLowerCase().includes(search.toLowerCase()) ||
    (t.host ?? '').includes(search)
  );

  const audited   = targets.filter(t => t.latest_session?.status === 'completed');
  const avgScore  = audited.length
    ? audited.reduce((acc, t) => acc + (t.latest_session?.score ?? 0), 0) / audited.length
    : null;
  const totalCriticals = audited.reduce(
    (acc, t) => acc + (t.latest_session?.findings_summary?.CRITICAL ?? 0), 0
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Systèmes audités</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
            Périmètre d'audit — conformité ANSSI-BP-028
          </p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          {/* Hidden global import input */}
          <input
            ref={fileInputRef}
            type="file"
            accept=".xml"
            className="hidden"
            onChange={e => {
              const file = e.target.files?.[0];
              if (file) importXmlMutation.mutate(file);
              e.target.value = '';
            }}
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={importXmlMutation.isPending}
            className="btn btn-md flex items-center gap-2 border border-gray-200 bg-white text-gray-700 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-200 dark:hover:bg-gray-700 disabled:opacity-50">
            {importXmlMutation.isPending
              ? <div className="h-4 w-4 animate-spin rounded-full border-2 border-gray-400 border-t-primary-600" />
              : <FileCode className="h-4 w-4 text-primary-600" />}
            Importer un rapport
          </button>
          <button onClick={() => setShowAdd(true)} className="btn btn-primary btn-md">
            <Download className="mr-2 h-4 w-4" /> Télécharger l'agent
          </button>
        </div>
      </div>

      {/* Stats */}
      {targets.length > 0 && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          {[
            { label: 'Systèmes',  value: targets.length,    sub: 'dans le périmètre', icon: Server,        color: 'text-blue-600' },
            { label: 'Audités',   value: audited.length,    sub: `sur ${targets.length}`, icon: CheckCircle, color: 'text-green-600' },
            { label: 'Score moy.', value: avgScore !== null ? `${avgScore.toFixed(0)}/100` : '—', sub: 'conformité', icon: Shield, color: SCORE_COLOR(avgScore ?? 0) },
            { label: 'Critiques', value: totalCriticals,    sub: 'findings actifs',   icon: AlertTriangle, color: totalCriticals > 0 ? 'text-red-600' : 'text-gray-400' },
          ].map(stat => (
            <div key={stat.label} className="rounded-xl border border-gray-200 bg-white p-4 dark:border-gray-700 dark:bg-gray-800">
              <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400 mb-1">
                <stat.icon className={`h-3.5 w-3.5 ${stat.color}`} />
                {stat.label}
              </div>
              <p className={`text-2xl font-bold ${stat.color}`}>{stat.value}</p>
              <p className="text-xs text-gray-400 mt-0.5">{stat.sub}</p>
            </div>
          ))}
        </div>
      )}

      {/* Search */}
      <div className="relative max-w-sm">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
        <input type="text" placeholder="Rechercher un système…" value={search}
          onChange={e => setSearch(e.target.value)} className="input pl-9 text-sm" />
      </div>

      {/* Grid */}
      {isLoading ? (
        <div className="flex h-48 items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600" />
        </div>
      ) : filtered.length === 0 ? (
        <div className="flex h-64 flex-col items-center justify-center gap-4 rounded-xl border border-dashed border-gray-300 bg-gray-50 text-gray-400 dark:border-gray-700 dark:bg-gray-800/50">
          <Server className="h-12 w-12 opacity-30" />
          <div className="text-center">
            <p className="font-medium text-gray-600 dark:text-gray-300">Aucun système dans le périmètre</p>
            <p className="text-sm mt-1">Ajoutez un système puis téléchargez l'agent pour lancer l'audit</p>
          </div>
          <button onClick={() => setShowAdd(true)} className="btn btn-primary btn-sm">
            <Download className="mr-1.5 h-3.5 w-3.5" /> Télécharger l'agent
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map(target => (
            <SystemCard
              key={target.id}
              target={target}
              onShowAgent={t => setAgentTarget(t)}
              onDelete={id => {
                if (confirm('Supprimer ce système et tous ses audits ?')) {
                  deleteMutation.mutate(id);
                }
              }}
            />
          ))}
        </div>
      )}

      {showAdd && <DownloadOnlyModal onClose={() => setShowAdd(false)} />}
      {agentTarget && <DownloadAgentModal target={agentTarget} onClose={() => setAgentTarget(null)} />}
    </div>
  );
}
