import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { Download, Monitor, Terminal, Apple, Shield, CheckCircle, AlertTriangle } from 'lucide-react';
import toast from 'react-hot-toast';
import { apiClient } from '@/api/client';

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
    cmd: 'bash petrix-agent-install-linux.sh',
    ext: '.sh',
  },
  macos: {
    label: 'macOS',
    icon: Apple,
    color: 'text-gray-700 dark:text-gray-200',
    bg: 'bg-gray-50 dark:bg-gray-800 border-gray-200 dark:border-gray-700',
    active: 'ring-2 ring-gray-500',
    cmd: 'bash petrix-agent-install-macos.sh',
    ext: '.sh',
  },
  windows: {
    label: 'Windows',
    icon: Monitor,
    color: 'text-blue-500',
    bg: 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800',
    active: 'ring-2 ring-blue-500',
    cmd: 'powershell -ExecutionPolicy Bypass -File petrix-agent-install-windows.ps1',
    ext: '.ps1',
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

export default function AgentPage() {
  const [selectedOS, setSelectedOS] = useState<OS>(detectOS());
  const [showTos, setShowTos] = useState(false);
  const [tosAccepted, setTosAccepted] = useState(false);
  const [tosChecked, setTosChecked] = useState(false);

  const { data: tokenData, refetch: generateToken, isFetching } = useQuery({
    queryKey: ['agent-token'],
    queryFn: async () => {
      const r = await apiClient.post('/agent/token');
      return r.data as { token: string; user: string };
    },
    enabled: false,
  });

  const handleDownload = async () => {
    if (!tosAccepted) {
      setShowTos(true);
      return;
    }
    await doDownload();
  };

  const doDownload = async () => {
    let token = tokenData?.token;
    if (!token) {
      const result = await generateToken();
      token = result.data?.token;
    }
    if (!token) {
      toast.error('Impossible de générer le token agent');
      return;
    }
    const serverUrl = window.location.origin;
    const url = `/api/v1/agent/download/${selectedOS}?server_url=${encodeURIComponent(serverUrl)}&token=${encodeURIComponent(token)}`;
    const a = document.createElement('a');
    a.href = url;
    a.download = `petrix-agent-install-${selectedOS}${OS_INFO[selectedOS].ext}`;
    a.click();
    toast.success('Téléchargement démarré');
  };

  const acceptTos = () => {
    if (!tosChecked) {
      toast.error("Veuillez accepter les conditions d'utilisation");
      return;
    }
    setTosAccepted(true);
    setShowTos(false);
    doDownload();
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Petrix Agent</h1>
        <p className="text-gray-600 dark:text-gray-400">
          Installez l'agent sur vos machines pour scanner votre réseau local et remonter les résultats.
        </p>
      </div>

      {/* How it works */}
      <div className="card">
        <h2 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">Comment ça fonctionne</h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-4">
          {[
            { step: '1', title: 'Choisissez votre OS', desc: 'Windows, Linux ou macOS' },
            { step: '2', title: 'Téléchargez', desc: 'Script pré-configuré avec votre token' },
            { step: '3', title: 'Exécutez', desc: 'Une seule commande, tout est automatique' },
            { step: '4', title: 'Résultats', desc: 'Visibles ici en temps réel' },
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
              <button
                key={os}
                onClick={() => setSelectedOS(os)}
                className={`flex flex-col items-center gap-2 rounded-lg border p-4 transition-all ${info.bg} ${isSelected ? info.active : 'hover:opacity-80'}`}
              >
                <Icon className={`h-8 w-8 ${info.color}`} />
                <span className="font-medium text-gray-900 dark:text-white">{info.label}</span>
                {os === detectOS() && (
                  <span className="text-xs text-green-600 dark:text-green-400">Votre OS</span>
                )}
              </button>
            );
          })}
        </div>

        {/* Download button */}
        <div className="mt-6">
          <button
            onClick={handleDownload}
            disabled={isFetching}
            className="btn btn-primary btn-lg w-full"
          >
            <Download className="mr-2 h-5 w-5" />
            {isFetching ? 'Génération du token...' : `Télécharger pour ${OS_INFO[selectedOS].label}`}
          </button>

          {tosAccepted && (
            <p className="mt-2 flex items-center gap-1 text-center text-xs text-green-600 dark:text-green-400">
              <CheckCircle className="h-3 w-3" /> Conditions d'utilisation acceptées
            </p>
          )}
        </div>
      </div>

      {/* Installation instructions */}
      <div className="card">
        <h2 className="mb-3 text-lg font-semibold text-gray-900 dark:text-white">Après le téléchargement</h2>
        {selectedOS === 'windows' ? (
          <div className="space-y-2 text-sm text-gray-700 dark:text-gray-300">
            <p>1. Ouvrez <strong>PowerShell en tant qu'administrateur</strong></p>
            <p>2. Naviguez vers le dossier téléchargé :</p>
            <code className="block rounded bg-gray-100 px-3 py-2 font-mono text-xs dark:bg-gray-800">cd ~/Downloads</code>
            <p>3. Exécutez l'installeur :</p>
            <code className="block rounded bg-gray-100 px-3 py-2 font-mono text-xs dark:bg-gray-800">
              powershell -ExecutionPolicy Bypass -File petrix-agent-install-windows.ps1
            </code>
          </div>
        ) : (
          <div className="space-y-2 text-sm text-gray-700 dark:text-gray-300">
            <p>1. Ouvrez un <strong>terminal</strong></p>
            <p>2. Naviguez vers le dossier téléchargé :</p>
            <code className="block rounded bg-gray-100 px-3 py-2 font-mono text-xs dark:bg-gray-800">cd ~/Downloads</code>
            <p>3. Exécutez l'installeur :</p>
            <code className="block rounded bg-gray-100 px-3 py-2 font-mono text-xs dark:bg-gray-800">
              {OS_INFO[selectedOS].cmd}
            </code>
            <p className="text-xs text-gray-400">Note : un mot de passe administrateur peut être demandé pour installer nmap.</p>
          </div>
        )}
      </div>

      {/* Requirements */}
      <div className="card">
        <h2 className="mb-3 text-lg font-semibold text-gray-900 dark:text-white">Prérequis</h2>
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-3 text-sm">
          {[
            { req: 'Python 3.9+', note: 'Installé automatiquement si absent' },
            { req: 'nmap', note: 'Optionnel — fallback socket si absent' },
            { req: 'Connexion internet', note: 'Pour l\'installation uniquement' },
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
                <input
                  type="checkbox"
                  checked={tosChecked}
                  onChange={(e) => setTosChecked(e.target.checked)}
                  className="mt-0.5 h-4 w-4 accent-primary-600"
                />
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  J'ai lu et j'accepte les conditions d'utilisation de Petrix Agent.
                </span>
              </label>
            </div>

            <div className="flex gap-3 border-t border-gray-200 p-6 dark:border-gray-700">
              <button onClick={() => setShowTos(false)} className="btn btn-secondary btn-md flex-1">
                Annuler
              </button>
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
