import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  Server,
  Shield,
  ShieldCheck,
  TrendingUp,
  AlertTriangle,
  Activity,
  ChevronRight,
  RefreshCw,
  ArrowUpRight,
  ArrowDownRight,
} from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { dashboardApi } from '@/api/client';
import { useAuthStore } from '@/stores/authStore';

// ─── Constantes ──────────────────────────────────────────────────────────────

const SEV_COLOR: Record<string, string> = {
  critical: '#ef4444',
  high:     '#f97316',
  medium:   '#eab308',
  low:      '#3b82f6',
  info:     '#64748b',
};

const SEV_LABEL: Record<string, string> = {
  critical: 'Critique',
  high:     'Élevé',
  medium:   'Moyen',
  low:      'Faible',
  info:     'Info',
};

const GRADE_META: Record<string, { color: string; label: string }> = {
  A: { color: '#3b82f6', label: 'Excellent' },
  B: { color: '#22c55e', label: 'Bon' },
  C: { color: '#eab308', label: 'Moyen' },
  D: { color: '#f97316', label: 'Insuffisant' },
  F: { color: '#ef4444', label: 'Critique' },
};

function scoreToGrade(score: number): string {
  if (score >= 90) return 'A';
  if (score >= 75) return 'B';
  if (score >= 60) return 'C';
  if (score >= 40) return 'D';
  return 'F';
}

// ─── Jauge circulaire ─────────────────────────────────────────────────────────

function ScoreRing({ score, size = 120 }: { score: number | null; size?: number }) {
  const r = (size / 2) - 10;
  const cx = size / 2;
  const cy = size / 2;
  const circumference = 2 * Math.PI * r;
  const grade = score !== null ? scoreToGrade(score) : '—';
  const meta = score !== null ? (GRADE_META[grade] ?? GRADE_META.F) : { color: 'var(--faint)', label: '' };
  const progress = score !== null ? (score / 100) * circumference : 0;

  return (
    <div style={{ position: 'relative', width: size, height: size, flexShrink: 0 }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        {/* Track */}
        <circle cx={cx} cy={cy} r={r} fill="none" stroke="var(--line)" strokeWidth="7" />
        {/* Progress */}
        <circle
          cx={cx} cy={cy} r={r}
          fill="none"
          stroke={meta.color}
          strokeWidth="7"
          strokeLinecap="round"
          strokeDasharray={`${progress} ${circumference}`}
          transform={`rotate(-90 ${cx} ${cy})`}
          style={{ transition: 'stroke-dasharray 1.2s ease' }}
        />
      </svg>
      <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
        <span style={{ fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: size * 0.22, color: meta.color, lineHeight: 1 }}>
          {grade}
        </span>
        <span style={{ fontFamily: 'var(--font-mono)', fontSize: size * 0.1, color: 'var(--dim)', marginTop: 2 }}>
          {score !== null ? `${score}/100` : '—'}
        </span>
      </div>
    </div>
  );
}

// ─── Carte stat ───────────────────────────────────────────────────────────────

function StatCard({
  label,
  value,
  sub,
  icon: Icon,
  accent,
  to,
}: {
  label: string;
  value: string | number;
  sub?: string;
  icon: React.ElementType;
  accent: string;
  to?: string;
}) {
  const inner = (
    <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 16, height: '100%' }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
        <div
          style={{
            width: 36, height: 36, borderRadius: 3,
            background: accent + '18',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}
        >
          <Icon style={{ width: 18, height: 18, color: accent }} />
        </div>
        {to && <ChevronRight style={{ width: 14, height: 14, color: 'var(--faint)' }} />}
      </div>
      <div>
        <div style={{ fontFamily: 'var(--font-display)', fontSize: 28, fontWeight: 700, color: 'var(--text)', lineHeight: 1 }}>
          {value}
        </div>
        <div style={{ fontSize: 12, color: 'var(--faint)', marginTop: 4, fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase' }}>
          {label}
        </div>
        {sub && (
          <div style={{ fontSize: 11, color: 'var(--dim)', marginTop: 4 }}>{sub}</div>
        )}
      </div>
    </div>
  );

  return to
    ? <Link to={to} style={{ display: 'block', textDecoration: 'none' }}>{inner}</Link>
    : inner;
}

// ─── Barre de sévérité ────────────────────────────────────────────────────────

function SeverityBar({ sev, count, total }: { sev: string; count: number; total: number }) {
  const pct = total > 0 ? Math.round((count / total) * 100) : 0;
  const color = SEV_COLOR[sev] ?? 'var(--faint)';
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
      <div style={{ width: 70, fontSize: 11, fontWeight: 600, letterSpacing: '0.06em', textTransform: 'uppercase', color: 'var(--faint)', flexShrink: 0 }}>
        {SEV_LABEL[sev] ?? sev}
      </div>
      <div style={{ flex: 1, height: 4, background: 'var(--line)', borderRadius: 2, overflow: 'hidden' }}>
        <div style={{ width: `${pct}%`, height: '100%', background: color, borderRadius: 2, transition: 'width 1s ease' }} />
      </div>
      <div style={{ width: 28, textAlign: 'right', fontFamily: 'var(--font-mono)', fontSize: 13, fontWeight: 700, color, flexShrink: 0 }}>
        {count}
      </div>
    </div>
  );
}

// ─── Badge grade ──────────────────────────────────────────────────────────────

function GradeBadge({ grade }: { grade: string | null }) {
  if (!grade) return <span style={{ color: 'var(--faint)' }}>—</span>;
  const meta = GRADE_META[grade] ?? GRADE_META.F;
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center',
      fontFamily: 'var(--font-display)', fontWeight: 700, fontSize: 13,
      padding: '2px 8px', borderRadius: 3,
      background: meta.color + '18',
      color: meta.color,
      border: `1px solid ${meta.color}40`,
    }}>
      {grade}
    </span>
  );
}

// ─── Badge status ────────────────────────────────────────────────────────────

const STATUS_META: Record<string, { color: string; label: string }> = {
  completed:  { color: '#3b82f6', label: 'Terminé' },
  running:    { color: '#eab308', label: 'En cours' },
  pending:    { color: '#64748b', label: 'En attente' },
  failed:     { color: '#ef4444', label: 'Échec' },
  connecting: { color: '#a855f7', label: 'Connexion' },
};

function StatusBadge({ status }: { status: string }) {
  const meta = STATUS_META[status] ?? { color: 'var(--faint)', label: status };
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center',
      fontSize: 11, fontWeight: 600, letterSpacing: '0.05em',
      padding: '2px 8px', borderRadius: 3,
      background: meta.color + '18',
      color: meta.color,
      border: `1px solid ${meta.color}40`,
      fontFamily: 'var(--font-display)',
      textTransform: 'uppercase',
    }}>
      {meta.label}
    </span>
  );
}

// ─── Tooltip chart ───────────────────────────────────────────────────────────

function ChartTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: 'var(--panel)', border: '1px solid var(--line)',
      padding: '10px 14px', borderRadius: 3, fontSize: 12,
    }}>
      <p style={{ color: 'var(--faint)', marginBottom: 6, fontWeight: 600 }}>{label}</p>
      {payload.map((p: any) => (
        <p key={p.dataKey} style={{ color: p.color, margin: '2px 0' }}>
          {p.dataKey === 'critical' ? 'Critique' : p.dataKey === 'high' ? 'Élevé' : 'Moyen'} : <strong>{p.value}</strong>
        </p>
      ))}
    </div>
  );
}

// ─── Page principale ─────────────────────────────────────────────────────────

export default function DashboardPage() {
  const authUser = useAuthStore(s => s.user);
  const isAdmin  = authUser?.role === 'admin';

  const { data, isLoading, refetch, isFetching } = useQuery({
    queryKey: ['dashboard'],
    queryFn: dashboardApi.get,
  });

  if (isLoading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', minHeight: 320 }}>
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-500 border-t-transparent" />
      </div>
    );
  }

  const stats          = data?.stats ?? {};
  const vulnBySeverity = data?.vuln_by_severity ?? {};
  const recentAudits   = data?.recent_audits ?? [];
  const vulnTrends     = data?.vuln_trends ?? [];
  // Scope envoyé par le backend : "own" (auditeur) | "global" (admin)
  const scope          = (data as any)?.scope ?? (isAdmin ? 'global' : 'own');

  const avgScore: number | null = stats.average_hardening_score ?? null;
  const totalVulns = Object.values(vulnBySeverity as Record<string, number>).reduce((a, b) => a + b, 0);

  const trendData = (vulnTrends as any[]).map((t: any) => ({
    date:     new Date(t.date).toLocaleDateString('fr', { weekday: 'short' }),
    critical: t.critical ?? 0,
    high:     t.high ?? 0,
    medium:   t.medium ?? 0,
  }));

  const scoreTrend = avgScore !== null && avgScore > 60
    ? 'up' : avgScore !== null && avgScore < 40
    ? 'down' : 'flat';

  // Libellés contextuels
  const auditsTitle  = scope === 'global' ? 'Derniers audits (tous comptes)' : 'Vos derniers audits';
  const scoreTitle   = scope === 'global' ? 'Score moyen global' : 'Votre score moyen';
  const auditsCount  = scope === 'global' ? 'Audits complétés (global)' : 'Vos audits complétés';
  const postureTitle = scope === 'global' ? 'Posture globale de sécurité' : 'Votre posture de sécurité';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>

      {/* ── Header ── */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <div className="eyebrow">Tableau de bord</div>
          <h1 style={{ fontSize: 22, fontWeight: 700, fontFamily: 'var(--font-display)', color: 'var(--text)', marginTop: 4 }}>
            {postureTitle}
          </h1>
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: 6, marginTop: 6,
            fontSize: 11, fontWeight: 600, letterSpacing: '0.06em',
            padding: '3px 10px', borderRadius: 2,
            background: scope === 'global' ? '#a855f718' : 'var(--lime-dim)',
            color: scope === 'global' ? '#a855f7' : 'var(--lime)',
            border: `1px solid ${scope === 'global' ? '#a855f740' : 'var(--lime)'}40`,
          }}>
            {scope === 'global' ? '⬡ ADMIN · Vue globale' : '◈ Données personnelles uniquement'}
          </div>
        </div>
        <button
          onClick={() => refetch()}
          style={{
            display: 'flex', alignItems: 'center', gap: 6,
            padding: '7px 14px', background: 'transparent',
            border: '1px solid var(--line)', cursor: 'pointer',
            fontSize: 12, fontWeight: 600, fontFamily: 'var(--font-display)',
            color: 'var(--dim)', letterSpacing: '0.05em',
            transition: 'color 0.15s, border-color 0.15s',
          }}
          onMouseEnter={e => {
            (e.currentTarget as HTMLButtonElement).style.color = 'var(--lime)';
            (e.currentTarget as HTMLButtonElement).style.borderColor = 'var(--lime)';
          }}
          onMouseLeave={e => {
            (e.currentTarget as HTMLButtonElement).style.color = 'var(--dim)';
            (e.currentTarget as HTMLButtonElement).style.borderColor = 'var(--line)';
          }}
        >
          <RefreshCw style={{ width: 13, height: 13 }} className={isFetching ? 'animate-spin' : ''} />
          Actualiser
        </button>
      </div>

      {/* ── Bloc posture ── */}
      <div className="card" style={{ display: 'flex', gap: 32, alignItems: 'center', flexWrap: 'wrap' }}>
        {/* Jauge */}
        <ScoreRing score={avgScore} size={120} />

        {/* Résumé texte */}
        <div style={{ flex: 1, minWidth: 200 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
            <span style={{ fontFamily: 'var(--font-display)', fontSize: 20, fontWeight: 700, color: 'var(--text)' }}>
              {avgScore !== null ? `${scoreTitle} : ${avgScore}/100` : scope === 'own' ? 'Aucun audit à votre compte' : 'Aucun audit'}
            </span>
            {avgScore !== null && scoreTrend !== 'flat' && (
              <span style={{
                display: 'inline-flex', alignItems: 'center', gap: 3,
                fontSize: 11, fontWeight: 600, padding: '2px 8px', borderRadius: 2,
                background: scoreTrend === 'up' ? '#3b82f620' : '#ef444420',
                color: scoreTrend === 'up' ? '#3b82f6' : '#ef4444',
              }}>
                {scoreTrend === 'up'
                  ? <ArrowUpRight style={{ width: 12, height: 12 }} />
                  : <ArrowDownRight style={{ width: 12, height: 12 }} />}
                {scoreTrend === 'up' ? 'En progression' : 'En baisse'}
              </span>
            )}
          </div>
          <p style={{ fontSize: 13, color: 'var(--dim)', marginTop: 6 }}>
            {stats.total_assets ?? 0} systèmes (global) ·{' '}
            {stats.open_vulnerabilities ?? 0} vulnérabilités ouvertes (global) ·{' '}
            {stats.completed_hardening_sessions ?? 0} {scope === 'own' ? 'vos audits complétés' : 'audits complétés (tous comptes)'}
          </p>
        </div>

        {/* Compteurs par sévérité */}
        <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
          {(['critical', 'high', 'medium', 'low'] as const).map(sev => {
            const count = (vulnBySeverity as Record<string, number>)[sev] ?? 0;
            const color = SEV_COLOR[sev];
            return (
              <div key={sev} style={{ textAlign: 'center', minWidth: 52 }}>
                <div style={{ fontFamily: 'var(--font-mono)', fontSize: 24, fontWeight: 700, color: count > 0 ? color : 'var(--faint)', lineHeight: 1 }}>
                  {count}
                </div>
                <div style={{ fontSize: 10, fontWeight: 600, letterSpacing: '0.08em', textTransform: 'uppercase', color: count > 0 ? color : 'var(--faint)', marginTop: 4 }}>
                  {SEV_LABEL[sev]}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* ── Stat cards ── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 16 }}>
        <StatCard
          label="Systèmes"
          value={stats.total_assets ?? 0}
          sub={`${stats.active_assets ?? 0} actifs`}
          icon={Server}
          accent="#3b82f6"
          to="/assets"
        />
        <StatCard
          label="Vulnérabilités"
          value={stats.open_vulnerabilities ?? 0}
          sub={`dont ${stats.critical_vulnerabilities ?? 0} critiques`}
          icon={Shield}
          accent="#ef4444"
          to="/vulnerabilities"
        />
        <StatCard
          label={auditsCount}
          value={stats.completed_hardening_sessions ?? 0}
          sub={stats.running_hardening_sessions ? `${stats.running_hardening_sessions} en cours` : 'Aucun en cours'}
          icon={ShieldCheck}
          accent="#3b82f6"
          to="/hardening"
        />
        <StatCard
          label={scoreTitle}
          value={avgScore !== null ? `${avgScore}/100` : '—'}
          sub={avgScore !== null ? `Grade ${scoreToGrade(avgScore)}` : scope === 'own' ? 'Importez un rapport XML' : 'Aucun audit'}
          icon={TrendingUp}
          accent={avgScore !== null ? (GRADE_META[scoreToGrade(avgScore)]?.color ?? '#64748b') : '#64748b'}
        />
      </div>

      {/* ── Charts row ── */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>

        {/* Tendance vulnérabilités */}
        <div className="card">
          <div style={{ marginBottom: 20, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <div className="eyebrow" style={{ marginBottom: 4 }}>Analyse temporelle</div>
              <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 600, fontSize: 15, color: 'var(--text)' }}>
                Tendance — 7 derniers jours
              </h2>
            </div>
            <Activity style={{ width: 16, height: 16, color: 'var(--faint)' }} />
          </div>
          {trendData.length > 0 ? (
            <div style={{ height: 200 }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={trendData} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--line)" vertical={false} />
                  <XAxis dataKey="date" tick={{ fontSize: 11, fill: 'var(--faint)', fontFamily: 'var(--font-body)' }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fontSize: 11, fill: 'var(--faint)', fontFamily: 'var(--font-mono)' }} axisLine={false} tickLine={false} />
                  <Tooltip content={<ChartTooltip />} />
                  <Line type="monotone" dataKey="critical" stroke={SEV_COLOR.critical} strokeWidth={2} dot={false} activeDot={{ r: 4, strokeWidth: 0 }} />
                  <Line type="monotone" dataKey="high"     stroke={SEV_COLOR.high}     strokeWidth={2} dot={false} activeDot={{ r: 4, strokeWidth: 0 }} />
                  <Line type="monotone" dataKey="medium"   stroke={SEV_COLOR.medium}   strokeWidth={2} dot={false} activeDot={{ r: 4, strokeWidth: 0 }} strokeDasharray="4 2" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div style={{ height: 200, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 8 }}>
              <Activity style={{ width: 28, height: 28, color: 'var(--line)' }} />
              <span style={{ fontSize: 13, color: 'var(--faint)' }}>Pas encore de données de tendance</span>
            </div>
          )}
          {/* Légende */}
          <div style={{ display: 'flex', gap: 16, marginTop: 12, justifyContent: 'center' }}>
            {(['critical', 'high', 'medium'] as const).map(sev => (
              <div key={sev} style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 11, color: 'var(--dim)' }}>
                <div style={{ width: 20, height: 2, background: SEV_COLOR[sev] }} />
                {SEV_LABEL[sev]}
              </div>
            ))}
          </div>
        </div>

        {/* Répartition par sévérité */}
        <div className="card">
          <div style={{ marginBottom: 20, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <div className="eyebrow" style={{ marginBottom: 4 }}>Distribution</div>
              <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 600, fontSize: 15, color: 'var(--text)' }}>
                Vulnérabilités par sévérité
              </h2>
            </div>
            <AlertTriangle style={{ width: 16, height: 16, color: 'var(--faint)' }} />
          </div>

          {totalVulns > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
              {/* Total pill */}
              <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
                <span style={{ fontFamily: 'var(--font-mono)', fontSize: 32, fontWeight: 700, color: 'var(--text)' }}>
                  {totalVulns}
                </span>
                <span style={{ fontSize: 13, color: 'var(--faint)' }}>vulnérabilités ouvertes</span>
              </div>
              {/* Barres */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                {(['critical', 'high', 'medium', 'low'] as const).map(sev => (
                  <SeverityBar
                    key={sev}
                    sev={sev}
                    count={(vulnBySeverity as Record<string, number>)[sev] ?? 0}
                    total={totalVulns}
                  />
                ))}
              </div>
              {/* Barre empilée */}
              <div style={{ height: 6, display: 'flex', gap: 2, marginTop: 4 }}>
                {(['critical', 'high', 'medium', 'low'] as const).map(sev => {
                  const count = (vulnBySeverity as Record<string, number>)[sev] ?? 0;
                  const pct = totalVulns > 0 ? (count / totalVulns) * 100 : 0;
                  return pct > 0 ? (
                    <div
                      key={sev}
                      title={`${SEV_LABEL[sev]}: ${count}`}
                      style={{ width: `${pct}%`, height: '100%', background: SEV_COLOR[sev], borderRadius: 1, transition: 'width 1s ease' }}
                    />
                  ) : null;
                })}
              </div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 10, height: 200 }}>
              <div style={{ width: 48, height: 48, borderRadius: 3, background: 'var(--panel-hi)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <ShieldCheck style={{ width: 24, height: 24, color: '#3b82f6' }} />
              </div>
              <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--text)' }}>Aucune vulnérabilité ouverte</span>
              <span style={{ fontSize: 12, color: 'var(--faint)' }}>Excellent état de sécurité</span>
            </div>
          )}
        </div>
      </div>

      {/* ── Derniers audits ── */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        {/* Header table */}
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '16px 24px', borderBottom: '1px solid var(--line)',
        }}>
          <div>
            <div className="eyebrow" style={{ marginBottom: 4 }}>Historique</div>
            <h2 style={{ fontFamily: 'var(--font-display)', fontWeight: 600, fontSize: 15, color: 'var(--text)' }}>
              {auditsTitle}
            </h2>
          </div>
          <Link
            to="/hardening"
            style={{
              display: 'flex', alignItems: 'center', gap: 4,
              fontSize: 12, fontWeight: 600, color: 'var(--lime)',
              fontFamily: 'var(--font-display)', letterSpacing: '0.05em',
            }}
          >
            Voir tout <ArrowUpRight style={{ width: 13, height: 13 }} />
          </Link>
        </div>

        {recentAudits.length > 0 ? (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--line)' }}>
                  {['Cible', 'Hôte', 'Statut', 'Grade', 'Score', 'Findings', 'Date'].map(h => (
                    <th key={h} style={{
                      padding: '10px 24px', textAlign: 'left',
                      fontSize: 11, fontWeight: 600, letterSpacing: '0.07em',
                      textTransform: 'uppercase', color: 'var(--faint)',
                      fontFamily: 'var(--font-display)', whiteSpace: 'nowrap',
                    }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {(recentAudits as any[]).map((audit: any, i: number) => (
                  <tr
                    key={audit.id}
                    style={{
                      borderBottom: i < recentAudits.length - 1 ? '1px solid var(--line)' : 'none',
                      transition: 'background 0.1s',
                    }}
                    onMouseEnter={e => (e.currentTarget as HTMLTableRowElement).style.background = 'var(--panel-hi)'}
                    onMouseLeave={e => (e.currentTarget as HTMLTableRowElement).style.background = 'transparent'}
                  >
                    <td style={{ padding: '12px 24px', fontWeight: 600, color: 'var(--text)', fontSize: 13, whiteSpace: 'nowrap' }}>
                      {audit.target_name}
                    </td>
                    <td style={{ padding: '12px 24px', fontSize: 12, color: 'var(--faint)', fontFamily: 'var(--font-mono)', whiteSpace: 'nowrap' }}>
                      {audit.target_host}
                    </td>
                    <td style={{ padding: '12px 24px', whiteSpace: 'nowrap' }}>
                      <StatusBadge status={audit.status} />
                    </td>
                    <td style={{ padding: '12px 24px', whiteSpace: 'nowrap' }}>
                      <GradeBadge grade={audit.grade} />
                    </td>
                    <td style={{ padding: '12px 24px', fontFamily: 'var(--font-mono)', fontSize: 13, fontWeight: 700, color: 'var(--text)', whiteSpace: 'nowrap' }}>
                      {audit.score != null ? `${audit.score}/100` : '—'}
                    </td>
                    <td style={{ padding: '12px 24px', whiteSpace: 'nowrap' }}>
                      {/* Mini sévérités */}
                      {audit.findings_summary ? (
                        <div style={{ display: 'flex', gap: 6 }}>
                          {(['critical', 'high', 'medium'] as const).map(sev => {
                            const n = (audit.findings_summary as Record<string, number>)[sev.toUpperCase()] ?? 0;
                            return n > 0 ? (
                              <span key={sev} style={{
                                fontFamily: 'var(--font-mono)', fontSize: 11, fontWeight: 700,
                                padding: '1px 6px', borderRadius: 2,
                                background: SEV_COLOR[sev] + '18',
                                color: SEV_COLOR[sev],
                              }}>
                                {n}
                              </span>
                            ) : null;
                          })}
                          {!['critical','high','medium'].some(s => (audit.findings_summary as any)[(s.charAt(0).toUpperCase()+s.slice(1)).toUpperCase()] > 0) && (
                            <span style={{ fontSize: 12, color: '#3b82f6', fontWeight: 600 }}>✓ Propre</span>
                          )}
                        </div>
                      ) : <span style={{ color: 'var(--faint)', fontSize: 12 }}>—</span>}
                    </td>
                    <td style={{ padding: '12px 24px', fontSize: 12, color: 'var(--faint)', whiteSpace: 'nowrap' }}>
                      {audit.completed_at
                        ? new Date(audit.completed_at).toLocaleDateString('fr', { day: '2-digit', month: 'short', year: 'numeric' })
                        : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{ padding: '48px 24px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12 }}>
            <div style={{ width: 52, height: 52, borderRadius: 3, background: 'var(--panel-hi)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <ShieldCheck style={{ width: 26, height: 26, color: 'var(--faint)' }} />
            </div>
            <p style={{ fontSize: 14, fontWeight: 600, color: 'var(--text)' }}>
              {scope === 'own' ? 'Aucun audit associé à votre compte' : 'Aucun audit effectué'}
            </p>
            <p style={{ fontSize: 12, color: 'var(--faint)', textAlign: 'center', maxWidth: 300 }}>
              {scope === 'own'
                ? 'Téléchargez l\'agent et importez le rapport XML — il sera lié à votre compte.'
                : 'Aucun utilisateur n\'a encore importé de rapport d\'audit.'}
            </p>
            <Link to="/hardening" style={{
              display: 'inline-flex', alignItems: 'center', gap: 6,
              marginTop: 4, padding: '7px 16px',
              background: 'var(--lime)', color: '#fff',
              fontFamily: 'var(--font-display)', fontSize: 12, fontWeight: 600,
              letterSpacing: '0.06em', textTransform: 'uppercase',
            }}>
              Aller à Hardening <ArrowUpRight style={{ width: 13, height: 13 }} />
            </Link>
          </div>
        )}
      </div>

    </div>
  );
}
