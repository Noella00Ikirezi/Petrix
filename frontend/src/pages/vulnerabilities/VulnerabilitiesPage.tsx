/**
 * Page de gestion des vulnérabilités et de veille CERT-FR.
 * Deux onglets principaux : liste des CVE locales avec filtres sévérité/statut,
 * et flux CERT-FR en temps réel (alertes, avis, IOC) avec corrélations automatiques.
 */
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

/**
 * Panneau latéral (drawer) affichant le détail d'une fiche CERT-FR :
 * bannière colorée par sévérité, risques, systèmes affectés, résumé, solution, CVE et références.
 * @param certId - Identifiant CERT-FR (ex. CERTFR-2025-ALE-001).
 * @param feedType - Type de flux (alerte | avis | dur | ioc | actualite).
 * @param onClose - Callback de fermeture du drawer.
 */
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

      {/* Modal centré */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="relative flex w-full max-w-2xl max-h-[88vh] flex-col overflow-hidden rounded-2xl bg-white shadow-2xl dark:bg-gray-900">

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
      </div>
    </>
  );
}

/**
 * Section encadrée de la fiche CERT-FR avec titre et icône colorée.
 * Utilisée pour compartimenter risques, systèmes affectés, solution et références.
 */
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

/**
 * Onglet flux CERT-FR : agrège alertes, avis, IOC et actualités via feedApi.certFrMulti,
 * permet le filtrage par type de publication et l'ouverture de la fiche détaillée dans un drawer.
 */
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

// ─── Research Links ────────────────────────────────────────────────────────────

function ResearchLinks({ title, cve_ids }: { title: string; cve_ids: string[] }) {
  const q = encodeURIComponent(title.slice(0, 80));
  return (
    <div className="mt-3 rounded-lg border border-blue-100 bg-blue-50/60 p-3 dark:border-blue-900/40 dark:bg-blue-950/20">
      <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-blue-600 dark:text-blue-400">
        Rechercher sur les bases officielles
      </p>
      <div className="flex flex-wrap gap-2">
        {cve_ids.map(cve => (
          <span key={cve} className="contents">
            <a href={`https://nvd.nist.gov/vuln/detail/${cve}`} target="_blank" rel="noreferrer"
              className="flex items-center gap-1 rounded-md bg-blue-600 px-2.5 py-1 font-mono text-xs font-semibold text-white hover:bg-blue-700">
              <ExternalLink className="h-3 w-3" /> NVD · {cve}
            </a>
            <a href={`https://cve.mitre.org/cgi-bin/cvename.cgi?name=${cve}`} target="_blank" rel="noreferrer"
              className="flex items-center gap-1 rounded-md bg-purple-100 px-2.5 py-1 font-mono text-xs font-semibold text-purple-700 hover:bg-purple-200 dark:bg-purple-900/30 dark:text-purple-300">
              <ExternalLink className="h-3 w-3" /> MITRE · {cve}
            </a>
            <a href={`https://www.cve.org/CVERecord?id=${cve}`} target="_blank" rel="noreferrer"
              className="flex items-center gap-1 rounded-md bg-purple-50 px-2.5 py-1 font-mono text-xs font-medium text-purple-600 hover:bg-purple-100 dark:bg-purple-900/20 dark:text-purple-400">
              <ExternalLink className="h-3 w-3" /> CVE.org · {cve}
            </a>
          </span>
        ))}
        <a href={`https://www.cert.ssi.gouv.fr/?s=${q}`} target="_blank" rel="noreferrer"
          className="flex items-center gap-1 rounded-md bg-indigo-100 px-2.5 py-1 text-xs font-medium text-indigo-700 hover:bg-indigo-200 dark:bg-indigo-900/30 dark:text-indigo-300">
          <ExternalLink className="h-3 w-3" /> Rechercher CERT-FR
        </a>
        <a href={`https://nvd.nist.gov/vuln/search/results?query=${q}&search_type=all`} target="_blank" rel="noreferrer"
          className="flex items-center gap-1 rounded-md bg-blue-100 px-2.5 py-1 text-xs font-medium text-blue-700 hover:bg-blue-200 dark:bg-blue-900/30 dark:text-blue-300">
          <ExternalLink className="h-3 w-3" /> Rechercher NVD
        </a>
        <a href={`https://cve.mitre.org/cgi-bin/cvekey.cgi?keyword=${q}`} target="_blank" rel="noreferrer"
          className="flex items-center gap-1 rounded-md bg-purple-100 px-2.5 py-1 text-xs font-medium text-purple-700 hover:bg-purple-200 dark:bg-purple-900/30 dark:text-purple-300">
          <ExternalLink className="h-3 w-3" /> Rechercher MITRE
        </a>
        <a href="https://www.ssi.gouv.fr/guide/recommandations-de-securite-relatives-a-un-systeme-gnulinux/" target="_blank" rel="noreferrer"
          className="flex items-center gap-1 rounded-md bg-gray-100 px-2.5 py-1 text-xs font-medium text-gray-600 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300">
          <ExternalLink className="h-3 w-3" /> ANSSI BP-028
        </a>
      </div>
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

/**
 * Ligne expandable représentant une vulnérabilité locale : sévérité, statut, CVE IDs,
 * score CVSS, description complète et date de découverte.
 */
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
                <ResearchLinks title={vuln.title} cve_ids={vuln.cve_ids ?? []} />
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

// ─── Main Page ────────────────────────────────────────────────────────────────

/**
 * Page principale des vulnérabilités.
 * Trois onglets : liste locale (CVE inventoriées), flux CERT-FR temps réel, corrélations CVE.
 * Inclut un formulaire de création manuelle de vulnérabilité et des filtres par sévérité/statut.
 */
export default function VulnerabilitiesPage() {
  const [activeTab, setActiveTab] = useState<'feed' | 'internal'>('feed');
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
          { id: 'feed',     label: 'Veille CERT-FR',           icon: Radio },
          { id: 'internal', label: 'Vulnérabilités détectées', icon: Shield, count: data?.total },
        ].map(tab => (
          <button key={tab.id} onClick={() => setActiveTab(tab.id as 'feed' | 'internal')}
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

      {activeTab === 'feed' && <CertFrFeed />}

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
