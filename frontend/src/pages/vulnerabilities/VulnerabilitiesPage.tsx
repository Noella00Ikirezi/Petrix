import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search, Shield, AlertTriangle, ExternalLink, ChevronDown, ChevronUp, RefreshCw } from 'lucide-react';
import { vulnsApi } from '@/api/client';

export default function VulnerabilitiesPage() {
  const [search, setSearch] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [activeTab, setActiveTab] = useState<'internal' | 'feed'>('internal');

  const { data, isLoading } = useQuery({
    queryKey: ['vulnerabilities', search, severityFilter, statusFilter],
    queryFn: () => vulnsApi.list({ search: search || undefined, severity: severityFilter || undefined, status: statusFilter || undefined }),
  });

  const vulns = data?.items || [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Vulnérabilités</h1>
        <p className="text-gray-600 dark:text-gray-400">Suivi des vulnérabilités détectées et veille CVE</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 rounded-lg border border-gray-200 bg-gray-50 p-1 dark:border-gray-700 dark:bg-gray-900 w-fit">
        <button
          onClick={() => setActiveTab('internal')}
          className={`rounded-md px-4 py-1.5 text-sm font-medium transition-colors ${
            activeTab === 'internal'
              ? 'bg-white shadow text-gray-900 dark:bg-gray-800 dark:text-white'
              : 'text-gray-500 hover:text-gray-700 dark:text-gray-400'
          }`}
        >
          Vulnérabilités détectées
        </button>
        <button
          onClick={() => setActiveTab('feed')}
          className={`rounded-md px-4 py-1.5 text-sm font-medium transition-colors ${
            activeTab === 'feed'
              ? 'bg-white shadow text-gray-900 dark:bg-gray-800 dark:text-white'
              : 'text-gray-500 hover:text-gray-700 dark:text-gray-400'
          }`}
        >
          Veille CVE (NVD)
        </button>
      </div>

      {activeTab === 'internal' && (
        <>
          <div className="flex flex-wrap gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
              <input type="text" placeholder="Rechercher..." value={search}
                onChange={(e) => setSearch(e.target.value)} className="input pl-10" />
            </div>
            <select value={severityFilter} onChange={(e) => setSeverityFilter(e.target.value)} className="input w-44">
              <option value="">Toutes les sévérités</option>
              <option value="critical">Critique</option>
              <option value="high">Élevé</option>
              <option value="medium">Moyen</option>
              <option value="low">Faible</option>
              <option value="info">Info</option>
            </select>
            <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} className="input w-44">
              <option value="">Tous les statuts</option>
              <option value="open">Ouvert</option>
              <option value="in_progress">En cours</option>
              <option value="resolved">Résolu</option>
              <option value="accepted">Accepté</option>
              <option value="false_positive">Faux positif</option>
            </select>
          </div>

          <div className="card overflow-hidden p-0">
            {isLoading ? (
              <div className="flex h-64 items-center justify-center">
                <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-500 border-t-transparent" />
              </div>
            ) : vulns.length === 0 ? (
              <div className="flex h-64 flex-col items-center justify-center text-gray-500">
                <Shield className="mb-2 h-12 w-12" />
                <p>Aucune vulnérabilité — lancez un scan pour en découvrir</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-200 dark:divide-gray-700">
                {vulns.map((vuln: Vuln) => (
                  <VulnRow key={vuln.id} vuln={vuln} />
                ))}
              </div>
            )}
          </div>
        </>
      )}

      {activeTab === 'feed' && <CveFeed />}
    </div>
  );
}

function VulnRow({ vuln }: { vuln: Vuln }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3 flex-1 min-w-0">
          <AlertTriangle className={`mt-0.5 h-5 w-5 shrink-0 ${getSeverityColor(vuln.severity)}`} />
          <div className="flex-1 min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <SeverityBadge severity={vuln.severity} />
              <StatusBadge status={vuln.status} />
              {vuln.cve_ids?.length > 0 && (
                <span className="font-mono text-xs text-primary-600 dark:text-primary-400">{vuln.cve_ids[0]}</span>
              )}
              {vuln.cvss_score && (
                <span className="text-xs font-medium text-gray-500">CVSS {vuln.cvss_score.toFixed(1)}</span>
              )}
            </div>
            <p className="mt-1 font-medium text-gray-900 dark:text-white">{vuln.title}</p>
            {expanded && (
              <div className="mt-3 space-y-2 text-sm text-gray-600 dark:text-gray-400">
                {vuln.description && <p>{vuln.description}</p>}
                <p className="text-xs text-gray-400">Découverte le {new Date(vuln.discovered_at).toLocaleString('fr')}</p>
                {vuln.cve_ids?.map((cve) => (
                  <a key={cve} href={`https://nvd.nist.gov/vuln/detail/${cve}`} target="_blank" rel="noreferrer"
                    className="flex items-center gap-1 text-xs text-primary-600 hover:underline dark:text-primary-400">
                    <ExternalLink className="h-3 w-3" /> {cve} — NVD
                  </a>
                ))}
              </div>
            )}
          </div>
        </div>
        <button onClick={() => setExpanded(!expanded)}
          className="shrink-0 rounded p-1 text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700">
          {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </button>
      </div>
    </div>
  );
}

interface CveItem {
  id: string;
  published: string;
  lastModified: string;
  description: string;
  cvssScore: number | null;
  cvssVector: string | null;
  severity: string;
  references: string[];
}

function CveFeed() {
  const [keyword, setKeyword] = useState('');
  const [inputVal, setInputVal] = useState('');

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ['cve-feed', keyword],
    queryFn: async (): Promise<CveItem[]> => {
      const params = new URLSearchParams({
        resultsPerPage: '20',
        startIndex: '0',
      });
      if (keyword) params.set('keywordSearch', keyword);
      else params.set('pubStartDate', new Date(Date.now() - 30 * 86400000).toISOString().slice(0, 19) + '.000');

      const res = await fetch(`https://services.nvd.nist.gov/rest/json/cves/2.0?${params}`);
      if (!res.ok) throw new Error('NVD API error');
      const json = await res.json();

      return (json.vulnerabilities || []).map((v: Record<string, unknown>) => {
        const cve = v.cve as Record<string, unknown>;
        const metrics = (cve.metrics as Record<string, unknown>) || {};
        const cvssV31 = ((metrics.cvssMetricV31 as unknown[]) || [])[0] as Record<string, unknown> | undefined;
        const cvssV30 = ((metrics.cvssMetricV30 as unknown[]) || [])[0] as Record<string, unknown> | undefined;
        const cvssV2  = ((metrics.cvssMetricV2  as unknown[]) || [])[0] as Record<string, unknown> | undefined;
        const m = cvssV31 || cvssV30 || cvssV2;
        const cvssData = m ? (m.cvssData as Record<string, unknown>) : null;
        const score = cvssData ? (cvssData.baseScore as number) : null;
        const vector = cvssData ? (cvssData.vectorString as string) : null;
        const sev = (cvssData?.baseSeverity as string || '').toLowerCase() || (score ? (score >= 9 ? 'critical' : score >= 7 ? 'high' : score >= 4 ? 'medium' : 'low') : 'info');
        const descs = (cve.descriptions as { lang: string; value: string }[]) || [];
        const desc = descs.find((d) => d.lang === 'en')?.value || '';
        const refs = ((cve.references as { url: string }[]) || []).slice(0, 3).map((r) => r.url);

        return {
          id: cve.id as string,
          published: cve.published as string,
          lastModified: cve.lastModified as string,
          description: desc,
          cvssScore: score,
          cvssVector: vector,
          severity: sev,
          references: refs,
        };
      });
    },
    staleTime: 5 * 60 * 1000,
  });

  return (
    <div className="space-y-4">
      <div className="flex gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
          <input type="text" placeholder="Rechercher par mot-clé (ex: apache, windows, ssh)..."
            value={inputVal} onChange={(e) => setInputVal(e.target.value)}
            onKeyDown={(e) => { if (e.key === 'Enter') setKeyword(inputVal); }}
            className="input pl-10" />
        </div>
        <button onClick={() => setKeyword(inputVal)} className="btn btn-primary btn-md">Rechercher</button>
        {keyword && (
          <button onClick={() => { setKeyword(''); setInputVal(''); }} className="btn btn-secondary btn-md">Réinitialiser</button>
        )}
        <button onClick={() => refetch()} className="btn btn-secondary btn-md" title="Actualiser">
          <RefreshCw className="h-4 w-4" />
        </button>
      </div>

      <p className="text-sm text-gray-500 dark:text-gray-400">
        {keyword ? `Résultats pour "${keyword}"` : 'CVEs publiées ces 30 derniers jours (source : NVD/NIST)'}
      </p>

      {isLoading && (
        <div className="flex h-48 items-center justify-center">
          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-500 border-t-transparent" />
        </div>
      )}

      {isError && (
        <div className="rounded-md bg-red-50 px-4 py-3 text-sm text-red-700 dark:bg-red-900/20 dark:text-red-400">
          Impossible de joindre l'API NVD. Vérifiez votre connexion internet.
        </div>
      )}

      {data && (
        <div className="space-y-3">
          {data.length === 0 && (
            <div className="py-12 text-center text-gray-500">Aucune CVE trouvée pour cette recherche.</div>
          )}
          {data.map((cve) => (
            <CveCard key={cve.id} cve={cve} />
          ))}
        </div>
      )}
    </div>
  );
}

function CveCard({ cve }: { cve: CveItem }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="card">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <a href={`https://nvd.nist.gov/vuln/detail/${cve.id}`} target="_blank" rel="noreferrer"
              className="font-mono text-sm font-bold text-primary-600 hover:underline dark:text-primary-400">
              {cve.id}
            </a>
            <SeverityBadge severity={cve.severity} />
            {cve.cvssScore && (
              <span className={`text-xs font-bold ${
                cve.cvssScore >= 9 ? 'text-red-600' : cve.cvssScore >= 7 ? 'text-orange-600' : cve.cvssScore >= 4 ? 'text-yellow-600' : 'text-green-600'
              }`}>
                CVSS {cve.cvssScore.toFixed(1)}
              </span>
            )}
            <span className="text-xs text-gray-400">
              Publié le {new Date(cve.published).toLocaleDateString('fr')}
            </span>
            {cve.lastModified !== cve.published && (
              <span className="text-xs text-gray-400">
                · Modifié le {new Date(cve.lastModified).toLocaleDateString('fr')}
              </span>
            )}
          </div>
          <p className={`mt-2 text-sm text-gray-700 dark:text-gray-300 ${!expanded ? 'line-clamp-2' : ''}`}>
            {cve.description}
          </p>
          {expanded && (
            <div className="mt-3 space-y-2">
              {cve.cvssVector && (
                <p className="font-mono text-xs text-gray-400 break-all">{cve.cvssVector}</p>
              )}
              {cve.references.length > 0 && (
                <div className="space-y-1">
                  <p className="text-xs font-medium text-gray-500">Sources :</p>
                  {cve.references.map((ref) => (
                    <a key={ref} href={ref} target="_blank" rel="noreferrer"
                      className="flex items-center gap-1 text-xs text-primary-600 hover:underline dark:text-primary-400 break-all">
                      <ExternalLink className="h-3 w-3 shrink-0" />
                      {ref}
                    </a>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
        <button onClick={() => setExpanded(!expanded)}
          className="shrink-0 rounded p-1 text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700">
          {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </button>
      </div>
    </div>
  );
}

interface Vuln {
  id: string;
  title: string;
  description: string | null;
  severity: string;
  status: string;
  cvss_score: number | null;
  cve_ids: string[];
  discovered_at: string;
}

function getSeverityColor(severity: string): string {
  const colors: Record<string, string> = {
    critical: 'text-red-500', high: 'text-orange-500', medium: 'text-yellow-500',
    low: 'text-green-500', info: 'text-gray-500',
  };
  return colors[severity] || 'text-gray-500';
}

function SeverityBadge({ severity }: { severity: string }) {
  const styles: Record<string, string> = {
    critical: 'badge-critical', high: 'badge-high', medium: 'badge-medium', low: 'badge-low', info: 'badge-info',
  };
  const labels: Record<string, string> = { critical: 'Critique', high: 'Élevé', medium: 'Moyen', low: 'Faible', info: 'Info' };
  return <span className={`badge ${styles[severity] || ''}`}>{labels[severity] || severity}</span>;
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    open: 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300',
    in_progress: 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300',
    resolved: 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300',
    accepted: 'bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300',
    false_positive: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
  };
  const labels: Record<string, string> = {
    open: 'Ouvert', in_progress: 'En cours', resolved: 'Résolu', accepted: 'Accepté', false_positive: 'Faux positif',
  };
  return <span className={`badge ${styles[status] || ''}`}>{labels[status] || status}</span>;
}
