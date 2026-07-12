import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Search, Shield, AlertTriangle, ExternalLink,
  ChevronDown, ChevronUp, RefreshCw, Radio,
  AlertOctagon, Info, Bell, FileText, X,
  Monitor, Wrench, BookOpen, AlertTriangle as TriangleAlert, Tag, Link2,
} from 'lucide-react';
import { vulnsApi, feedApi } from '@/api/client';

// ─── Types ────────────────────────────────────────────────────────────────────

interface Vuln {
  id: string; title: string; description: string | null;
  severity: string; status: string; cvss_score: number | null;
  cve_ids: string[]; discovered_at: string;
}

interface CertFrItem {
  cert_id: string; title: string; link: string;
  published: string; summary: string; severity: string;
  cves: string[]; feed_type: string;
}

interface Fiche {
  cert_id: string; url: string; feed_type: string;
  title: string; reference: string;
  published: string; updated: string; source: string;
  severity: string;
  risks: string[]; affected_systems: string[];
  summary: string; workaround: string; solution: string;
  cves: string[]; references: string[];
}

// ─── Severity config ───────────────────────────────────────────────────────────

const SEV: Record<string, { border: string; bg: string; badge: string; icon: string; label: string; bannerBg: string }> = {
  CRITICAL: { border: 'border-l-red-500',    bg: 'bg-red-50 dark:bg-red-950/20',    badge: 'bg-red-600 text-white',    icon: 'text-red-500',    label: 'Critique', bannerBg: 'from-red-700 to-red-900' },
  HIGH:     { border: 'border-l-orange-400', bg: 'bg-orange-50 dark:bg-orange-950/20', badge: 'bg-orange-500 text-white', icon: 'text-orange-500', label: 'Élevé',    bannerBg: 'from-orange-600 to-orange-800' },
  MEDIUM:   { border: 'border-l-yellow-400', bg: 'bg-yellow-50 dark:bg-yellow-950/10', badge: 'bg-yellow-500 text-white', icon: 'text-yellow-600', label: 'Moyen',    bannerBg: 'from-yellow-600 to-yellow-800' },
  LOW:      { border: 'border-l-green-400',  bg: 'bg-green-50 dark:bg-green-950/10',  badge: 'bg-green-600 text-white',  icon: 'text-green-500',  label: 'Faible',   bannerBg: 'from-green-600 to-green-800' },
};

function formatDate(raw: string) {
  if (!raw) return '';
  try { return new Date(raw).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' }); }
  catch { return raw; }
}

function cleanTitle(t: string) {
  return t.replace(/^\[MàJ\]\s*/i, '').trim();
}

function isRecent(d: string, days = 60) {
  try { return (Date.now() - new Date(d).getTime()) < days * 86400000; }
  catch { return false; }
}

// ─── Fiche Drawer ──────────────────────────────────────────────────────────────

function FicheDrawer({ certId, feedType, onClose }: { certId: string; feedType: string; onClose: () => void }) {
  const { data: fiche, isLoading, isError } = useQuery<Fiche>({
    queryKey: ['fiche', certId],
    queryFn: () => feedApi.certFrFiche(certId, feedType),
    staleTime: 30 * 60 * 1000,
  });

  const sev = SEV[fiche?.severity ?? 'MEDIUM'] ?? SEV.MEDIUM;

  return (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 z-40 bg-black/40 backdrop-blur-sm" onClick={onClose} />

      {/* Drawer */}
      <div className="fixed inset-y-0 right-0 z-50 flex w-full max-w-2xl flex-col overflow-hidden bg-white shadow-2xl dark:bg-gray-900">

        {/* Banner */}
        {fiche ? (
          <div className={`bg-gradient-to-br ${sev.bannerBg} px-6 py-5 text-white`}>
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-2">
                  <span className="rounded bg-white/20 px-2 py-0.5 font-mono text-sm font-bold">{fiche.reference}</span>
                  <span className="rounded bg-white/20 px-2 py-0.5 text-xs">{sev.label.toUpperCase()}</span>
                  {fiche.updated && fiche.updated !== fiche.published && (
                    <span className="rounded bg-white/15 px-2 py-0.5 text-xs">Mis à jour</span>
                  )}
                </div>
                <h2 className="text-lg font-bold leading-snug">{cleanTitle(fiche.title)}</h2>
                <div className="mt-2 flex flex-wrap items-center gap-3 text-sm text-white/80">
                  {fiche.published && <span>Publié le {fiche.published}</span>}
                  {fiche.updated && fiche.updated !== fiche.published && (
                    <span className="text-white/60">· Mis à jour le {fiche.updated}</span>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <a href={fiche.url} target="_blank" rel="noreferrer"
                  className="flex items-center gap-1.5 rounded-lg bg-white/20 px-3 py-1.5 text-xs font-medium hover:bg-white/30 transition-colors">
                  <ExternalLink className="h-3.5 w-3.5" /> CERT-FR
                </a>
                <button onClick={onClose}
                  className="rounded-lg bg-white/20 p-1.5 hover:bg-white/30 transition-colors">
                  <X className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-between bg-gray-800 px-6 py-4">
            <span className="font-mono text-sm font-bold text-white">{certId}</span>
            <button onClick={onClose} className="rounded p-1.5 text-gray-400 hover:text-white">
              <X className="h-4 w-4" />
            </button>
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-y-auto">
          {isLoading && (
            <div className="flex h-48 flex-col items-center justify-center gap-3 text-gray-400">
              <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-200 border-t-primary-600" />
              <p className="text-sm">Chargement de la fiche CERT-FR…</p>
            </div>
          )}
          {isError && (
            <div className="m-6 rounded-xl border border-red-200 bg-red-50 p-5 dark:border-red-800 dark:bg-red-950/20">
              <p className="font-semibold text-red-700 dark:text-red-400">Impossible de charger la fiche</p>
              <p className="mt-1 text-sm text-red-600 dark:text-red-300">Vérifiez l'identifiant CERT-FR ou réessayez.</p>
            </div>
          )}

          {fiche && (
            <div className="space-y-1 p-6">

              {/* Risques */}
              {fiche.risks.length > 0 && (
                <FicheSection icon={TriangleAlert} title="Risque(s)" iconClass="text-red-500">
                  <div className="flex flex-wrap gap-2">
                    {fiche.risks.map((r, i) => (
                      <span key={i} className="flex items-center gap-1.5 rounded-full border border-red-200 bg-red-50 px-3 py-1 text-sm font-medium text-red-700 dark:border-red-800 dark:bg-red-950/30 dark:text-red-300">
                        <AlertTriangle className="h-3.5 w-3.5 shrink-0" /> {r}
                      </span>
                    ))}
                  </div>
                </FicheSection>
              )}

              {/* Systèmes affectés */}
              {fiche.affected_systems.length > 0 && (
                <FicheSection icon={Monitor} title="Systèmes affectés" iconClass="text-orange-500">
                  <div className="flex flex-wrap gap-1.5">
                    {fiche.affected_systems.map((s, i) => (
                      <span key={i} className="rounded-md bg-gray-100 px-2.5 py-1 text-sm text-gray-700 dark:bg-gray-800 dark:text-gray-300">
                        {s}
                      </span>
                    ))}
                  </div>
                </FicheSection>
              )}

              {/* Résumé */}
              {fiche.summary && (
                <FicheSection icon={FileText} title="Résumé" iconClass="text-blue-500">
                  <p className="whitespace-pre-line text-sm leading-relaxed text-gray-700 dark:text-gray-300">
                    {fiche.summary}
                  </p>
                </FicheSection>
              )}

              {/* Solution */}
              {fiche.solution && (
                <FicheSection icon={Wrench} title="Solution" iconClass="text-green-500">
                  <div className="mb-2 flex items-center gap-2">
                    <span className="rounded-full bg-green-100 px-2.5 py-0.5 text-xs font-semibold text-green-700 dark:bg-green-900/40 dark:text-green-400">
                      ✓ Correctif disponible
                    </span>
                  </div>
                  <p className="whitespace-pre-line text-sm leading-relaxed text-gray-700 dark:text-gray-300">
                    {fiche.solution}
                  </p>
                </FicheSection>
              )}

              {/* Contournement */}
              {fiche.workaround && fiche.workaround.length > 10 && (
                <FicheSection icon={Shield} title="Contournement provisoire" iconClass="text-yellow-500">
                  <p className="whitespace-pre-line text-sm leading-relaxed text-gray-700 dark:text-gray-300">
                    {fiche.workaround}
                  </p>
                </FicheSection>
              )}

              {/* CVE */}
              {fiche.cves.length > 0 && (
                <FicheSection icon={Tag} title="CVE associées" iconClass="text-purple-500">
                  <div className="flex flex-wrap gap-2">
                    {fiche.cves.map(cve => (
                      <a key={cve}
                        href={`https://nvd.nist.gov/vuln/detail/${cve}`}
                        target="_blank" rel="noreferrer"
                        className="flex items-center gap-1 rounded-md bg-purple-50 px-3 py-1.5 font-mono text-sm font-medium text-purple-700 hover:bg-purple-100 dark:bg-purple-950/30 dark:text-purple-300 dark:hover:bg-purple-950/50">
                        <ExternalLink className="h-3 w-3" /> {cve}
                      </a>
                    ))}
                  </div>
                </FicheSection>
              )}

              {/* Références */}
              {fiche.references.length > 0 && (
                <FicheSection icon={Link2} title="Documentation" iconClass="text-gray-400">
                  <ul className="space-y-1.5">
                    {fiche.references.map((ref, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-gray-600 dark:text-gray-400">
                        <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-gray-300 dark:bg-gray-600" />
                        {ref}
                      </li>
                    ))}
                  </ul>
                </FicheSection>
              )}

              {/* Source */}
              {fiche.source && (
                <p className="border-t border-gray-100 pt-4 text-xs text-gray-400 dark:border-gray-800">
                  Source : {fiche.source}
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </>
  );
}

function FicheSection({ icon: Icon, title, iconClass, children }: {
  icon: React.ElementType; title: string; iconClass: string; children: React.ReactNode;
}) {
  return (
    <div className="rounded-xl border border-gray-100 bg-gray-50/50 p-4 dark:border-gray-800 dark:bg-gray-800/30">
      <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
        <Icon className={`h-4 w-4 ${iconClass}`} />
        {title}
      </h3>
      {children}
    </div>
  );
}

// ─── Feed tabs ────────────────────────────────────────────────────────────────

const FEED_TABS = [
  { id: 'alerte',    label: 'Alertes',      icon: AlertOctagon, desc: 'Vulnérabilités critiques — action immédiate' },
  { id: 'avis',      label: 'Avis',         icon: FileText,     desc: 'Avis de sécurité — recommandations' },
  { id: 'dur',       label: 'Durcissement', icon: Bell,         desc: 'Guides de durcissement ANSSI' },
  { id: 'actualite', label: 'Actualités',   icon: Radio,        desc: 'Actualités CERT-FR' },
] as const;
type FeedType = typeof FEED_TABS[number]['id'];

// ─── CERT-FR Feed ─────────────────────────────────────────────────────────────

function CertFrFeed() {
  const [feedType, setFeedType]           = useState<FeedType>('alerte');
  const [severityFilter, setSeverityFilter] = useState('');
  const [expanded, setExpanded]           = useState<string | null>(null);
  const [openFiche, setOpenFiche]         = useState<{ certId: string; feedType: string } | null>(null);

  const { data, isLoading, isError, refetch, isFetching, dataUpdatedAt } = useQuery({
    queryKey: ['cert-fr', feedType],
    queryFn:  () => feedApi.certFr(feedType),
    staleTime: 10 * 60 * 1000,
    retry: 2,
  });

  const items: CertFrItem[] = (data?.items || []).sort(
    (a: CertFrItem, b: CertFrItem) => new Date(b.published).getTime() - new Date(a.published).getTime()
  );
  const filtered = severityFilter ? items.filter(i => i.severity === severityFilter) : items;
  const critCount = items.filter(i => i.severity === 'CRITICAL').length;

  return (
    <div className="space-y-5">
      {/* Header band */}
      <div className="flex items-center justify-between rounded-xl border border-blue-200 bg-gradient-to-r from-blue-50 to-indigo-50 px-5 py-3 dark:border-blue-800 dark:from-blue-950/30 dark:to-indigo-950/30">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-blue-600">
            <Radio className="h-4 w-4 text-white" />
          </div>
          <div>
            <p className="text-sm font-semibold text-blue-900 dark:text-blue-100">Veille CERT-FR — ANSSI</p>
            <p className="text-xs text-blue-600 dark:text-blue-400">Flux officiel · Proxy backend · Pas de restriction réseau</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {dataUpdatedAt > 0 && (
            <span className="text-xs text-blue-500">{formatDate(new Date(dataUpdatedAt).toISOString())}</span>
          )}
          <a href={`https://www.cert.ssi.gouv.fr/${feedType}/`} target="_blank" rel="noreferrer"
            className="flex items-center gap-1 rounded-md bg-white px-3 py-1.5 text-xs font-medium text-blue-700 shadow-sm hover:bg-blue-50 dark:bg-gray-800 dark:text-blue-300">
            <ExternalLink className="h-3 w-3" /> cert.ssi.gouv.fr
          </a>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex rounded-lg border border-gray-200 bg-gray-50 p-0.5 dark:border-gray-700 dark:bg-gray-900">
          {FEED_TABS.map(tab => (
            <button key={tab.id} onClick={() => { setFeedType(tab.id); setExpanded(null); }}
              className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-all ${
                feedType === tab.id
                  ? 'bg-white shadow text-gray-900 dark:bg-gray-800 dark:text-white'
                  : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
              }`}>
              <tab.icon className="h-3.5 w-3.5" />
              {tab.label}
              {tab.id === 'alerte' && critCount > 0 && (
                <span className="ml-0.5 rounded-full bg-red-500 px-1.5 text-xs text-white">{critCount}</span>
              )}
            </button>
          ))}
        </div>
        <div className="flex gap-1 ml-auto">
          {(['', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'] as const).map(s => {
            const cfg = s ? SEV[s] : null;
            return (
              <button key={s} onClick={() => setSeverityFilter(s)}
                className={`rounded-full px-2.5 py-1 text-xs font-medium transition-all ${
                  severityFilter === s
                    ? cfg ? cfg.badge : 'bg-gray-800 text-white dark:bg-gray-200 dark:text-gray-800'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-300'
                }`}>
                {s ? SEV[s].label : 'Tout'}
              </button>
            );
          })}
          <button onClick={() => refetch()}
            className="ml-1 rounded-full p-1.5 text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800" title="Actualiser">
            <RefreshCw className={`h-3.5 w-3.5 ${isFetching ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Stats */}
      {!isLoading && !isError && items.length > 0 && (
        <div className="flex flex-wrap gap-4 text-xs text-gray-500 dark:text-gray-400">
          <span>{filtered.length} résultat{filtered.length > 1 ? 's' : ''}</span>
          {(['CRITICAL', 'HIGH', 'MEDIUM'] as const).map(s => {
            const n = items.filter(i => i.severity === s).length;
            return n > 0 ? (
              <span key={s} className="flex items-center gap-1">
                <span className={`h-2 w-2 rounded-full ${s === 'CRITICAL' ? 'bg-red-500' : s === 'HIGH' ? 'bg-orange-400' : 'bg-yellow-400'}`} />
                {n} {SEV[s].label.toLowerCase()}{n > 1 ? 's' : ''}
              </span>
            ) : null;
          })}
        </div>
      )}

      {/* States */}
      {isLoading && (
        <div className="flex flex-col items-center gap-3 py-16">
          <div className="h-10 w-10 animate-spin rounded-full border-4 border-blue-200 border-t-blue-600" />
          <p className="text-sm text-gray-500">Récupération du flux CERT-FR…</p>
        </div>
      )}
      {isError && (
        <div className="overflow-hidden rounded-xl border border-red-200 dark:border-red-800">
          <div className="flex items-center gap-3 bg-red-600 px-5 py-3">
            <AlertOctagon className="h-5 w-5 text-white" />
            <p className="text-sm font-semibold text-white">Flux CERT-FR inaccessible</p>
          </div>
          <div className="bg-red-50 px-5 py-4 dark:bg-red-950/20">
            <p className="text-sm text-red-700 dark:text-red-300">
              Le serveur Petrix ne peut momentanément pas joindre cert.ssi.gouv.fr.
            </p>
            <button onClick={() => refetch()}
              className="mt-3 rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700">
              Réessayer
            </button>
          </div>
        </div>
      )}
      {!isLoading && !isError && filtered.length === 0 && (
        <div className="flex flex-col items-center gap-2 py-16 text-gray-400">
          <Info className="h-10 w-10" />
          <p>Aucun résultat pour ce filtre</p>
        </div>
      )}

      {/* Items */}
      {!isLoading && !isError && filtered.length > 0 && (
        <div className="space-y-3">
          {filtered.map(item => {
            const cfg    = SEV[item.severity] ?? SEV.MEDIUM;
            const isExp  = expanded === item.cert_id;
            const title  = cleanTitle(item.title);
            const isMaj  = /^\[M[àa]J\]/i.test(item.title);
            const recent = isRecent(item.published);

            return (
              <div key={item.cert_id}
                className={`overflow-hidden rounded-xl border border-gray-200 border-l-4 transition-shadow hover:shadow-md dark:border-gray-700 ${cfg.border}`}>

                <div
                  className={`flex w-full cursor-pointer items-start gap-4 px-5 py-4 ${isExp ? cfg.bg : 'bg-white dark:bg-gray-800'}`}
                  onClick={() => setExpanded(e => e === item.cert_id ? null : item.cert_id)}>

                  <span className={`mt-0.5 shrink-0 rounded-md px-2 py-0.5 text-xs font-bold ${cfg.badge}`}>
                    {cfg.label.toUpperCase()}
                  </span>

                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-mono text-sm font-bold text-primary-600 dark:text-primary-400">
                        {item.cert_id || '—'}
                      </span>
                      {isMaj && <span className="rounded bg-indigo-100 px-1.5 py-0.5 text-xs font-medium text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300">Mise à jour</span>}
                      {recent && !isMaj && <span className="rounded bg-green-100 px-1.5 py-0.5 text-xs font-medium text-green-700 dark:bg-green-900/40 dark:text-green-300">Récent</span>}
                      {item.cves.slice(0, 2).map(cve => (
                        <span key={cve} className="rounded bg-gray-100 px-1.5 py-0.5 font-mono text-xs text-gray-600 dark:bg-gray-700 dark:text-gray-300">{cve}</span>
                      ))}
                      {item.cves.length > 2 && <span className="text-xs text-gray-400">+{item.cves.length - 2} CVE</span>}
                      <span className="ml-auto text-xs text-gray-400 shrink-0">{formatDate(item.published)}</span>
                    </div>
                    <p className={`mt-1.5 text-sm font-semibold leading-snug text-gray-900 dark:text-white ${isExp ? '' : 'line-clamp-1'}`}>{title}</p>
                    {!isExp && item.summary && (
                      <p className="mt-0.5 text-xs text-gray-500 dark:text-gray-400 line-clamp-1">{item.summary}</p>
                    )}
                  </div>

                  <span className="shrink-0 mt-1 text-gray-400">
                    {isExp ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                  </span>
                </div>

                {/* Expanded */}
                {isExp && (
                  <div className={`px-5 pb-5 pt-3 ${cfg.bg} border-t border-gray-100 dark:border-gray-700`}>
                    <p className="text-sm leading-relaxed text-gray-700 dark:text-gray-200">{item.summary}</p>
                    {item.cves.length > 0 && (
                      <div className="mt-4 flex flex-wrap gap-2">
                        <span className="text-xs font-semibold uppercase tracking-wide text-gray-400">CVE :</span>
                        {item.cves.map(cve => (
                          <a key={cve} href={`https://nvd.nist.gov/vuln/detail/${cve}`} target="_blank" rel="noreferrer"
                            className="flex items-center gap-1 rounded-md bg-white px-2.5 py-1 font-mono text-xs font-medium text-primary-700 shadow-sm hover:shadow-md dark:bg-gray-700 dark:text-primary-300">
                            <ExternalLink className="h-3 w-3" /> {cve}
                          </a>
                        ))}
                      </div>
                    )}
                    <div className="mt-4 flex gap-2">
                      {item.cert_id && item.cert_id.startsWith('CERTFR-') && (
                        <button
                          onClick={e => { e.stopPropagation(); setOpenFiche({ certId: item.cert_id, feedType: item.feed_type }); }}
                          className="flex items-center gap-2 rounded-md bg-primary-600 px-4 py-2 text-xs font-medium text-white hover:bg-primary-700">
                          <BookOpen className="h-3.5 w-3.5" />
                          Voir la fiche complète
                        </button>
                      )}
                      <a href={item.link} target="_blank" rel="noreferrer"
                        className="flex items-center gap-2 rounded-md border border-gray-200 bg-white px-4 py-2 text-xs font-medium text-gray-600 hover:bg-gray-50 dark:bg-gray-800 dark:border-gray-600 dark:text-gray-300">
                        <ExternalLink className="h-3.5 w-3.5" /> CERT-FR
                      </a>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Fiche Drawer */}
      {openFiche && (
        <FicheDrawer
          certId={openFiche.certId}
          feedType={openFiche.feedType}
          onClose={() => setOpenFiche(null)}
        />
      )}
    </div>
  );
}

// ─── Internal Vuln Tab ─────────────────────────────────────────────────────────

const VULN_SEV: Record<string, typeof SEV[keyof typeof SEV]> = {
  critical: SEV.CRITICAL,
  high:     SEV.HIGH,
  medium:   SEV.MEDIUM,
  low:      SEV.LOW,
  info:     { border: 'border-l-gray-300', bg: '', badge: 'bg-gray-400 text-white', icon: 'text-gray-400', label: 'Info', bannerBg: 'from-gray-600 to-gray-800' },
};

function VulnRow({ vuln }: { vuln: Vuln }) {
  const [exp, setExp] = useState(false);
  const cfg = VULN_SEV[vuln.severity] ?? VULN_SEV.info;

  return (
    <div className={`border-l-4 ${cfg.border} px-5 py-4 hover:bg-gray-50 dark:hover:bg-gray-700/30`}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3 flex-1 min-w-0">
          <AlertTriangle className={`mt-0.5 h-5 w-5 shrink-0 ${cfg.icon}`} />
          <div className="flex-1 min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <span className={`rounded-full px-2 py-0.5 text-xs font-bold ${cfg.badge}`}>{cfg.label}</span>
              <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600 dark:bg-gray-700 dark:text-gray-300">
                {{ open:'Ouvert', in_progress:'En cours', resolved:'Résolu', accepted:'Accepté', false_positive:'Faux positif' }[vuln.status] ?? vuln.status}
              </span>
              {vuln.cve_ids?.[0] && <span className="font-mono text-xs font-semibold text-primary-600 dark:text-primary-400">{vuln.cve_ids[0]}</span>}
              {vuln.cvss_score && <span className="text-xs font-bold text-gray-500">CVSS {vuln.cvss_score.toFixed(1)}</span>}
            </div>
            <p className="mt-1 font-semibold text-gray-900 dark:text-white">{vuln.title}</p>
            {exp && (
              <div className="mt-3 space-y-2 text-sm text-gray-600 dark:text-gray-400">
                {vuln.description && <p>{vuln.description}</p>}
                <p className="text-xs text-gray-400">Découverte le {new Date(vuln.discovered_at).toLocaleString('fr-FR')}</p>
                {vuln.cve_ids?.map(cve => (
                  <a key={cve} href={`https://nvd.nist.gov/vuln/detail/${cve}`} target="_blank" rel="noreferrer"
                    className="flex items-center gap-1 text-xs text-primary-600 hover:underline dark:text-primary-400">
                    <ExternalLink className="h-3 w-3" /> {cve}
                  </a>
                ))}
              </div>
            )}
          </div>
        </div>
        <button onClick={() => setExp(!exp)} className="shrink-0 rounded p-1 text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700">
          {exp ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </button>
      </div>
    </div>
  );
}

// ─── Correlations Tab ─────────────────────────────────────────────────────────

const CERT_SEV_COLOR: Record<string, string> = {
  CRITICAL: '#ef4444',
  HIGH:     '#f97316',
  MEDIUM:   '#eab308',
  LOW:      '#3b82f6',
};

function CorrelationsTab() {
  const { data, isLoading, isError, refetch, isFetching } = useQuery({
    queryKey: ['vuln-correlations'],
    queryFn: feedApi.vulnCorrelations,
    staleTime: 5 * 60 * 1000,
  });

  const correlations: any[] = data?.correlations ?? [];
  const total: number = data?.total_correlated ?? 0;

  if (isLoading) {
    return (
      <div className="flex h-48 items-center justify-center gap-3 text-gray-400">
        <div className="h-6 w-6 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600" />
        <span className="text-sm">Interrogation du CERT-FR…</span>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex h-40 flex-col items-center justify-center gap-2 text-gray-400">
        <AlertTriangle className="h-8 w-8 opacity-40" />
        <p className="text-sm">Impossible de joindre le CERT-FR — réessayez.</p>
        <button onClick={() => refetch()} className="btn btn-sm mt-1">Réessayer</button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            {total === 0
              ? 'Aucune vulnérabilité Petrix ne correspond à une alerte CERT-FR active.'
              : `${total} vulnérabilité${total > 1 ? 's' : ''} corrélée${total > 1 ? 's' : ''} avec des alertes CERT-FR`}
          </p>
          <p className="mt-0.5 text-xs text-gray-400">Corrélation par CVE ID · {data?.cert_items_fetched ?? 0} bulletins CERT-FR analysés</p>
        </div>
        <button onClick={() => refetch()} className="btn btn-sm flex items-center gap-1.5" disabled={isFetching}>
          <RefreshCw className={`h-3.5 w-3.5 ${isFetching ? 'animate-spin' : ''}`} />
          Actualiser
        </button>
      </div>

      {correlations.length === 0 ? (
        <div className="flex h-40 flex-col items-center justify-center gap-3 text-gray-400 rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
          <Shield className="h-10 w-10 opacity-20" />
          <div className="text-center">
            <p className="font-medium text-sm">Aucune corrélation CVE trouvée</p>
            <p className="text-xs mt-1 max-w-sm">
              Les vulnérabilités Petrix doivent avoir des CVE ID renseignés, et ceux-ci doivent apparaître dans les alertes/avis CERT-FR récents.
            </p>
          </div>
        </div>
      ) : (
        <div className="space-y-3">
          {correlations.map((corr: any) => {
            const sevColor = CERT_SEV_COLOR[corr.vuln_severity?.toUpperCase()] ?? '#64748b';
            return (
              <div key={corr.vuln_id}
                className="rounded-xl border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800 overflow-hidden">
                {/* Vuln header */}
                <div className="flex items-start gap-3 p-4 border-b border-gray-100 dark:border-gray-700">
                  <div className="shrink-0 mt-0.5">
                    <AlertTriangle style={{ width: 18, height: 18, color: sevColor }} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2 mb-1">
                      <span className="rounded-full px-2 py-0.5 text-xs font-bold text-white"
                        style={{ background: sevColor }}>
                        {({ critical:'Critique', high:'Élevé', medium:'Moyen', low:'Faible' } as Record<string,string>)[corr.vuln_severity] ?? corr.vuln_severity}
                      </span>
                      {corr.matched_cves.map((cve: string) => (
                        <a key={cve}
                          href={`https://nvd.nist.gov/vuln/detail/${cve}`}
                          target="_blank" rel="noreferrer"
                          className="flex items-center gap-1 rounded bg-blue-50 px-2 py-0.5 font-mono text-xs font-semibold text-blue-700 hover:underline dark:bg-blue-950/30 dark:text-blue-300">
                          <ExternalLink className="h-2.5 w-2.5" />{cve}
                        </a>
                      ))}
                    </div>
                    <p className="font-semibold text-sm text-gray-900 dark:text-white">{corr.vuln_title}</p>
                  </div>
                  <div className="shrink-0 rounded-full bg-orange-100 px-2 py-1 text-xs font-bold text-orange-700 dark:bg-orange-950/30 dark:text-orange-300">
                    {corr.cert_alerts.length} alerte{corr.cert_alerts.length > 1 ? 's' : ''} CERT-FR
                  </div>
                </div>

                {/* Matched CERT-FR alerts */}
                <div className="divide-y divide-gray-50 dark:divide-gray-700/50">
                  {corr.cert_alerts.map((alert: any) => {
                    const alertSev = CERT_SEV_COLOR[alert.severity] ?? '#64748b';
                    return (
                      <div key={alert.cert_id} className="flex items-start gap-3 px-4 py-3 bg-gray-50/50 dark:bg-gray-700/20">
                        <div className="shrink-0 mt-0.5 flex h-5 w-5 items-center justify-center rounded"
                          style={{ background: alertSev + '20' }}>
                          <Bell style={{ width: 11, height: 11, color: alertSev }} />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex flex-wrap items-center gap-2 mb-0.5">
                            <span className="font-mono text-xs font-bold"
                              style={{ color: alertSev }}>{alert.cert_id}</span>
                            <span className="text-xs text-gray-400">{formatDate(alert.published)}</span>
                          </div>
                          <p className="text-xs text-gray-700 dark:text-gray-300 leading-snug">{cleanTitle(alert.title)}</p>
                        </div>
                        {alert.link && (
                          <a href={alert.link} target="_blank" rel="noreferrer"
                            className="shrink-0 rounded p-1 text-gray-400 hover:text-primary-600">
                            <ExternalLink className="h-3.5 w-3.5" />
                          </a>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export default function VulnerabilitiesPage() {
  const [activeTab, setActiveTab] = useState<'feed' | 'internal' | 'correlations'>('feed');
  const [search, setSearch]       = useState('');
  const [sevFilter, setSev]       = useState('');
  const [statusFilter, setStatus] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['vulnerabilities', search, sevFilter, statusFilter],
    queryFn: () => vulnsApi.list({ search: search || undefined, severity: sevFilter || undefined, status: statusFilter || undefined }),
    enabled: activeTab === 'internal',
  });
  const vulns: Vuln[] = data?.items || [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Vulnérabilités</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">Veille CERT-FR (ANSSI) et suivi des vulnérabilités détectées</p>
      </div>

      <div className="flex border-b border-gray-200 dark:border-gray-700">
        {[
          { id: 'feed',         label: 'Veille CERT-FR',           icon: Radio },
          { id: 'internal',     label: 'Vulnérabilités détectées', icon: Shield, count: data?.total },
          { id: 'correlations', label: 'Corrélations CVE ↔ CERT-FR', icon: Link2 },
        ].map(tab => (
          <button key={tab.id} onClick={() => setActiveTab(tab.id as 'feed' | 'internal' | 'correlations')}
            className={`flex items-center gap-2 border-b-2 px-4 pb-3 text-sm font-medium transition-colors ${
              activeTab === tab.id
                ? 'border-primary-600 text-primary-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400'
            }`}>
            <tab.icon className="h-4 w-4" />
            {tab.label}
            {tab.count != null && tab.count > 0 && (
              <span className="rounded-full bg-red-500 px-1.5 py-0.5 text-xs text-white">{tab.count}</span>
            )}
          </button>
        ))}
      </div>

      {activeTab === 'feed'         && <CertFrFeed />}
      {activeTab === 'correlations' && <CorrelationsTab />}

      {activeTab === 'internal' && (
        <>
          <div className="flex flex-wrap gap-3">
            <div className="relative flex-1 min-w-48">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
              <input type="text" placeholder="Rechercher…" value={search}
                onChange={e => setSearch(e.target.value)} className="input pl-9 text-sm" />
            </div>
            <select value={sevFilter} onChange={e => setSev(e.target.value)} className="input w-40 text-sm">
              <option value="">Toutes sévérités</option>
              <option value="critical">Critique</option>
              <option value="high">Élevé</option>
              <option value="medium">Moyen</option>
              <option value="low">Faible</option>
            </select>
            <select value={statusFilter} onChange={e => setStatus(e.target.value)} className="input w-40 text-sm">
              <option value="">Tous les statuts</option>
              <option value="open">Ouvert</option>
              <option value="in_progress">En cours</option>
              <option value="resolved">Résolu</option>
              <option value="accepted">Accepté</option>
            </select>
          </div>
          <div className="overflow-hidden rounded-xl border border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-800">
            {isLoading ? (
              <div className="flex h-48 items-center justify-center">
                <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-200 border-t-primary-600" />
              </div>
            ) : vulns.length === 0 ? (
              <div className="flex h-48 flex-col items-center justify-center gap-3 text-gray-400">
                <Shield className="h-12 w-12 opacity-20" />
                <div className="text-center">
                  <p className="font-medium">Aucune vulnérabilité enregistrée</p>
                  <p className="text-xs mt-1">Les vulnérabilités découvertes lors des audits apparaîtront ici</p>
                </div>
              </div>
            ) : (
              <div className="divide-y divide-gray-100 dark:divide-gray-700">
                {vulns.map(v => <VulnRow key={v.id} vuln={v} />)}
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
