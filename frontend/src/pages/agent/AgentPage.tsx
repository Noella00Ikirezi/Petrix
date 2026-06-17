import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  Download, Monitor, Terminal, Apple, Shield, CheckCircle,
  AlertTriangle, Activity, Clock, Play, Loader2,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { apiClient, scansApi } from '@/api/client';

type OS = 'linux' | 'macos' | 'windows';

function detectOS(): OS {
  const ua = navigator.userAgent.toLowerCase();
  const platform = navigator.platform.toLowerCase();
  if (platform.includes('win') || ua.includes('windows')) return 'windows';
  if (platform.includes('mac') || ua.includes('mac')) return 'macos';
  return 'linux';
}

const OS_INFO = {
  linux: {
    label: 'Linux',
    icon: Terminal,
    color: 'text-orange-500',
    bg: 'bg-orange-50 dark:bg-orange-900/20 border-orange-200 dark:border-orange-800',
    active: 'ring-2 ring-orange-500',
  },
  macos: {
    label: 'macOS',
    icon: Apple,
    color: 'text-gray-700 dark:text-gray-200',
    bg: 'bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700',
    active: 'ring-2 ring-gray-500',
  },
  windows: {
    label: 'Windows',
    icon: Monitor,
    color: 'text-blue-500',
    bg: 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800',
    active: 'ring-2 ring-blue-500',
  },
};

const TERMS = [
  "Je certifie être propriétaire des réseaux scannés ou disposer d'une autorisation écrite des responsables.",
  "Je m'engage à ne pas utiliser Petrix Agent à des fins malveillantes, illégales ou non autorisées.",
  "Je comprends que le scan réseau peut être détecté par des systèmes de sécurité tiers.",
  "Les résultats de scan sont confidentiels et ne doivent pas être partagés sans autorisation.",
  "L'utilisation de cet outil engage ma responsabilité personnelle et professionnelle.",
  "Petrix et ses développeurs ne sauraient être tenus responsables d'une utilisation abusive.",
];

interface ScanItem {
  id: string;
  name: string;
  scan_type: string;
  status: string;
  progress: number;
  current_phase: string | null;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
  duration_seconds: number | null;
  grade: string | null;
  findings_summary: { critical: number; high: number; medium: number; low: number; info: number } | null;
}

export default function AgentPage() {
  const [selectedOS, setSelectedOS] = useState<OS>(detectOS());
  const [showTos, setShowTos] = useState(false);
  const [tosAccepted, setTosAccepted] = useState(false);
  const [tosChecked, setTosChecked] = useState(false);
  const [activeTab, setActiveTab] = useState<'install' | 'console'>('install');

  const [freshToken, setFreshToken] = useState<string | null>(null);
  const [isFetching, setIsFetching] = useState(false);

  const generateToken = async (): Promise<string | null> => {
    setIsFetching(true);
    try {
      const r = await apiClient.post('/agent/token');
      const tok = (r.data as { token: string; user: string }).token;
      setFreshToken(tok);
      return tok;
    } catch {
      return null;
    } finally {
      setIsFetching(false);
    }
  };

  // Console: poll recent scans for live activity
  const { data: scansData, isLoading: scansLoading } = useQuery({
    queryKey: ['scans'],
    queryFn: () => scansApi.list(),
    refetchInterval: activeTab === 'console' ? 4000 : false,
    enabled: activeTab === 'console',
  });

  const recentScans: ScanItem[] = (scansData?.items || []).slice(0, 10);
  const runningScans = recentScans.filter((s) => s.status === 'running');

  const handleDownload = async () => {
    if (!tosAccepted) { setShowTos(true); return; }
    await doDownload();
  };

  const doDownload = async () => {
    const token = await generateToken();
    if (!token) { toast.error('Impossible de générer le token agent'); return; }

    const serverUrl = window.location.origin;
    const osEndpoint = selectedOS === 'windows' ? 'windows-ps' : selectedOS;
    const url = `/api/v1/agent/download/${osEndpoint}?server_url=${encodeURIComponent(serverUrl)}&token=${encodeURIComponent(token)}`;
    const ext = selectedOS === 'windows' ? '.ps1' : '.sh';
    const filename = `petrix-agent-installer-${selectedOS}${ext}`;
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    toast.success('Téléchargement démarré — token valable 30 jours');
  };

  const acceptTos = () => {
    if (!tosChecked) { toast.error("Veuillez accepter les conditions d'utilisation"); return; }
    setTosAccepted(true);
    setShowTos(false);
    doDownload();
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Petrix Agent</h1>
        <p className="text-gray-600 dark:text-gray-400">
          Déployez l'agent sur vos machines pour scanner votre réseau local et remonter les résultats.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 rounded-lg border border-gray-200 bg-gray-50 p-1 dark:border-gray-700 dark:bg-gray-900 w-fit">
        <button onClick={() => setActiveTab('install')}
          className={`rounded-md px-4 py-1.5 text-sm font-medium transition-colors ${
            activeTab === 'install' ? 'bg-white shadow text-gray-900 dark:bg-gray-800 dark:text-white' : 'text-gray-500 hover:text-gray-700 dark:text-gray-400'
          }`}>
          Installation
        </button>
        <button onClick={() => setActiveTab('console')}
          className={`flex items-center gap-2 rounded-md px-4 py-1.5 text-sm font-medium transition-colors ${
            activeTab === 'console' ? 'bg-white shadow text-gray-900 dark:bg-gray-800 dark:text-white' : 'text-gray-500 hover:text-gray-700 dark:text-gray-400'
          }`}>
          Console
          {runningScans.length > 0 && (
            <span className="flex h-2 w-2 rounded-full bg-green-500 animate-pulse" />
          )}
        </button>
      </div>

      {activeTab === 'install' && (
        <>
          {/* How it works */}
          <div className="card">
            <h2 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">Comment ça fonctionne</h2>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
              {[
                { step: '1', title: 'Choisissez votre OS', desc: 'Windows, Linux ou macOS' },
                { step: '2', title: 'Téléchargez', desc: 'Installer pré-configuré avec votre token' },
                { step: '3', title: 'Exécutez', desc: 'Double-cliquez (Windows) ou bash (Linux/macOS)' },
                { step: '4', title: 'Résultats', desc: 'Visibles ici en temps réel dans la Console' },
              ].map((s) => (
                <div key={s.step} className="flex items-start gap-3">
                  <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary-100 text-sm font-bold text-primary-700 dark:bg-primary-900 dark:text-primary-300">
                    {s.step}
                  </div>
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">{s.title}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">{s.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* OS selector */}
          <div className="card">
            <h2 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">Choisissez votre système</h2>
            <div className="grid grid-cols-3 gap-3">
              {(Object.entries(OS_INFO) as [OS, typeof OS_INFO.linux][]).map(([os, info]) => {
                const Icon = info.icon;
                const isSelected = selectedOS === os;
                return (
                  <button key={os} onClick={() => setSelectedOS(os)}
                    className={`flex flex-col items-center gap-2 rounded-lg border p-4 transition-all ${info.bg} ${isSelected ? info.active : 'hover:opacity-80'}`}>
                    <Icon className={`h-8 w-8 ${info.color}`} />
                    <span className="font-medium text-gray-900 dark:text-white">{info.label}</span>
                    {os === detectOS() && <span className="text-xs text-green-600 dark:text-green-400">Votre OS</span>}
                  </button>
                );
              })}
            </div>

            <div className="mt-6">
              <button onClick={handleDownload} disabled={isFetching} className="btn btn-primary btn-lg w-full">
                <Download className="mr-2 h-5 w-5" />
                {isFetching ? 'Génération du token...' : `Télécharger pour ${OS_INFO[selectedOS].label}`}
              </button>
              {tosAccepted && (
                <p className="mt-2 flex items-center justify-center gap-1 text-xs text-green-600 dark:text-green-400">
                  <CheckCircle className="h-3 w-3" /> Conditions acceptées
                </p>
              )}
            </div>
          </div>

          {/* Instructions */}
          <div className="card">
            <h2 className="mb-3 text-lg font-semibold text-gray-900 dark:text-white">Après le téléchargement</h2>
            {selectedOS === 'windows' ? (
              <div className="space-y-4 text-sm text-gray-700 dark:text-gray-300">
                <div className="rounded-md bg-blue-50 border border-blue-200 px-3 py-2 text-blue-800 dark:bg-blue-900/20 dark:text-blue-300 dark:border-blue-800">
                  Le bouton télécharge un <strong>script PowerShell</strong> pré-configuré avec votre token (valable 30 jours).
                  Exécutez-le <strong>en tant qu'administrateur</strong> — il installe Python, nmap et l'agent automatiquement.
                </div>

                <div>
                  <p className="font-semibold mb-2">Étapes</p>
                  <ol className="space-y-2 list-none">
                    <li>1. Cliquez sur <strong>Télécharger pour Windows</strong> ci-dessus</li>
                    <li>2. Ouvrez <strong>PowerShell en administrateur</strong> (clic droit → Exécuter en tant qu'administrateur)</li>
                    <li>3. Collez et exécutez :</li>
                  </ol>
                  <code className="mt-2 block rounded bg-gray-100 px-3 py-2 font-mono text-xs dark:bg-gray-800 select-all">
                    {'powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\\Downloads\\petrix-agent-installer-windows.ps1"'}
                  </code>
                  <li className="mt-2 list-none text-xs text-gray-500">4. Répondre <strong>O</strong> à la question "Lancer un scan maintenant ?"</li>
                </div>

                <div>
                  <p className="font-semibold mb-2">Alternative — Une seule commande PowerShell admin</p>
                  <p className="text-xs text-gray-500 mb-1">Cliquez d'abord sur "Télécharger" pour générer le token, puis copiez cette commande :</p>
                  {freshToken ? (
                    <code className="block rounded bg-gray-100 px-3 py-2 font-mono text-xs dark:bg-gray-800 break-all whitespace-pre-wrap select-all">
                      {`$f="$env:TEMP\\petrix.ps1"; (New-Object Net.WebClient).DownloadFile("${window.location.origin}/api/v1/agent/download/windows-ps?server_url=${encodeURIComponent(window.location.origin)}&token=${encodeURIComponent(freshToken)}", $f); powershell -ExecutionPolicy Bypass -File $f -Server "${window.location.origin}" -Token "${freshToken}"`}
                    </code>
                  ) : (
                    <div className="rounded bg-gray-100 px-3 py-2 text-xs text-gray-400 dark:bg-gray-800 italic">
                      Cliquez sur "Télécharger" ci-dessus → la commande apparaîtra ici avec votre token.
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="space-y-3 text-sm text-gray-700 dark:text-gray-300">
                <p>1. Ouvrez un <strong>terminal</strong></p>
                <p>2. Rendez le script exécutable et lancez-le :</p>
                <code className="block rounded bg-gray-100 px-3 py-2 font-mono text-xs dark:bg-gray-800">
                  chmod +x ~/Downloads/petrix-agent-install-{selectedOS}.sh{'\n'}
                  sudo bash ~/Downloads/petrix-agent-install-{selectedOS}.sh
                </code>
                <p className="text-xs text-gray-400">sudo est requis pour installer nmap et accéder au réseau en mode audit.</p>
              </div>
            )}
          </div>

          {/* Requirements */}
          <div className="card">
            <h2 className="mb-3 text-lg font-semibold text-gray-900 dark:text-white">Prérequis</h2>
            <div className="grid grid-cols-1 gap-2 sm:grid-cols-3 text-sm">
              {[
                { req: 'Python 3.9+', note: 'Installé automatiquement (winget/brew/apt)' },
                { req: 'Git', note: 'Requis pour l\'installation — installé automatiquement' },
                { req: 'Droits admin', note: 'Obligatoire pour le mode audit réseau' },
              ].map((r) => (
                <div key={r.req} className="flex items-start gap-2">
                  <CheckCircle className="mt-0.5 h-4 w-4 shrink-0 text-green-500" />
                  <div>
                    <p className="font-medium text-gray-900 dark:text-white">{r.req}</p>
                    <p className="text-xs text-gray-500">{r.note}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}

      {activeTab === 'console' && (
        <div className="space-y-4">
          {runningScans.length > 0 && (
            <div className="rounded-lg border border-green-200 bg-green-50 p-4 dark:border-green-800 dark:bg-green-900/10">
              <div className="flex items-center gap-2 mb-3">
                <Activity className="h-5 w-5 text-green-600 animate-pulse" />
                <span className="font-semibold text-green-800 dark:text-green-300">
                  {runningScans.length} scan(s) en cours
                </span>
              </div>
              {runningScans.map((scan) => (
                <div key={scan.id} className="rounded-md bg-white dark:bg-gray-800 p-3 mb-2">
                  <div className="flex justify-between mb-1">
                    <span className="font-medium text-gray-900 dark:text-white text-sm">{scan.name}</span>
                    <span className="text-xs text-gray-500">{scan.progress}%</span>
                  </div>
                  <div className="h-2 w-full rounded-full bg-gray-200 dark:bg-gray-700">
                    <div className="h-2 rounded-full bg-green-500 transition-all"
                      style={{ width: `${scan.progress}%` }} />
                  </div>
                  {scan.current_phase && (
                    <p className="mt-1 text-xs text-gray-500">Phase : {scan.current_phase}</p>
                  )}
                </div>
              ))}
            </div>
          )}

          <div className="card p-0 overflow-hidden">
            <div className="flex items-center gap-2 border-b border-gray-200 dark:border-gray-700 px-4 py-3">
              <Activity className="h-4 w-4 text-gray-500" />
              <h2 className="font-semibold text-gray-900 dark:text-white text-sm">Activité récente</h2>
              {scansLoading && <Loader2 className="h-3 w-3 animate-spin text-gray-400" />}
            </div>

            {recentScans.length === 0 ? (
              <div className="flex h-48 flex-col items-center justify-center text-gray-500 gap-2">
                <Play className="h-8 w-8" />
                <p className="text-sm">Aucun scan enregistré — installez l'agent et lancez un scan</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-100 dark:divide-gray-700">
                {recentScans.map((scan) => (
                  <div key={scan.id} className="px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-700/50">
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-start gap-3">
                        <div className={`mt-0.5 h-2.5 w-2.5 rounded-full shrink-0 ${
                          scan.status === 'running' ? 'bg-green-500 animate-pulse'
                          : scan.status === 'completed' ? 'bg-gray-400'
                          : scan.status === 'failed' ? 'bg-red-500'
                          : 'bg-yellow-500'
                        }`} />
                        <div>
                          <p className="text-sm font-medium text-gray-900 dark:text-white">{scan.name}</p>
                          <p className="text-xs text-gray-500">
                            {scan.scan_type} ·{' '}
                            {scan.status === 'running' ? `en cours — ${scan.progress}%`
                              : scan.status === 'completed' ? `terminé en ${Math.round(scan.duration_seconds || 0)}s`
                              : scan.status === 'failed' ? 'échoué'
                              : 'en attente'}
                          </p>
                          {scan.status === 'running' && scan.current_phase && (
                            <p className="text-xs text-blue-600 dark:text-blue-400">↳ {scan.current_phase}</p>
                          )}
                          {scan.status === 'failed' && scan.error_message && (
                            <p className="text-xs text-red-500">↳ {scan.error_message}</p>
                          )}
                          {scan.status === 'completed' && scan.findings_summary && (
                            <p className="text-xs text-gray-400">
                              {scan.findings_summary.critical > 0 && <span className="text-red-500 font-medium">{scan.findings_summary.critical} critique </span>}
                              {scan.findings_summary.high > 0 && <span className="text-orange-500">{scan.findings_summary.high} élevé </span>}
                              {scan.findings_summary.medium > 0 && <span className="text-yellow-500">{scan.findings_summary.medium} moyen </span>}
                            </p>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        {scan.grade && (
                          <span className={`text-xs font-bold px-1.5 py-0.5 rounded ${
                            scan.grade === 'A' ? 'bg-green-100 text-green-700' : scan.grade === 'B' ? 'bg-lime-100 text-lime-700'
                            : scan.grade === 'C' ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700'
                          }`}>{scan.grade}</span>
                        )}
                        <div className="flex items-center gap-1 text-xs text-gray-400">
                          <Clock className="h-3 w-3" />
                          {scan.started_at
                            ? new Date(scan.started_at).toLocaleTimeString('fr', { hour: '2-digit', minute: '2-digit' })
                            : '—'}
                        </div>
                      </div>
                    </div>
                    {scan.status === 'running' && (
                      <div className="mt-2 ml-5">
                        <div className="h-1.5 w-full rounded-full bg-gray-200 dark:bg-gray-700">
                          <div className="h-1.5 rounded-full bg-primary-500 transition-all"
                            style={{ width: `${scan.progress}%` }} />
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ToS Modal */}
      {showTos && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
          <div className="w-full max-w-lg rounded-xl bg-white shadow-2xl dark:bg-gray-800">
            <div className="flex items-center gap-3 border-b border-gray-200 p-6 dark:border-gray-700">
              <Shield className="h-6 w-6 text-primary-600" />
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">Conditions d'utilisation</h2>
            </div>
            <div className="p-6 space-y-3">
              <div className="rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-800 dark:bg-amber-900/30 dark:text-amber-300">
                <AlertTriangle className="mb-1 inline h-4 w-4" />{' '}
                Cet outil est réservé aux réseaux que vous êtes autorisé à tester.
              </div>
              <ul className="space-y-2">
                {TERMS.map((term, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-gray-700 dark:text-gray-300">
                    <span className="mt-0.5 shrink-0 text-primary-500">•</span>
                    {term}
                  </li>
                ))}
              </ul>
              <label className="flex cursor-pointer items-start gap-3 rounded-md border border-primary-200 bg-primary-50 p-3 dark:border-primary-800 dark:bg-primary-900/20">
                <input type="checkbox" checked={tosChecked} onChange={(e) => setTosChecked(e.target.checked)}
                  className="mt-0.5 h-4 w-4 accent-primary-600" />
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  J'ai lu et j'accepte les conditions d'utilisation de Petrix Agent.
                </span>
              </label>
            </div>
            <div className="flex gap-3 border-t border-gray-200 p-6 dark:border-gray-700">
              <button onClick={() => setShowTos(false)} className="btn btn-secondary btn-md flex-1">Annuler</button>
              <button onClick={acceptTos} disabled={!tosChecked} className="btn btn-primary btn-md flex-1">
                Accepter et télécharger
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
