import { Link } from 'react-router-dom';
import {
  Server,
  Shield,
  Crosshair,
  Sparkles,
  ClipboardList,
  Building2,
  ArrowRight,
  Lock,
  Globe,
  Cpu,
  LayoutDashboard,
} from 'lucide-react';
import { useAuthStore } from '@/stores/authStore';

const modules = [
  {
    name: 'Asset Management',
    description: 'Inventaire complet et suivi en temps reel de vos actifs IT, serveurs, applications et infrastructures.',
    icon: Server,
    color: 'bg-blue-100 text-blue-600 dark:bg-blue-900/40 dark:text-blue-400',
  },
  {
    name: 'Vulnerability Scanner',
    description: 'Detection automatique des vulnerabilites avec scoring CVSS, priorisation et suivi de remediation.',
    icon: Shield,
    color: 'bg-red-100 text-red-600 dark:bg-red-900/40 dark:text-red-400',
  },
  {
    name: 'Pentest Automation',
    description: 'Tests d\'intrusion automatises assistes par IA : scan Nmap, analyse de surface d\'attaque, rapports detailles.',
    icon: Crosshair,
    color: 'bg-orange-100 text-orange-600 dark:bg-orange-900/40 dark:text-orange-400',
  },
  {
    name: 'SMSI Generator',
    description: 'Generation automatique de documentation ISO 27001 : politiques, procedures, declarations d\'applicabilite.',
    icon: Sparkles,
    color: 'bg-purple-100 text-purple-600 dark:bg-purple-900/40 dark:text-purple-400',
  },
  {
    name: 'Compliance & Audit',
    description: 'Logs d\'audit exhaustifs, conformite reglementaire, tracabilite de toutes les actions utilisateurs.',
    icon: ClipboardList,
    color: 'bg-green-100 text-green-600 dark:bg-green-900/40 dark:text-green-400',
  },
  {
    name: 'Client Management',
    description: 'Gestion multi-client pour consultants et MSSP : contextes isoles, rapports par client, vue consolidee.',
    icon: Building2,
    color: 'bg-cyan-100 text-cyan-600 dark:bg-cyan-900/40 dark:text-cyan-400',
  },
];

const values = [
  {
    icon: Lock,
    title: 'Souverainete numerique',
    description: 'Aucune dependance cloud externe. Vos donnees restent sur votre infrastructure, sous votre controle total.',
  },
  {
    icon: Cpu,
    title: 'IA integree',
    description: 'Modeles open-source auto-heberges (Ollama) pour l\'enrichissement des vulnerabilites et l\'analyse de risques.',
  },
  {
    icon: Globe,
    title: '100% Open Source',
    description: 'Code source ouvert, auditable et personnalisable. Contribuez au projet et adaptez-le a vos besoins.',
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
            <span className="text-xl font-bold text-petrix-void dark:text-petrix-cyan-light">
              Petrix
            </span>
          </div>
          <div className="flex items-center gap-3">
            {isAuthenticated ? (
              <Link
                to="/dashboard"
                className="btn btn-primary btn-md"
              >
                <LayoutDashboard className="mr-2 h-4 w-4" />
                Dashboard
              </Link>
            ) : (
              <Link to="/signup" className="btn btn-primary btn-md">
                Sign up
              </Link>
            )}
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="px-6 py-20 text-center">
        <div className="mx-auto max-w-3xl">
          <div className="mb-6 inline-flex items-center rounded-full border border-primary-200 bg-primary-50 px-4 py-1.5 text-sm font-medium text-primary-700 dark:border-primary-800 dark:bg-primary-900/30 dark:text-primary-300">
            Open Source &middot; Self-Hosted &middot; Souverain
          </div>
          <h1 className="text-5xl font-bold tracking-tight text-petrix-void dark:text-white">
            La plateforme
            <br />
            <span className="text-primary-600 dark:text-petrix-cyan-light">tout-en-un</span>
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg text-gray-600 dark:text-gray-400">
            Securite, conformite et pentest reunis dans une seule plateforme.
            Gerez vos actifs, detectez les vulnerabilites, automatisez vos audits
            et generez votre documentation ISO 27001 — le tout sans dependance cloud.
          </p>
          <div className="mt-10 flex items-center justify-center gap-4">
            {isAuthenticated ? (
              <Link to="/dashboard" className="btn btn-primary btn-lg">
                Acceder au Dashboard
                <ArrowRight className="ml-2 h-5 w-5" />
              </Link>
            ) : (
              <>
                <Link to="/signup" className="btn btn-primary btn-lg">
                  Commencer
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Link>
                <a
                  href="#modules"
                  className="btn btn-secondary btn-lg"
                >
                  Decouvrir les modules
                </a>
              </>
            )}
          </div>
        </div>
      </section>

      {/* Modules */}
      <section id="modules" className="border-t border-gray-200 bg-gray-50 px-6 py-20 dark:border-gray-800 dark:bg-gray-900/50">
        <div className="mx-auto max-w-6xl">
          <div className="mb-12 text-center">
            <h2 className="text-3xl font-bold text-petrix-void dark:text-white">
              Modules integres
            </h2>
            <p className="mt-3 text-gray-600 dark:text-gray-400">
              Tout ce dont vous avez besoin pour securiser et auditer votre SI.
            </p>
          </div>
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
            {modules.map((mod) => (
              <div
                key={mod.name}
                className="rounded-xl border border-gray-200 bg-white p-6 transition-shadow hover:shadow-md dark:border-gray-700 dark:bg-gray-800"
              >
                <div className={`mb-4 inline-flex rounded-lg p-3 ${mod.color}`}>
                  <mod.icon className="h-6 w-6" />
                </div>
                <h3 className="mb-2 text-lg font-semibold text-gray-900 dark:text-white">
                  {mod.name}
                </h3>
                <p className="text-sm leading-relaxed text-gray-600 dark:text-gray-400">
                  {mod.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Values / Ambition */}
      <section className="px-6 py-20">
        <div className="mx-auto max-w-6xl">
          <div className="mb-12 text-center">
            <h2 className="text-3xl font-bold text-petrix-void dark:text-white">
              Notre ambition
            </h2>
            <p className="mt-3 text-gray-600 dark:text-gray-400">
              Une approche differente de la cybersecurite.
            </p>
          </div>
          <div className="grid grid-cols-1 gap-8 md:grid-cols-3">
            {values.map((val) => (
              <div key={val.title} className="text-center">
                <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-primary-100 dark:bg-primary-900/40">
                  <val.icon className="h-7 w-7 text-primary-600 dark:text-primary-400" />
                </div>
                <h3 className="mb-2 text-lg font-semibold text-gray-900 dark:text-white">
                  {val.title}
                </h3>
                <p className="text-sm leading-relaxed text-gray-600 dark:text-gray-400">
                  {val.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-200 px-6 py-8 dark:border-gray-800">
        <div className="mx-auto flex max-w-6xl items-center justify-between">
          <div className="flex items-center gap-2">
            <img src="/logo-petrix.svg" alt="Petrix" className="h-6 w-6 dark:hidden" />
            <img src="/logo-petrix-dark.svg" alt="Petrix" className="hidden h-6 w-6 dark:block" />
            <span className="text-sm font-medium text-gray-500 dark:text-gray-400">
              Petrix v0.1.0
            </span>
          </div>
          {!isAuthenticated && (
            <Link to="/signup" className="text-sm text-primary-600 hover:text-primary-700 dark:text-primary-400">
              Sign up
            </Link>
          )}
        </div>
      </footer>
    </div>
  );
}
