import { Link } from 'react-router-dom';
import {
  Server,
  Shield,
  Scan,
  ClipboardList,
  ArrowRight,
  Lock,
  Globe,
  Cpu,
  LayoutDashboard,
  Terminal,
} from 'lucide-react';
import { useAuthStore } from '@/stores/authStore';

const modules = [
  {
    name: 'Gestion des actifs',
    description: 'Inventaire de votre parc IT : serveurs, postes, équipements réseau. Suivi de la criticité et des vulnérabilités associées.',
    icon: Server,
    color: 'bg-blue-100 text-blue-600 dark:bg-blue-900/40 dark:text-blue-400',
    img: 'https://images.unsplash.com/photo-1544197150-b99a580bb7a8?w=400&q=80',
  },
  {
    name: 'Scanner de vulnérabilités',
    description: 'Détection des failles avec scoring CVSS, tri par sévérité et suivi de remédiation.',
    icon: Shield,
    color: 'bg-red-100 text-red-600 dark:bg-red-900/40 dark:text-red-400',
    img: 'https://images.unsplash.com/photo-1550751827-4bd374c3f58b?w=400&q=80',
  },
  {
    name: 'Scans réseau',
    description: 'Découverte d\'hôtes, scan de ports, analyse de services et détection de CVEs sur votre infrastructure.',
    icon: Scan,
    color: 'bg-orange-100 text-orange-600 dark:bg-orange-900/40 dark:text-orange-400',
    img: 'https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=400&q=80',
  },
  {
    name: 'Hardening (HCO)',
    description: 'Audit de durcissement par SSH : configurations système, politiques de mots de passe, services exposés.',
    icon: Lock,
    color: 'bg-purple-100 text-purple-600 dark:bg-purple-900/40 dark:text-purple-400',
    img: 'https://images.unsplash.com/photo-1518770660439-4636190af475?w=400&q=80',
  },
  {
    name: 'Agent terrain',
    description: 'Déployez un agent léger (Windows/Linux/macOS) pour scanner les réseaux internes sans exposition directe.',
    icon: Terminal,
    color: 'bg-cyan-100 text-cyan-600 dark:bg-cyan-900/40 dark:text-cyan-400',
    img: 'https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=400&q=80',
  },
  {
    name: 'Journaux d\'audit',
    description: 'Traçabilité complète de toutes les actions utilisateurs pour la conformité réglementaire.',
    icon: ClipboardList,
    color: 'bg-green-100 text-green-600 dark:bg-green-900/40 dark:text-green-400',
    img: 'https://images.unsplash.com/photo-1555255707-c07966088b7b?w=400&q=80',
  },
];

const values = [
  {
    icon: Lock,
    title: 'Souveraineté numérique',
    description: 'Aucune dépendance cloud externe. Vos données restent sur votre infrastructure, sous votre contrôle total.',
  },
  {
    icon: Cpu,
    title: 'Automatisation poussée',
    description: 'Scans, hardening, scoring de risques : tout est automatisé pour réduire la charge opérationnelle.',
  },
  {
    icon: Globe,
    title: 'Open Source',
    description: 'Code source ouvert, auditable et personnalisable. Adaptez Petrix à vos contraintes.',
  },
];

export default function HomePage() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  return (
    <div className="min-h-screen bg-petrix-white dark:bg-petrix-void">

      {/* Navigation */}
      <nav className="border-b border-gray-200 dark:border-gray-800">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
          <div className="flex items-center gap-3">
            <img src="/logo-petrix.svg" alt="Petrix" className="h-9 w-9 dark:hidden" />
            <img src="/logo-petrix-dark.svg" alt="Petrix" className="hidden h-9 w-9 dark:block" />
            <span className="text-xl font-bold text-petrix-void dark:text-petrix-cyan-light">Petrix</span>
          </div>
          <div className="flex items-center gap-3">
            {isAuthenticated ? (
              <Link to="/dashboard" className="btn btn-primary btn-md">
                <LayoutDashboard className="mr-2 h-4 w-4" />
                Dashboard
              </Link>
            ) : (
              <>
                <Link to="/login" className="btn btn-secondary btn-md">Connexion</Link>
                <Link to="/signup" className="btn btn-primary btn-md">Créer un compte</Link>
              </>
            )}
          </div>
        </div>
      </nav>

      {/* Hero — photo plein écran + overlay */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0">
          <img
            src="https://images.unsplash.com/photo-1558494949-ef010cbdcc31?auto=format&fit=crop&w=1920&q=80"
            alt="Salle de serveurs"
            className="h-full w-full object-cover"
          />
          <div className="absolute inset-0 bg-gradient-to-b from-gray-950/80 via-gray-950/70 to-gray-950" />
        </div>
        <div className="relative mx-auto max-w-3xl px-6 py-28 text-center">
          <div className="mb-6 inline-flex items-center rounded-full border border-primary-500/40 bg-primary-900/30 px-4 py-1.5 text-sm font-medium text-primary-300">
            Open Source · Self-Hosted · Souverain
          </div>
          <h1 className="text-5xl font-bold tracking-tight text-white">
            Plateforme d'audit
            <br />
            <span className="text-primary-400">cybersécurité</span>
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg text-gray-300">
            Gérez vos actifs, scannez vos réseaux, détectez les vulnérabilités
            et auditez le durcissement de vos systèmes — le tout depuis une seule plateforme,
            hébergée sur votre infrastructure.
          </p>
          <div className="mt-10 flex items-center justify-center gap-4">
            {isAuthenticated ? (
              <Link to="/dashboard" className="btn btn-primary btn-lg">
                Accéder au Dashboard
                <ArrowRight className="ml-2 h-5 w-5" />
              </Link>
            ) : (
              <>
                <Link to="/signup" className="btn btn-primary btn-lg">
                  Commencer
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Link>
                <a href="#modules" className="btn btn-secondary btn-lg">
                  Découvrir les modules
                </a>
              </>
            )}
          </div>
        </div>
      </section>

      {/* Bande de stats */}
      <div className="border-y border-gray-800 bg-gray-900">
        <div className="mx-auto grid max-w-6xl grid-cols-3 divide-x divide-gray-800 px-6">
          {[
            { label: 'Types de scans', value: '5' },
            { label: 'OS supportés (Hardening)', value: 'Linux · macOS · Windows' },
            { label: 'Sources CVE', value: 'NVD · CIRCL' },
          ].map((s) => (
            <div key={s.label} className="px-8 py-6 text-center">
              <div className="text-2xl font-bold text-white">{s.value}</div>
              <div className="mt-1 text-sm text-gray-400">{s.label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Modules — cartes avec photo */}
      <section id="modules" className="bg-gray-950 px-6 py-20">
        <div className="mx-auto max-w-6xl">
          <div className="mb-12 text-center">
            <h2 className="text-3xl font-bold text-white">Modules disponibles</h2>
            <p className="mt-3 text-gray-400">Tout ce dont vous avez besoin pour auditer et sécuriser votre SI.</p>
          </div>
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
            {modules.map((mod) => (
              <div
                key={mod.name}
                className="group overflow-hidden rounded-xl border border-gray-800 bg-gray-900 transition-all hover:border-primary-700 hover:shadow-lg hover:shadow-primary-900/20"
              >
                <div className="relative h-40 overflow-hidden">
                  <img
                    src={mod.img}
                    alt={mod.name}
                    className="h-full w-full object-cover transition-transform duration-500 group-hover:scale-105"
                    loading="lazy"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-gray-900 via-gray-900/60 to-transparent" />
                  <div className={`absolute bottom-3 left-3 inline-flex rounded-lg p-2 ${mod.color}`}>
                    <mod.icon className="h-5 w-5" />
                  </div>
                </div>
                <div className="p-5">
                  <h3 className="mb-2 text-base font-semibold text-white">{mod.name}</h3>
                  <p className="text-sm leading-relaxed text-gray-400">{mod.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Laptop mockup — photo réelle */}
      <section className="relative overflow-hidden bg-gray-950 px-6 py-20">
        <div className="mx-auto flex max-w-6xl flex-col items-center gap-12 lg:flex-row">
          <div className="flex-1">
            <h2 className="text-3xl font-bold text-white">
              Conçu pour les équipes sécurité
            </h2>
            <p className="mt-4 text-gray-400 leading-relaxed">
              Interface web claire et rapide, accessible depuis n'importe quel navigateur.
              Vos résultats de scan, vos actifs et vos rapports de conformité en un seul endroit.
            </p>
            <ul className="mt-6 space-y-3 text-sm text-gray-300">
              {[
                'Scans en temps réel avec suivi de progression',
                'Scoring automatique CVSS et grade de risque',
                'Audit SSH hardening en un clic',
                'Veille CVE directement depuis NVD/NIST',
                'Agent déployable sur Windows, Linux et macOS',
              ].map((item) => (
                <li key={item} className="flex items-center gap-2">
                  <span className="h-1.5 w-1.5 rounded-full bg-primary-400 flex-shrink-0" />
                  {item}
                </li>
              ))}
            </ul>
          </div>
          <div className="flex-1">
            <div className="overflow-hidden rounded-2xl border border-gray-700 shadow-2xl shadow-primary-900/20">
              <img
                src="https://images.unsplash.com/photo-1484557985045-edf25e08da73?auto=format&fit=crop&w=900&q=80"
                alt="Terminal cybersécurité"
                className="w-full object-cover"
                loading="lazy"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Valeurs */}
      <section className="border-t border-gray-800 bg-gray-900 px-6 py-20">
        <div className="mx-auto max-w-6xl">
          <div className="mb-12 text-center">
            <h2 className="text-3xl font-bold text-white">Notre approche</h2>
            <p className="mt-3 text-gray-400">Une cybersécurité maîtrisée, sans compromis.</p>
          </div>
          <div className="grid grid-cols-1 gap-8 md:grid-cols-3">
            {values.map((val) => (
              <div key={val.title} className="text-center">
                <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-primary-900/40 ring-1 ring-primary-700/50">
                  <val.icon className="h-7 w-7 text-primary-400" />
                </div>
                <h3 className="mb-2 text-lg font-semibold text-white">{val.title}</h3>
                <p className="text-sm leading-relaxed text-gray-400">{val.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-800 bg-gray-950 px-6 py-8">
        <div className="mx-auto flex max-w-6xl items-center justify-between">
          <div className="flex items-center gap-2">
            <img src="/logo-petrix-dark.svg" alt="Petrix" className="h-6 w-6" />
            <span className="text-sm font-medium text-gray-500">Petrix v0.1.0 — Open Source</span>
          </div>
          {!isAuthenticated && (
            <Link to="/signup" className="text-sm text-primary-400 hover:text-primary-300">
              Créer un compte →
            </Link>
          )}
        </div>
      </footer>
    </div>
  );
}
