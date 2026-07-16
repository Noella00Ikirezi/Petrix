/**
 * Page de rapport d'audit de durcissement HCO.
 * Affiche le rapport complet d'une session (score, grade, analyse IA Mistral, findings par module,
 * ports réseau dangereux) avec export PDF et chat IA contextuel.
 * Accessible via /audit ou /audit/:sessionId.
 */
import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  ArrowLeft, Shield, ShieldCheck, ShieldX, ShieldAlert,
  CheckCircle2, XCircle, AlertTriangle, Info,
  Monitor, Server, Globe, ChevronDown, ChevronRight,
  BookOpen, Terminal, Clock, FileBarChart2, ListChecks, Sparkles,
  TrendingUp, Zap, Target, Download, Flame,
  Send, MessageSquare, Loader2, ExternalLink,
} from 'lucide-react';
import { useMutation } from '@tanstack/react-query';
import { hardeningApi } from '@/api/client';

// ─── Types ───────────────────────────────────────────────────────────────────

/** Résultat d'un contrôle de sécurité ANSSI-BP-028 avec statut PASS/FAIL/WARN et remédiation. */
interface Finding {
  id: string;
  check_id: string;
  check_name: string;
  module: string;
  description: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO';
  found: string;
  expected: string;
  remediation: string | null;
  status: 'FAIL' | 'WARN' | 'PASS' | 'INFO';
  cve_ids?: string[];
}

interface Session {
  id: string;
  target_id: string;
  target_name: string;
  target_host: string;
  target_os_type: string | null;
  status: string;
  score: number | null;
  grade: string | null;
  findings_summary: Record<string, number> | null;
  total_findings: number;
  total_checks: number;
  passed_checks: number;
  completed_at: string | null;
  duration_seconds: number | null;
}

/** Analyse IA Mistral : résumé exécutif, top priorités, évaluation ANSSI et plan de remédiation. */
interface AiAnalysis {
  resume_executif: string;
  top_priorites: string[];
  evaluation_anssi: string;
  plan_remediation: string;
  risque_global: 'CRITIQUE' | 'ÉLEVÉ' | 'MODÉRÉ' | 'FAIBLE';
}

interface FullReport {
  session: Session;
  findings: Finding[];
  target_description: string | null;
  target_tags: string[] | null;
  ai_analysis: AiAnalysis | null;
}

// ─── ANSSI-BP-028 Mapping ────────────────────────────────────────────────────

// Mapping norme par module : { ref, label, norm (ANSSI|CIS_MACOS|CIS_WIN) }
const NORM_MAP: Record<string, { ref: string; label: string; norm: 'ANSSI' | 'CIS_MAC' | 'CIS_WIN' }[]> = {
  ssh:        [
    { ref: 'ANSSI R4',    label: 'SSH v2 uniquement',            norm: 'ANSSI' },
    { ref: 'ANSSI R5',    label: 'Limiter les tentatives SSH',    norm: 'ANSSI' },
    { ref: 'CIS 2.3.1',   label: 'Remote Login désactivé',        norm: 'CIS_MAC' },
  ],
  firewall:   [
    { ref: 'ANSSI R67',   label: 'Pare-feu local actif',          norm: 'ANSSI' },
    { ref: 'CIS 2.2.2',   label: 'Pare-feu applicatif macOS',      norm: 'CIS_MAC' },
    { ref: 'CIS 9.1',     label: 'Windows Defender Firewall',      norm: 'CIS_WIN' },
  ],
  filevault:  [
    { ref: 'CIS 2.6.1',   label: 'FileVault activé',              norm: 'CIS_MAC' },
  ],
  system:     [
    { ref: 'CIS 5.1.3',   label: 'SIP (System Integrity)',         norm: 'CIS_MAC' },
    { ref: 'CIS 2.7.1',   label: 'Gatekeeper actif',              norm: 'CIS_MAC' },
  ],
  users:      [
    { ref: 'ANSSI R30',   label: 'Comptes inactifs verrouillés',   norm: 'ANSSI' },
    { ref: 'ANSSI R31',   label: 'Complexité mots de passe',        norm: 'ANSSI' },
    { ref: 'CIS 5.6',     label: 'Compte invité macOS désactivé',  norm: 'CIS_MAC' },
    { ref: 'CIS 2.3.1.1', label: 'Administrator intégré désactivé',norm: 'CIS_WIN' },
    { ref: 'CIS 1.1.4',   label: 'Longueur minimale mdp ≥ 12',     norm: 'CIS_WIN' },
  ],
  services:   [
    { ref: 'ANSSI R62',   label: 'Services inutiles désactivés',   norm: 'ANSSI' },
    { ref: 'CIS 18.3.2',  label: 'SMBv1 désactivé (EternalBlue)',   norm: 'CIS_WIN' },
  ],
  updates:    [
    { ref: 'CIS 1.1',     label: 'Mises à jour automatiques macOS', norm: 'CIS_MAC' },
    { ref: 'ANSSI R61',   label: 'Patchs de sécurité appliqués',    norm: 'ANSSI' },
  ],
  network:    [
    { ref: 'ANSSI R12',   label: 'Ports en écoute non nécessaires', norm: 'ANSSI' },
    { ref: 'CIS 9.1',     label: 'Politique entrante Block',         norm: 'CIS_WIN' },
  ],
  kernel:     [
    { ref: 'ANSSI R8',    label: 'ASLR activé',                     norm: 'ANSSI' },
    { ref: 'ANSSI R10',   label: 'dmesg restreint',                  norm: 'ANSSI' },
    { ref: 'ANSSI R13',   label: 'Protection ptrace (YAMA)',          norm: 'ANSSI' },
  ],
  pam:        [
    { ref: 'ANSSI R68',   label: 'Verrouillage après tentatives',    norm: 'ANSSI' },
    { ref: 'ANSSI R69',   label: 'Hachage SHA-512 / YESCRYPT',       norm: 'ANSSI' },
  ],
  logging:    [
    { ref: 'ANSSI R71',   label: 'Démon syslog actif',               norm: 'ANSSI' },
    { ref: 'ANSSI R72',   label: 'auditd configuré',                  norm: 'ANSSI' },
  ],
  filesystem: [
    { ref: 'ANSSI R28',   label: 'noexec/nosuid sur /tmp',           norm: 'ANSSI' },
    { ref: 'ANSSI R49',   label: 'Permissions /etc/shadow',           norm: 'ANSSI' },
    { ref: 'ANSSI R57',   label: 'Binaires setuid non standard',      norm: 'ANSSI' },
  ],
  packages:   [
    { ref: 'ANSSI R58',   label: 'Pas de paquets inutiles',           norm: 'ANSSI' },
    { ref: 'ANSSI R61',   label: 'Mises à jour de sécurité',          norm: 'ANSSI' },
  ],
};

const NORM_BADGE: Record<string, { label: string; cls: string; url: string }> = {
  ANSSI:   { label: 'ANSSI-BP-028', cls: 'bg-purple-50 text-purple-700 border-purple-200 dark:bg-purple-900/20 dark:text-purple-300 dark:border-purple-700', url: 'https://www.ssi.gouv.fr/guide/recommandations-de-securite-relatives-a-un-systeme-gnulinux/' },
  CIS_MAC: { label: 'CIS macOS L1', cls: 'bg-gray-100 text-gray-700 border-gray-300 dark:bg-gray-700 dark:text-gray-300 dark:border-gray-600', url: 'https://www.cisecurity.org/benchmark/apple_os' },
  CIS_WIN: { label: 'CIS WS2019',   cls: 'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-900/20 dark:text-blue-300 dark:border-blue-700', url: 'https://www.cisecurity.org/benchmark/microsoft_windows_server' },
};

// ─── Severity config ─────────────────────────────────────────────────────────

const SEV = {
  CRITICAL: { label: 'Critique',  color: 'text-red-700 dark:text-red-400',    bg: 'bg-red-50 dark:bg-red-900/20',    border: 'border-red-400', badge: 'bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300', icon: ShieldX },
  HIGH:     { label: 'Élevé',    color: 'text-orange-700 dark:text-orange-400', bg: 'bg-orange-50 dark:bg-orange-900/20', border: 'border-orange-400', badge: 'bg-orange-100 text-orange-800 dark:bg-orange-900/40 dark:text-orange-300', icon: ShieldAlert },
  MEDIUM:   { label: 'Moyen',    color: 'text-yellow-700 dark:text-yellow-400', bg: 'bg-yellow-50 dark:bg-yellow-900/20', border: 'border-yellow-400', badge: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/40 dark:text-yellow-300', icon: Shield },
  LOW:      { label: 'Faible',   color: 'text-blue-700 dark:text-blue-400',   bg: 'bg-blue-50 dark:bg-blue-900/20',  border: 'border-blue-400', badge: 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300', icon: ShieldCheck },
  INFO:     { label: 'Info',     color: 'text-gray-600 dark:text-gray-400',   bg: 'bg-gray-50 dark:bg-gray-800',     border: 'border-gray-300', badge: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300', icon: Info },
} as const;

const GRADE_COLOR: Record<string, string> = {
  A: 'text-green-600',  B: 'text-teal-600',   C: 'text-yellow-600',
  D: 'text-orange-600', E: 'text-red-500',     F: 'text-red-700',
};
const GRADE_BG: Record<string, string> = {
  A: 'bg-green-50 border-green-200 dark:bg-green-900/20 dark:border-green-700',
  B: 'bg-teal-50 border-teal-200 dark:bg-teal-900/20 dark:border-teal-700',
  C: 'bg-yellow-50 border-yellow-200 dark:bg-yellow-900/20 dark:border-yellow-700',
  D: 'bg-orange-50 border-orange-200 dark:bg-orange-900/20 dark:border-orange-700',
  E: 'bg-red-50 border-red-200 dark:bg-red-900/20 dark:border-red-700',
  F: 'bg-red-100 border-red-300 dark:bg-red-900/30 dark:border-red-600',
};

const OS_ICON: Record<string, typeof Monitor> = {
  linux: Server, macos_intel: Monitor, macos_silicon: Monitor, windows: Globe,
};
const OS_LABEL: Record<string, string> = {
  linux: 'Linux', macos_intel: 'macOS Intel', macos_silicon: 'macOS Apple Silicon', windows: 'Windows',
};

function formatDate(iso: string | null) {
  if (!iso) return '—';
  return new Date(iso).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}

// ─── Remediation helpers ──────────────────────────────────────────────────────

function isShellCommand(text: string): boolean {
  if (!text) return false;
  return /^(sudo|systemctl|sed|echo|chmod|chown|ufw|iptables|nft\b|firewall-cmd|passwd|usermod|groupmod|apt|yum|dnf|brew|sysctl|auditctl|service|mkdir|cp|mv|rm|cat|tee|update-alternatives)\b|&&|\|\||>>/m
    .test(text.trim());
}

function getPrivilegeBadge(cmd: string): { label: string; cls: string } {
  const needsRoot = /\/(etc|sys|usr|boot|lib|sbin)\//i.test(cmd) ||
    /\b(systemctl|iptables|ufw|nft|firewall-cmd|auditctl|sysctl|usermod|groupmod|passwd|sed -i|chmod|chown)\b/.test(cmd);
  return needsRoot
    ? { label: 'Nécessite root / sudo', cls: 'border-orange-300 bg-orange-50 text-orange-700 dark:border-orange-700 dark:bg-orange-900/20 dark:text-orange-300' }
    : { label: 'Utilisateur standard', cls: 'border-gray-300 bg-gray-50 text-gray-600 dark:border-gray-600 dark:bg-gray-800 dark:text-gray-400' };
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      onClick={() => { navigator.clipboard.writeText(text); setCopied(true); setTimeout(() => setCopied(false), 1800); }}
      className="rounded px-2 py-0.5 text-xs font-medium bg-blue-200 hover:bg-blue-300 text-blue-800 dark:bg-blue-800 dark:hover:bg-blue-700 dark:text-blue-200 transition-colors shrink-0"
    >
      {copied ? '✓ Copié' : 'Copier'}
    </button>
  );
}

// ─── FindingCard ─────────────────────────────────────────────────────────────

/**
 * Carte expandable d'un finding de sécurité : affiche la valeur trouvée vs attendue,
 * la remédiation en ligne de commande, les CVE liées et les références ANSSI-BP-028.
 * @param f - Finding issu du rapport d'audit.
 */
function FindingCard({ f }: { f: Finding }) {
  const [open, setOpen] = useState(false);
  const sev = SEV[f.severity] ?? SEV.INFO;
  const SevIcon = sev.icon;
  const norms = NORM_MAP[f.module?.toLowerCase()] ?? [];
  const isPassed = f.status === 'PASS';
  const isDanger = isDangerousPort(f);

  return (
    <div className={`rounded-xl border-l-4 ${sev.border} ${sev.bg} border border-gray-200 dark:border-gray-700 overflow-hidden`}>
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center gap-3 px-4 py-3 text-left hover:brightness-95 transition-all"
      >
        {isPassed
          ? <CheckCircle2 className="h-4 w-4 shrink-0 text-green-500" />
          : <SevIcon className={`h-4 w-4 shrink-0 ${sev.color}`} />
        }
        <span className="flex-1 font-medium text-sm text-gray-900 dark:text-white">{f.check_name}</span>
        <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${sev.badge}`}>{sev.label}</span>
        {!isPassed && f.severity !== 'INFO' && (
          <span className="rounded border border-red-200 bg-red-50 px-1.5 py-0.5 text-xs font-mono font-bold text-red-600 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400">
            −{({ CRITICAL: 15, HIGH: 8, MEDIUM: 3, LOW: 1 } as Record<string, number>)[f.severity] ?? 0} pts
          </span>
        )}
        {isDanger && (
          <span className="flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-bold bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400">
            <Flame className="h-3 w-3" /> Port dangereux
          </span>
        )}
        <span className="text-xs text-gray-400 ml-2 shrink-0">{f.module}</span>
        {open ? <ChevronDown className="h-4 w-4 text-gray-400 shrink-0" /> : <ChevronRight className="h-4 w-4 text-gray-400 shrink-0" />}
      </button>

      {open && (
        <div className="px-4 pb-4 space-y-4 border-t border-gray-200 dark:border-gray-700 pt-3">
          {f.description && (
            <p className="text-sm text-gray-600 dark:text-gray-400">{f.description}</p>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="rounded-lg bg-red-50 dark:bg-red-900/20 border border-red-100 dark:border-red-800 p-3">
              <p className="text-xs font-semibold text-red-600 dark:text-red-400 mb-1 flex items-center gap-1">
                <XCircle className="h-3 w-3" /> Trouvé
              </p>
              <p className="text-sm font-mono text-red-800 dark:text-red-300 break-all">{f.found || '—'}</p>
            </div>
            <div className="rounded-lg bg-green-50 dark:bg-green-900/20 border border-green-100 dark:border-green-800 p-3">
              <p className="text-xs font-semibold text-green-600 dark:text-green-400 mb-1 flex items-center gap-1">
                <CheckCircle2 className="h-3 w-3" /> Attendu
              </p>
              <p className="text-sm font-mono text-green-800 dark:text-green-300 break-all">{f.expected || '—'}</p>
            </div>
          </div>

          {f.remediation && !isPassed && (() => {
            const isCmd = isShellCommand(f.remediation!);
            const priv  = isCmd ? getPrivilegeBadge(f.remediation!) : null;
            return (
              <div className="rounded-lg bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 p-3 space-y-2">
                {/* Header */}
                <div className="flex items-center justify-between gap-2 flex-wrap">
                  <p className="text-xs font-semibold text-blue-600 dark:text-blue-400 flex items-center gap-1">
                    <Terminal className="h-3 w-3" />
                    {isCmd ? 'Commande de remédiation' : 'Remédiation'}
                  </p>
                  {priv && (
                    <span className={`rounded border px-2 py-0.5 text-xs font-medium ${priv.cls}`}>
                      {priv.label}
                    </span>
                  )}
                </div>
                {/* Command or text */}
                {isCmd ? (
                  <div className="rounded bg-blue-100/60 dark:bg-blue-950/40 border border-blue-200 dark:border-blue-800 p-2">
                    <div className="flex items-start gap-2">
                      <pre className="flex-1 text-xs text-blue-900 dark:text-blue-200 whitespace-pre-wrap font-mono leading-relaxed break-all">{f.remediation}</pre>
                      <CopyButton text={f.remediation!} />
                    </div>
                  </div>
                ) : (
                  <p className="text-xs text-blue-900 dark:text-blue-200 leading-relaxed">{f.remediation}</p>
                )}
              </div>
            );
          })()}

          {f.cve_ids && f.cve_ids.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              <span className="text-xs font-semibold text-gray-500 dark:text-gray-400 self-center">CVE :</span>
              {f.cve_ids.map(cve => (
                <a
                  key={cve}
                  href={`https://nvd.nist.gov/vuln/detail/${cve}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 rounded border border-orange-300 bg-orange-50 px-2 py-0.5 text-xs font-mono font-semibold text-orange-700 hover:bg-orange-100 dark:border-orange-700 dark:bg-orange-950/40 dark:text-orange-400 dark:hover:bg-orange-900/50 transition-colors"
                >
                  {cve}
                  <ExternalLink className="h-2.5 w-2.5 opacity-60" />
                </a>
              ))}
            </div>
          )}

          {norms.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {norms.map(n => {
                const badge = NORM_BADGE[n.norm];
                return (
                  <span key={n.ref} title={n.label}
                    className={`inline-flex items-center rounded border px-1.5 py-0.5 text-xs font-semibold ${badge.cls}`}>
                    {n.ref}
                  </span>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Session Selector (quand pas de sessionId dans l'URL) ────────────────────

/**
 * Sélecteur de session affiché quand /audit est ouvert sans :sessionId.
 * Liste toutes les sessions complétées et redirige vers /audit/:sessionId au choix.
 */
function SessionSelector() {
  const navigate = useNavigate();
  const { data: sessions = [], isLoading } = useQuery({
    queryKey: ['sessions-list'],
    queryFn: hardeningApi.listSessions,
  });

  if (isLoading) return (
    <div className="flex h-64 items-center justify-center">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600" />
    </div>
  );

  if (!sessions.length) return (
    <div className="flex h-64 flex-col items-center justify-center gap-4 rounded-xl border border-dashed border-gray-300 bg-gray-50 text-gray-400 dark:border-gray-700 dark:bg-gray-800/50">
      <FileBarChart2 className="h-12 w-12 opacity-30" />
      <div className="text-center">
        <p className="font-medium text-gray-600 dark:text-gray-300">Aucun rapport disponible</p>
        <p className="text-sm mt-1">Importez un rapport XML depuis la page Systèmes</p>
      </div>
      <Link to="/assets" className="btn btn-primary btn-sm">Aller aux Systèmes</Link>
    </div>
  );

  return (
    <div className="space-y-3">
      <h2 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide">Choisir un rapport</h2>
      {sessions.map((s: Session) => {
        const grade = s.grade ?? '?';
        return (
          <button
            key={s.id}
            onClick={() => navigate(`/audit/${s.id}`)}
            className="w-full flex items-center gap-4 rounded-xl border border-gray-200 bg-white p-4 text-left hover:border-primary-300 hover:shadow-sm transition-all dark:border-gray-700 dark:bg-gray-800"
          >
            <div className={`text-2xl font-black w-12 h-12 flex items-center justify-center rounded-xl border-2 ${GRADE_BG[grade] ?? 'bg-gray-50 border-gray-200'}`}>
              <span className={GRADE_COLOR[grade] ?? 'text-gray-600'}>{grade}</span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="font-semibold text-gray-900 dark:text-white truncate">{s.target_name}</p>
              <p className="text-xs text-gray-500">{s.target_host} · {formatDate(s.completed_at)}</p>
            </div>
            <div className="text-right">
              <p className="text-lg font-bold text-gray-900 dark:text-white">{s.score?.toFixed(0) ?? '—'}<span className="text-xs font-normal text-gray-400">/100</span></p>
              <p className="text-xs text-gray-500">{s.total_findings} findings</p>
            </div>
            <ChevronRight className="h-4 w-4 text-gray-400 shrink-0" />
          </button>
        );
      })}
    </div>
  );
}

// ─── Rapport imprimable / export PDF ─────────────────────────────────────────

/**
 * Vue d'impression du rapport d'audit : génère un document PDF complet avec score,
 * analyse IA et findings groupés par module. Déclenche window.print() si autoDownload est true.
 * @param report - Rapport complet incluant session, findings et analyse IA.
 * @param onClose - Callback pour fermer la vue d'impression.
 * @param autoDownload - Si true, ouvre automatiquement la boîte de dialogue d'impression.
 */
function PrintableReport({ report, onClose, autoDownload = false }: { report: FullReport; onClose: () => void; autoDownload?: boolean }) {
  const contentRef = useRef<HTMLDivElement>(null);
  const { session, findings, ai_analysis } = report;
  const grade = session.grade ?? '?';
  const score = session.score ?? 0;
  const failed = findings.filter(f => f.status !== 'PASS');
  const passed = findings.filter(f => f.status === 'PASS');
  const criticals = failed.filter(f => f.severity === 'CRITICAL');
  const highs     = failed.filter(f => f.severity === 'HIGH');
  const mediums   = failed.filter(f => f.severity === 'MEDIUM');
  const lows      = failed.filter(f => f.severity === 'LOW');
  const scoreColor = score >= 80 ? '#16a34a' : score >= 60 ? '#ca8a04' : score >= 40 ? '#ea580c' : '#dc2626';

  const handlePrint = () => {
    const printContent = document.getElementById('petrix-print-report');
    if (!printContent) return;
    const html = `<!DOCTYPE html><html lang="fr"><head>
<meta charset="utf-8">
<title>Rapport Petrix — ${session.target_name}</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Segoe UI', system-ui, sans-serif; font-size: 13px; color: #111; background: white; }
  .page { max-width: 900px; margin: 0 auto; padding: 32px; }
  .header { display: flex; align-items: center; gap: 24px; border-bottom: 3px solid #1e40af; padding-bottom: 20px; margin-bottom: 24px; }
  .grade-circle { width: 120px; height: 120px; border-radius: 16px; display: flex; flex-direction: column; align-items: center; justify-content: center; border: 3px solid #e5e7eb; }
  .grade-letter { font-size: 72px; font-weight: 900; color: ${scoreColor}; line-height: 1; }
  .score-num { font-size: 24px; font-weight: 700; color: ${scoreColor}; }
  .score-max { font-size: 13px; color: #6b7280; }
  .system-title { font-size: 28px; font-weight: 800; color: #111; }
  .system-meta { color: #6b7280; font-size: 13px; margin-top: 4px; }
  .petrix-logo { margin-left: auto; font-size: 20px; font-weight: 700; color: #1e40af; }
  .score-bar { height: 12px; border-radius: 6px; background: #e5e7eb; margin: 12px 0; overflow: hidden; }
  .score-bar-fill { height: 100%; border-radius: 6px; background: ${scoreColor}; width: ${score}%; }
  .stats { display: flex; gap: 20px; flex-wrap: wrap; margin: 16px 0; }
  .stat { text-align: center; }
  .stat-num { font-size: 24px; font-weight: 700; color: #111; }
  .stat-label { font-size: 11px; color: #6b7280; }
  .section-title { font-size: 16px; font-weight: 700; color: #1e40af; border-bottom: 2px solid #dbeafe; padding-bottom: 8px; margin: 24px 0 12px; }
  .finding { border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px; margin-bottom: 8px; page-break-inside: avoid; }
  .finding-crit { border-left: 4px solid #dc2626; }
  .finding-high { border-left: 4px solid #ea580c; }
  .finding-med  { border-left: 4px solid #ca8a04; }
  .finding-low  { border-left: 4px solid #2563eb; }
  .finding-pass { border-left: 4px solid #16a34a; background: #f0fdf4; }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 700; margin-right: 6px; }
  .badge-crit { background: #fee2e2; color: #dc2626; }
  .badge-high { background: #ffedd5; color: #ea580c; }
  .badge-med  { background: #fef9c3; color: #ca8a04; }
  .badge-low  { background: #dbeafe; color: #2563eb; }
  .badge-pass { background: #dcfce7; color: #16a34a; }
  .finding-name { font-weight: 600; font-size: 13px; margin-bottom: 4px; }
  .finding-desc { font-size: 12px; color: #374151; margin-bottom: 6px; }
  .finding-row { display: flex; gap: 12px; }
  .finding-col { flex: 1; padding: 6px; border-radius: 6px; font-size: 11px; }
  .found-col { background: #fef2f2; border: 1px solid #fecaca; }
  .expected-col { background: #f0fdf4; border: 1px solid #bbf7d0; }
  .remed { background: #eff6ff; border: 1px solid #bfdbfe; padding: 8px; border-radius: 6px; font-family: monospace; font-size: 11px; white-space: pre-wrap; margin-top: 6px; }
  .ai-box { background: #faf5ff; border: 1px solid #e9d5ff; border-radius: 8px; padding: 16px; margin-bottom: 12px; page-break-inside: avoid; }
  .ai-title { font-weight: 700; color: #7c3aed; margin-bottom: 8px; }
  .anssi-badge { display: inline-block; background: #f3e8ff; color: #7c3aed; border: 1px solid #e9d5ff; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 600; margin: 2px; }
  .severity-group-title { font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; margin: 16px 0 8px; }
  .footer { margin-top: 32px; border-top: 1px solid #e5e7eb; padding-top: 16px; text-align: center; font-size: 11px; color: #9ca3af; }
  @media print { .page { padding: 16px; } }
</style></head><body>${printContent.innerHTML}</body></html>`;
    const blob = new Blob([html], { type: 'text/html;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `rapport-petrix-${session.target_name.replace(/[^a-zA-Z0-9]/g, '-')}-${session.grade ?? 'X'}.html`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  useEffect(() => {
    if (autoDownload && contentRef.current) {
      handlePrint();
      onClose();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [autoDownload]);

  if (autoDownload) {
    return (
      <div style={{ position: 'fixed', top: -9999, left: -9999, visibility: 'hidden', pointerEvents: 'none' }}>
        <div ref={contentRef} id="petrix-print-report" style={{ fontFamily: 'system-ui, sans-serif', padding: '32px', background: 'white', maxWidth: 900 }}>

          {/* Header */}
          <div className="header" style={{ display: 'flex', alignItems: 'center', gap: '24px', borderBottom: '3px solid #1e40af', paddingBottom: '20px', marginBottom: '24px' }}>
            <div className="grade-circle" style={{ width: '120px', height: '120px', borderRadius: '16px', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', border: `3px solid ${scoreColor}`, flexShrink: 0 }}>
              <span style={{ fontSize: '64px', fontWeight: 900, color: scoreColor, lineHeight: 1 }}>{grade}</span>
              <span style={{ fontSize: '18px', fontWeight: 700, color: scoreColor }}>{score.toFixed(0)}<span style={{ fontSize: '12px', color: '#9ca3af' }}>/100</span></span>
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                <span style={{ fontSize: '11px', background: '#f3f4f6', padding: '2px 8px', borderRadius: '999px', color: '#374151' }}>
                  {OS_LABEL[session.target_os_type ?? ''] ?? session.target_os_type ?? 'Système'}
                </span>
              </div>
              <h1 style={{ fontSize: '28px', fontWeight: 800, color: '#111' }}>{session.target_name}</h1>
              <p style={{ color: '#6b7280', fontSize: '13px', marginTop: '4px' }}>{session.target_host} · {formatDate(session.completed_at)}</p>
              <div style={{ height: '10px', borderRadius: '5px', background: '#e5e7eb', marginTop: '12px', overflow: 'hidden' }}>
                <div style={{ height: '100%', borderRadius: '5px', background: scoreColor, width: `${score}%` }} />
              </div>
              <div style={{ display: 'flex', gap: '20px', marginTop: '10px', flexWrap: 'wrap' }}>
                <span style={{ fontSize: '12px', color: '#374151' }}><strong>{session.total_checks}</strong> contrôles</span>
                <span style={{ fontSize: '12px', color: '#16a34a' }}><strong>{session.passed_checks}</strong> réussis</span>
                <span style={{ fontSize: '12px', color: '#dc2626' }}><strong>{session.total_findings}</strong> findings</span>
                {criticals.length > 0 && <span style={{ fontSize: '12px', color: '#dc2626' }}>⛔ {criticals.length} Critique{criticals.length > 1 ? 's' : ''}</span>}
                {highs.length > 0 && <span style={{ fontSize: '12px', color: '#ea580c' }}>🔴 {highs.length} Élevé{highs.length > 1 ? 's' : ''}</span>}
              </div>
            </div>
            <div style={{ marginLeft: 'auto', textAlign: 'right', flexShrink: 0 }}>
              <div style={{ fontSize: '20px', fontWeight: 800, color: '#1e40af' }}>PETRIX</div>
              <div style={{ fontSize: '11px', color: '#6b7280' }}>Rapport de sécurité</div>
              <div style={{ fontSize: '11px', color: '#6b7280', marginTop: '4px' }}>ANSSI-BP-028 v2.0</div>
            </div>
          </div>

          {/* AI Analysis */}
          {ai_analysis && (
            <div>
              <h2 style={{ fontSize: '16px', fontWeight: 700, color: '#7c3aed', borderBottom: '2px solid #e9d5ff', paddingBottom: '8px', marginBottom: '12px' }}>
                🤖 Analyse IA — Mistral (Données traitées en UE)
              </h2>
              <div style={{ background: '#faf5ff', border: '1px solid #e9d5ff', borderRadius: '8px', padding: '16px', marginBottom: '12px' }}>
                <div style={{ fontWeight: 700, color: '#7c3aed', marginBottom: '6px', fontSize: '13px' }}>
                  Risque global : <span style={{ background: ai_analysis.risque_global === 'CRITIQUE' ? '#dc2626' : ai_analysis.risque_global === 'ÉLEVÉ' ? '#ea580c' : ai_analysis.risque_global === 'MODÉRÉ' ? '#ca8a04' : '#16a34a', color: 'white', padding: '2px 10px', borderRadius: '999px', fontSize: '12px' }}>{ai_analysis.risque_global}</span>
                </div>
                <p style={{ fontSize: '13px', color: '#374151', lineHeight: '1.6' }}>{ai_analysis.resume_executif}</p>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '12px' }}>
                <div style={{ background: '#fff7ed', border: '1px solid #fed7aa', borderRadius: '8px', padding: '14px' }}>
                  <div style={{ fontWeight: 700, color: '#ea580c', marginBottom: '8px', fontSize: '13px' }}>⚡ Actions prioritaires</div>
                  {ai_analysis.top_priorites.map((p: string, i: number) => (
                    <div key={i} style={{ display: 'flex', gap: '8px', marginBottom: '6px', fontSize: '12px', color: '#374151' }}>
                      <span style={{ background: i === 0 ? '#dc2626' : i === 1 ? '#ea580c' : '#ca8a04', color: 'white', width: '20px', height: '20px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '11px', fontWeight: 700, flexShrink: 0 }}>{i + 1}</span>
                      <span>{p}</span>
                    </div>
                  ))}
                </div>
                <div style={{ background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '8px', padding: '14px' }}>
                  <div style={{ fontWeight: 700, color: '#16a34a', marginBottom: '8px', fontSize: '13px' }}>📋 Plan de remédiation</div>
                  <p style={{ fontSize: '12px', color: '#374151', lineHeight: '1.5', whiteSpace: 'pre-line' }}>{ai_analysis.plan_remediation}</p>
                </div>
              </div>
            </div>
          )}

          {/* Findings */}
          {failed.length > 0 && (
            <div>
              <h2 style={{ fontSize: '16px', fontWeight: 700, color: '#dc2626', borderBottom: '2px solid #fee2e2', paddingBottom: '8px', marginBottom: '12px', marginTop: '24px' }}>
                ⚠️ Findings ({failed.length}) — Écarts de conformité
              </h2>
              {[
                { sev: 'CRITICAL', list: criticals, label: 'Critique' },
                { sev: 'HIGH',     list: highs,     label: 'Élevé' },
                { sev: 'MEDIUM',   list: mediums,   label: 'Moyen' },
                { sev: 'LOW',      list: lows,       label: 'Faible' },
              ].filter(g => g.list.length > 0).map(({ sev, list, label }) => (
                <div key={sev}>
                  <div style={{ fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', margin: '14px 0 8px', color: sev === 'CRITICAL' ? '#dc2626' : sev === 'HIGH' ? '#ea580c' : sev === 'MEDIUM' ? '#ca8a04' : '#2563eb' }}>
                    {label} · {list.length}
                  </div>
                  {list.map(f => (
                    <div key={f.id} style={{ border: '1px solid #e5e7eb', borderLeft: `4px solid ${sev === 'CRITICAL' ? '#dc2626' : sev === 'HIGH' ? '#ea580c' : sev === 'MEDIUM' ? '#ca8a04' : '#2563eb'}`, borderRadius: '8px', padding: '12px', marginBottom: '8px', pageBreakInside: 'avoid' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '6px' }}>
                        <span style={{ background: sev === 'CRITICAL' ? '#fee2e2' : sev === 'HIGH' ? '#ffedd5' : sev === 'MEDIUM' ? '#fef9c3' : '#dbeafe', color: sev === 'CRITICAL' ? '#dc2626' : sev === 'HIGH' ? '#ea580c' : sev === 'MEDIUM' ? '#ca8a04' : '#2563eb', padding: '2px 8px', borderRadius: '12px', fontSize: '11px', fontWeight: 700 }}>{label.toUpperCase()}</span>
                        <span style={{ fontWeight: 600, fontSize: '13px' }}>{f.check_name}</span>
                        <span style={{ marginLeft: 'auto', fontSize: '11px', color: '#9ca3af' }}>{f.module}</span>
                      </div>
                      {f.description && <p style={{ fontSize: '12px', color: '#374151', marginBottom: '8px' }}>{f.description}</p>}
                      <div style={{ display: 'flex', gap: '10px' }}>
                        <div style={{ flex: 1, background: '#fef2f2', border: '1px solid #fecaca', borderRadius: '6px', padding: '6px', fontSize: '11px' }}>
                          <div style={{ fontWeight: 700, color: '#dc2626', marginBottom: '2px' }}>Trouvé</div>
                          <code style={{ color: '#b91c1c' }}>{f.found || '—'}</code>
                        </div>
                        <div style={{ flex: 1, background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '6px', padding: '6px', fontSize: '11px' }}>
                          <div style={{ fontWeight: 700, color: '#16a34a', marginBottom: '2px' }}>Attendu</div>
                          <code style={{ color: '#15803d' }}>{f.expected || '—'}</code>
                        </div>
                      </div>
                      {f.remediation && (
                        <div style={{ background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: '6px', padding: '8px', marginTop: '8px' }}>
                          <div style={{ fontWeight: 700, color: '#1d4ed8', marginBottom: '4px', fontSize: '11px' }}>🔧 Remédiation</div>
                          <pre style={{ fontFamily: 'monospace', fontSize: '11px', color: '#1e40af', whiteSpace: 'pre-wrap', margin: 0 }}>{f.remediation}</pre>
                        </div>
                      )}
                      {f.cve_ids && f.cve_ids.length > 0 && (
                        <div style={{ marginTop: '8px', display: 'flex', flexWrap: 'wrap', gap: '4px', alignItems: 'center' }}>
                          <span style={{ fontSize: '11px', fontWeight: 600, color: '#6b7280' }}>CVE :</span>
                          {f.cve_ids.map(cve => (
                            <a key={cve} href={`https://nvd.nist.gov/vuln/detail/${cve}`} style={{ display: 'inline-block', background: '#fff7ed', color: '#c2410c', border: '1px solid #fdba74', padding: '1px 6px', borderRadius: '4px', fontSize: '10px', fontFamily: 'monospace', fontWeight: 700, textDecoration: 'none' }}>
                              {cve} ↗
                            </a>
                          ))}
                        </div>
                      )}
                      {(NORM_MAP[f.module?.toLowerCase()] ?? []).length > 0 && (
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px', marginTop: '6px' }}>
                          {(NORM_MAP[f.module?.toLowerCase()] ?? []).map((n: { ref: string; label: string; norm: string }) => (
                            <span key={n.ref} title={n.label} style={{ fontSize: '10px', fontWeight: 600, border: '1px solid #e9d5ff', background: '#f5f3ff', color: '#7c3aed', borderRadius: '4px', padding: '1px 6px' }}>
                              {n.ref}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ))}
            </div>
          )}

          {/* Passed */}
          {passed.length > 0 && (
            <div>
              <h2 style={{ fontSize: '16px', fontWeight: 700, color: '#16a34a', borderBottom: '2px solid #dcfce7', paddingBottom: '8px', marginBottom: '12px', marginTop: '24px' }}>
                ✅ Contrôles réussis ({passed.length})
              </h2>
              <div style={{ columns: 2, columnGap: '12px' }}>
                {passed.map(f => (
                  <div key={f.id} style={{ border: '1px solid #dcfce7', borderLeft: '4px solid #16a34a', borderRadius: '6px', padding: '8px', marginBottom: '6px', background: '#f0fdf4', breakInside: 'avoid' }}>
                    <span style={{ fontWeight: 600, fontSize: '12px', color: '#15803d' }}>✓ {f.check_name}</span>
                    <span style={{ display: 'block', fontSize: '11px', color: '#6b7280', marginTop: '2px' }}>{f.module}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Footer */}
          <div style={{ marginTop: '32px', borderTop: '1px solid #e5e7eb', paddingTop: '16px', textAlign: 'center', fontSize: '11px', color: '#9ca3af' }}>
            Rapport généré par Petrix Platform · ANSSI-BP-028 v2.0 · {new Date().toLocaleDateString('fr-FR', { day: '2-digit', month: 'long', year: 'numeric' })}
          </div>
        </div>
      </div>
    );
  }

  return null;
}

// ─── Main Page ────────────────────────────────────────────────────────────────

type Tab = 'findings' | 'ai' | 'compliance';

// Detect if a network finding is a dangerous port
/** Prédicat : renvoie true si le finding correspond à un port réseau considéré dangereux (FTP, Telnet, SMB, Redis…). */
const isDangerousPort = (f: Finding) =>
  f.module === 'network' && f.check_name.includes('DANGEREUX');


/**
 * Page de rapport d'audit : sélectionne la session (via URL ou sélecteur),
 * charge le rapport complet, et affiche score, analyse IA Mistral, findings filtrés
 * par module/sévérité, ports réseau dangereux et interface de chat IA contextuel.
 */
export default function AuditReportPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const [tab, setTab] = useState<Tab>('findings');
  const [expandAll, setExpandAll] = useState(false);
  const [showPrint, setShowPrint] = useState(false);
  const [chatMessages, setChatMessages] = useState<{ role: 'user' | 'ai'; content: string }[]>([]);
  const [chatInput, setChatInput] = useState('');

  const chatMutation = useMutation({
    mutationFn: ({ sessionId, question }: { sessionId: string; question: string }) =>
      hardeningApi.aiChat(sessionId, question),
    onSuccess: (data) => {
      setChatMessages(prev => [...prev, { role: 'ai', content: data.answer }]);
    },
    onError: () => {
      setChatMessages(prev => [...prev, { role: 'ai', content: "Désolé, une erreur est survenue. Vérifiez que la clé API Mistral est configurée." }]);
    },
  });

  const { data: report, isLoading, error } = useQuery<FullReport>({
    queryKey: ['audit-report', sessionId],
    queryFn: () => hardeningApi.getFullReport(sessionId!),
    enabled: !!sessionId,
  });

  // ─ No sessionId → show selector
  if (!sessionId) {
    return (
      <div className="space-y-6 max-w-3xl mx-auto">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <FileBarChart2 className="h-6 w-6 text-primary-600" /> Rapports d'audit
          </h1>
          <p className="text-sm text-gray-500 mt-0.5">Analyse détaillée des audits de conformité</p>
        </div>
        <SessionSelector />
      </div>
    );
  }

  if (isLoading) return (
    <div className="flex h-64 items-center justify-center">
      <div className="h-10 w-10 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600" />
    </div>
  );

  if (error || !report) return (
    <div className="flex h-64 flex-col items-center justify-center gap-3 text-gray-400">
      <ShieldX className="h-12 w-12 opacity-30" />
      <p>Rapport introuvable</p>
      <button onClick={() => navigate('/audit')} className="btn btn-primary btn-sm">Retour</button>
    </div>
  );

  const { session, findings, ai_analysis } = report;
  const grade = session.grade ?? '?';
  const score = session.score ?? 0;
  const OsIcon = OS_ICON[session.target_os_type ?? ''] ?? Server;

  // PrintableReport se monte invisiblement, génère le HTML et déclenche le téléchargement
  if (showPrint) {
    return <PrintableReport report={report} onClose={() => setShowPrint(false)} autoDownload />;
  }

  const failed  = findings.filter(f => f.status !== 'PASS');

  const bySev = (sev: string) => failed.filter(f => f.severity === sev);
  const criticals = bySev('CRITICAL');
  const highs     = bySev('HIGH');
  const mediums   = bySev('MEDIUM');
  const lows      = bySev('LOW');

  const moduleNames = [...new Set(findings.map(f => f.module))].sort();
  const complianceRows = moduleNames.map(mod => {
    const modFindings = findings.filter(f => f.module === mod);
    const modFailed   = modFindings.filter(f => f.status !== 'PASS');
    const norms       = NORM_MAP[mod.toLowerCase()] ?? [];
    const ok          = modFailed.length === 0;
    return { mod, total: modFindings.length, failed: modFailed.length, ok, norms };
  });

  const scoreColor = score >= 80 ? 'text-green-600' : score >= 60 ? 'text-yellow-600' : score >= 40 ? 'text-orange-600' : 'text-red-600';
  const scoreBar   = score >= 80 ? 'bg-green-500' : score >= 60 ? 'bg-yellow-400' : score >= 40 ? 'bg-orange-400' : 'bg-red-500';

  return (
    <div className="space-y-6 pb-12">

      {/* ── Breadcrumb ── */}
      <div className="flex items-center gap-2 text-sm text-gray-500">
        <button onClick={() => navigate('/assets')} className="hover:text-gray-900 dark:hover:text-white flex items-center gap-1 transition-colors">
          <ArrowLeft className="h-3.5 w-3.5" /> Systèmes
        </button>
        <span>/</span>
        <button onClick={() => navigate('/audit')} className="hover:text-gray-900 dark:hover:text-white transition-colors">Rapports</button>
        <span>/</span>
        <span className="text-gray-900 dark:text-white font-medium">{session.target_name}</span>
        <button
          onClick={() => setShowPrint(true)}
          className="ml-auto flex items-center gap-2 rounded-lg bg-gray-900 dark:bg-white px-4 py-2 text-sm font-semibold text-white dark:text-gray-900 hover:opacity-90 transition-opacity"
        >
          <Download className="h-4 w-4" /> Télécharger le rapport
        </button>
      </div>

      {/* ── Hero banner ── */}
      <div className={`rounded-2xl border-2 p-6 ${GRADE_BG[grade] ?? 'bg-gray-50 border-gray-200'}`}>
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-6">

          {/* Grade circle */}
          <div className={`flex-shrink-0 h-24 w-24 rounded-2xl border-2 flex flex-col items-center justify-center ${GRADE_BG[grade] ?? ''}`}>
            <span className={`text-5xl font-black ${GRADE_COLOR[grade] ?? 'text-gray-600'}`}>{grade}</span>
          </div>

          {/* System info */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <OsIcon className="h-5 w-5 text-gray-500" />
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white truncate">{session.target_name}</h1>
            </div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-3">
              {session.target_host} · {OS_LABEL[session.target_os_type ?? ''] ?? session.target_os_type ?? 'Inconnu'}
            </p>

            {/* Score bar */}
            <div className="flex items-center gap-3 mb-3">
              <div className="flex-1 h-3 rounded-full bg-gray-200 dark:bg-gray-700">
                <div className={`h-3 rounded-full transition-all duration-700 ${scoreBar}`} style={{ width: `${score}%` }} />
              </div>
              <span className={`text-xl font-black ${scoreColor}`}>{score.toFixed(0)}<span className="text-sm font-normal text-gray-400">/100</span></span>
            </div>

            {/* Stats row */}
            <div className="flex flex-wrap items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
              <span className="flex items-center gap-1"><ListChecks className="h-3.5 w-3.5" />{session.total_checks} contrôles</span>
              <span className="flex items-center gap-1 text-green-600 dark:text-green-400"><CheckCircle2 className="h-3.5 w-3.5" />{session.passed_checks} réussis</span>
              {session.total_findings > 0 && <span className="flex items-center gap-1 text-red-500"><XCircle className="h-3.5 w-3.5" />{session.total_findings} findings</span>}
              {session.completed_at && <span className="flex items-center gap-1 ml-auto"><Clock className="h-3.5 w-3.5" />{formatDate(session.completed_at)}</span>}
            </div>
          </div>

          {/* Severity pills */}
          <div className="flex flex-wrap gap-2 shrink-0">
            {criticals.length > 0 && <span className="flex items-center gap-1 rounded-full bg-red-100 px-3 py-1 text-xs font-bold text-red-700 dark:bg-red-900/30 dark:text-red-400"><ShieldX className="h-3.5 w-3.5" />{criticals.length} Critique{criticals.length > 1 ? 's' : ''}</span>}
            {highs.length > 0 && <span className="flex items-center gap-1 rounded-full bg-orange-100 px-3 py-1 text-xs font-bold text-orange-700 dark:bg-orange-900/30 dark:text-orange-400"><ShieldAlert className="h-3.5 w-3.5" />{highs.length} Élevé{highs.length > 1 ? 's' : ''}</span>}
            {mediums.length > 0 && <span className="flex items-center gap-1 rounded-full bg-yellow-100 px-3 py-1 text-xs font-bold text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400"><Shield className="h-3.5 w-3.5" />{mediums.length} Moyen{mediums.length > 1 ? 's' : ''}</span>}
            {lows.length > 0 && <span className="flex items-center gap-1 rounded-full bg-blue-100 px-3 py-1 text-xs font-bold text-blue-700 dark:bg-blue-900/30 dark:text-blue-400"><ShieldCheck className="h-3.5 w-3.5" />{lows.length} Faible{lows.length > 1 ? 's' : ''}</span>}
          </div>
        </div>
      </div>

      {/* ── Tabs ── */}
      <div className="flex gap-1 border-b border-gray-200 dark:border-gray-700 overflow-x-auto">
        {[
          { key: 'findings',   label: `Écarts (${failed.length})`,   icon: AlertTriangle },
          { key: 'ai',         label: 'Synthèse IA',                  icon: Sparkles },
          { key: 'compliance', label: 'Conformité',                   icon: BookOpen },
        ].map(t => (
          <button
            key={t.key}
            onClick={() => setTab(t.key as Tab)}
            className={`flex items-center gap-1.5 px-4 py-2.5 text-sm font-medium border-b-2 whitespace-nowrap transition-colors -mb-px ${
              tab === t.key
                ? 'border-primary-600 text-primary-700 dark:text-primary-400'
                : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
            }`}
          >
            <t.icon className="h-4 w-4" />
            {t.label}
          </button>
        ))}
      </div>

      {/* ── Tab: Analyse IA ── */}
      {tab === 'ai' && (
        <div className="space-y-4">
          {!ai_analysis ? (
            <div className="flex h-48 flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-purple-200 bg-purple-50 dark:border-purple-800 dark:bg-purple-900/10 text-purple-400">
              <Sparkles className="h-10 w-10 opacity-50" />
              <div className="text-center">
                <p className="font-medium text-purple-600 dark:text-purple-400">Analyse IA non disponible</p>
                <p className="text-sm mt-1 text-purple-400">Réimportez le rapport XML pour générer l'analyse Mistral</p>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {/* Risque global badge */}
              <div className="flex items-center gap-3">
                <span className={`inline-flex items-center gap-2 rounded-full px-4 py-1.5 text-sm font-bold ${
                  ai_analysis.risque_global === 'CRITIQUE' ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' :
                  ai_analysis.risque_global === 'ÉLEVÉ'    ? 'bg-orange-100 text-orange-700 dark:bg-orange-900/30 dark:text-orange-400' :
                  ai_analysis.risque_global === 'MODÉRÉ'   ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400' :
                  'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                }`}>
                  <Sparkles className="h-4 w-4" />
                  Risque global : {ai_analysis.risque_global}
                </span>
                <span className="text-xs text-gray-400">Analyse par Mistral AI · Données traitées en UE</span>
              </div>

              {/* Résumé exécutif */}
              <div className="rounded-xl border border-purple-200 bg-gradient-to-br from-purple-50 to-indigo-50 p-5 dark:border-purple-800 dark:from-purple-900/20 dark:to-indigo-900/20">
                <h3 className="flex items-center gap-2 text-sm font-bold text-purple-700 dark:text-purple-300 mb-2">
                  <Sparkles className="h-4 w-4" /> Résumé exécutif
                </h3>
                <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">{ai_analysis.resume_executif}</p>
              </div>

              {/* Top priorités */}
              <div className="rounded-xl border border-orange-200 bg-orange-50 p-5 dark:border-orange-800 dark:bg-orange-900/10">
                <h3 className="flex items-center gap-2 text-sm font-bold text-orange-700 dark:text-orange-300 mb-3">
                  <Zap className="h-4 w-4" /> Actions prioritaires
                </h3>
                <ol className="space-y-2">
                  {ai_analysis.top_priorites.map((p, i) => (
                    <li key={i} className="flex items-start gap-3">
                      <span className={`flex-shrink-0 h-6 w-6 rounded-full flex items-center justify-center text-xs font-bold text-white ${
                        i === 0 ? 'bg-red-500' : i === 1 ? 'bg-orange-500' : 'bg-yellow-500'
                      }`}>{i + 1}</span>
                      <span className="text-sm text-gray-700 dark:text-gray-300 pt-0.5">{p}</span>
                    </li>
                  ))}
                </ol>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {/* Évaluation ANSSI */}
                <div className="rounded-xl border border-blue-200 bg-blue-50 p-5 dark:border-blue-800 dark:bg-blue-900/10">
                  <h3 className="flex items-center gap-2 text-sm font-bold text-blue-700 dark:text-blue-300 mb-2">
                    <Target className="h-4 w-4" /> Conformité ANSSI-BP-028
                  </h3>
                  <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">{ai_analysis.evaluation_anssi}</p>
                </div>

                {/* Plan remédiation */}
                <div className="rounded-xl border border-green-200 bg-green-50 p-5 dark:border-green-800 dark:bg-green-900/10">
                  <h3 className="flex items-center gap-2 text-sm font-bold text-green-700 dark:text-green-300 mb-2">
                    <TrendingUp className="h-4 w-4" /> Plan de remédiation
                  </h3>
                  <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-line">{ai_analysis.plan_remediation}</p>
                </div>
              </div>
            </div>
          )}

          {/* ── Chat IA ── */}
          <div className="rounded-xl border border-purple-200 bg-gradient-to-b from-purple-50/60 to-white p-5 dark:border-purple-800 dark:from-purple-900/10 dark:to-gray-900 space-y-4">
            <h3 className="flex items-center gap-2 text-sm font-bold text-purple-700 dark:text-purple-300">
              <MessageSquare className="h-4 w-4" /> Posez une question à l'IA sur cet audit
            </h3>

            {/* Message history */}
            {chatMessages.length > 0 && (
              <div className="space-y-3 max-h-96 overflow-y-auto pr-1">
                {chatMessages.map((msg, i) => (
                  <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    {msg.role === 'ai' && (
                      <div className="flex-shrink-0 h-7 w-7 rounded-full bg-purple-600 flex items-center justify-center">
                        <Sparkles className="h-3.5 w-3.5 text-white" />
                      </div>
                    )}
                    <div className={`max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
                      msg.role === 'user'
                        ? 'bg-purple-600 text-white rounded-tr-sm'
                        : 'bg-white dark:bg-gray-800 border border-purple-100 dark:border-purple-800 text-gray-700 dark:text-gray-300 rounded-tl-sm'
                    }`}>
                      <p className="whitespace-pre-wrap">{msg.content}</p>
                    </div>
                    {msg.role === 'user' && (
                      <div className="flex-shrink-0 h-7 w-7 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center">
                        <span className="text-xs font-bold text-gray-600 dark:text-gray-300">Moi</span>
                      </div>
                    )}
                  </div>
                ))}
                {chatMutation.isPending && (
                  <div className="flex gap-3 justify-start">
                    <div className="flex-shrink-0 h-7 w-7 rounded-full bg-purple-600 flex items-center justify-center">
                      <Sparkles className="h-3.5 w-3.5 text-white" />
                    </div>
                    <div className="rounded-2xl rounded-tl-sm bg-white dark:bg-gray-800 border border-purple-100 dark:border-purple-800 px-4 py-3">
                      <Loader2 className="h-4 w-4 text-purple-500 animate-spin" />
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Input */}
            <form
              onSubmit={(e) => {
                e.preventDefault();
                const q = chatInput.trim();
                if (!q || chatMutation.isPending || !session?.id) return;
                setChatMessages(prev => [...prev, { role: 'user', content: q }]);
                setChatInput('');
                chatMutation.mutate({ sessionId: session.id, question: q });
              }}
              className="flex gap-2"
            >
              <input
                type="text"
                value={chatInput}
                onChange={e => setChatInput(e.target.value)}
                placeholder="Ex : Quels sont les risques les plus urgents ? Que faire pour le SSH ?"
                maxLength={500}
                disabled={chatMutation.isPending}
                className="flex-1 rounded-xl border border-purple-200 bg-white dark:bg-gray-800 dark:border-purple-800 px-4 py-2.5 text-sm text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-400 disabled:opacity-60"
              />
              <button
                type="submit"
                disabled={!chatInput.trim() || chatMutation.isPending}
                className="flex items-center gap-2 rounded-xl bg-purple-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {chatMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
                Envoyer
              </button>
            </form>
            <p className="text-xs text-gray-400">Mistral AI · Contexte limité aux findings de cette session · Données traitées en UE</p>
          </div>
        </div>
      )}

      {/* ── Tab: Findings ── */}
      {tab === 'findings' && (
        <div className="space-y-6">
          {failed.length === 0 ? (
            <div className="flex h-40 flex-col items-center justify-center gap-2 rounded-xl bg-green-50 dark:bg-green-900/10 text-green-600">
              <CheckCircle2 className="h-10 w-10" />
              <p className="font-semibold">Aucun finding — système conforme !</p>
            </div>
          ) : (
            <>
              {/* Expand toggle */}
              <div className="flex justify-end">
                <button onClick={() => setExpandAll(e => !e)} className="text-xs text-primary-600 hover:underline">
                  {expandAll ? 'Tout replier' : 'Tout déplier'}
                </button>
              </div>

              {[
                { sev: 'CRITICAL', list: criticals },
                { sev: 'HIGH',     list: highs },
                { sev: 'MEDIUM',   list: mediums },
                { sev: 'LOW',      list: lows },
              ].map(({ sev, list }) => list.length > 0 && (
                <div key={sev} className="space-y-2">
                  <h3 className={`text-xs font-bold uppercase tracking-widest ${SEV[sev as keyof typeof SEV].color}`}>
                    {SEV[sev as keyof typeof SEV].label} · {list.length}
                  </h3>
                  {list.map(f => <FindingCard key={f.id} f={f} />)}
                </div>
              ))}
            </>
          )}
        </div>
      )}

      {/* ── Tab: Compliance multi-norme ── */}
      {tab === 'compliance' && (
        <div className="space-y-5">
          {/* Liens normes officielles */}
          <div className="flex flex-wrap gap-2">
            {Object.entries(NORM_BADGE).map(([key, n]) => (
              <a key={key} href={n.url} target="_blank" rel="noopener noreferrer"
                className={`inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-semibold hover:shadow-sm transition-all ${n.cls}`}>
                {n.label} <ExternalLink className="h-3 w-3 opacity-60" />
              </a>
            ))}
          </div>

          <div className="overflow-x-auto rounded-xl border border-gray-200 dark:border-gray-700">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 dark:bg-gray-800 text-xs text-gray-500 uppercase tracking-wide">
                <tr>
                  <th className="px-4 py-3 text-left">Module</th>
                  <th className="px-4 py-3 text-left">Normes applicables</th>
                  <th className="px-4 py-3 text-center">Contrôles</th>
                  <th className="px-4 py-3 text-center">Résultat</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                {complianceRows.map(row => (
                  <tr key={row.mod} className="bg-white dark:bg-gray-800/50 hover:bg-gray-50 dark:hover:bg-gray-700/30 transition-colors">
                    <td className="px-4 py-3 font-medium text-gray-900 dark:text-white capitalize">{row.mod}</td>
                    <td className="px-4 py-3">
                      <div className="flex flex-wrap gap-1">
                        {row.norms.length > 0
                          ? row.norms.map(n => {
                              const badge = NORM_BADGE[n.norm];
                              return (
                                <span key={n.ref} title={n.label}
                                  className={`rounded border px-1.5 py-0.5 text-xs font-medium ${badge.cls}`}>
                                  {n.ref}
                                </span>
                              );
                            })
                          : <span className="text-gray-400 text-xs">—</span>
                        }
                      </div>
                    </td>
                    <td className="px-4 py-3 text-center text-gray-600 dark:text-gray-400">
                      {row.total - row.failed}/{row.total}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {row.ok
                        ? <span className="inline-flex items-center gap-1 rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-medium text-green-700 dark:bg-green-900/30 dark:text-green-400"><CheckCircle2 className="h-3 w-3" /> Conforme</span>
                        : <span className="inline-flex items-center gap-1 rounded-full bg-red-100 px-2.5 py-0.5 text-xs font-medium text-red-700 dark:bg-red-900/30 dark:text-red-400"><XCircle className="h-3 w-3" /> {row.failed} écart{row.failed > 1 ? 's' : ''}</span>
                      }
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

    </div>
  );
}
