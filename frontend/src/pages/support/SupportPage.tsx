/**
 * Page d'aide et de support de la plateforme Petrix.
 * Propose une FAQ interactive sur l'utilisation de l'application et un formulaire
 * de signalement (bug, suggestion, vulnérabilité) par email via mailto.
 */
import { useState } from 'react';
import {
  HelpCircle, ChevronDown, ChevronRight, Mail, GitBranch,
  BookOpen, AlertTriangle, Shield, FileCode, Download,
  MessageSquare, ExternalLink, CheckCircle2,
} from 'lucide-react';

// ─── FAQ ─────────────────────────────────────────────────────────────────────

const FAQ = [
  {
    q: "Comment lancer mon premier audit ?",
    a: `1. Allez sur la page "Systèmes" et cliquez sur "Ajouter un système".
2. Choisissez le nom et l'OS de la machine à auditer.
3. Cliquez sur "Auditer" → téléchargez l'agent correspondant (linux.sh, macos.sh ou windows.ps1).
4. Exécutez l'agent sur la machine cible avec les droits administrateur.
5. Importez le fichier XML généré via "Importer un rapport".
6. Le rapport et l'analyse IA sont disponibles dans "Rapport d'audit".`,
  },
  {
    q: "Que signifient les grades A / B / C / D / F ?",
    a: `Le score global (0–100) est calculé selon le référentiel ANSSI-BP-028 :
• A (≥ 90) : Excellent niveau de sécurité
• B (≥ 75) : Bon niveau, quelques points d'amélioration
• C (≥ 60) : Niveau acceptable, des mesures correctives sont recommandées
• D (≥ 40) : Niveau insuffisant, actions prioritaires requises
• F (< 40)  : Niveau critique — action immédiate nécessaire

Chaque finding FAIL déduit des points selon sa sévérité :
CRITICAL −15 pts · HIGH −8 pts · MEDIUM −3 pts · LOW −1 pt`,
  },
  {
    q: "L'analyse IA ne s'affiche pas — pourquoi ?",
    a: `L'analyse IA utilise Mistral AI. Si elle n'apparaît pas :
• La clé API Mistral n'est peut-être pas configurée (contacter l'administrateur).
• Le délai d'analyse est de quelques secondes après l'import — actualisez la page.
• Réimportez le rapport XML si l'analyse est toujours absente.`,
  },
  {
    q: "Puis-je auditer plusieurs systèmes en même temps ?",
    a: `Oui. Exécutez l'agent sur chaque machine cible indépendamment, puis importez chaque fichier XML séparément. Chaque import crée une nouvelle session d'audit liée au système correspondant (identifié par son hostname).`,
  },
  {
    q: "Comment interpréter les ports dangereux ?",
    a: `Dans l'onglet "Ports réseau" du rapport d'audit, les ports dangereux sont affichés avec une icône flamme 🔥. Ce sont des services exposés qui présentent un risque significatif :
FTP (21) · Telnet (23) · TFTP (69) · NetBIOS (135-139) · SMB (445)
MySQL (3306) · PostgreSQL (5432) · VNC (5900) · Redis (6379) · MongoDB (27017)

La remédiation recommandée est indiquée pour chaque port.`,
  },
  {
    q: "Qui peut voir quoi dans l'application ?",
    a: `• Admin : accès complet — tous les audits, utilisateurs, logs d'audit, paramètres.
• Auditeur : accès aux audits, rapports, vulnérabilités, logs d'audit.
• Analyste : lecture des audits et rapports, création de vulnérabilités.
• Lecteur : consultation uniquement (dashboard, assets, rapports).`,
  },
  {
    q: "Comment passer de GitLab à GitHub ?",
    a: `1. Créez un nouveau dépôt sur GitHub (github.com/new).
2. Dans le terminal, dans le dossier du projet :
   git remote rename origin gitlab
   git remote add origin https://github.com/VOTRE_USER/petrix.git
   git push -u origin main
3. Supprimez l'ancien remote si souhaité : git remote remove gitlab
4. Mettez à jour les liens dans le footer de l'application.`,
  },
];

/**
 * Entrée FAQ accordéon : affiche la question en titre et révèle la réponse au clic.
 * @param item - Paire question/réponse issue du tableau FAQ.
 */
function FaqItem({ item }: { item: typeof FAQ[0] }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
      <button
        onClick={() => setOpen(o => !o)}
        className="w-full flex items-center justify-between gap-3 px-5 py-4 text-left bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
      >
        <span className="font-medium text-gray-900 dark:text-white text-sm">{item.q}</span>
        {open ? <ChevronDown className="h-4 w-4 text-gray-400 shrink-0" /> : <ChevronRight className="h-4 w-4 text-gray-400 shrink-0" />}
      </button>
      {open && (
        <div className="px-5 py-4 bg-gray-50 dark:bg-gray-800/50 border-t border-gray-100 dark:border-gray-700">
          <pre className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap font-sans leading-relaxed">
            {item.a}
          </pre>
        </div>
      )}
    </div>
  );
}

// ─── Signalement ──────────────────────────────────────────────────────────────

/**
 * Formulaire de signalement : construit un lien mailto préformaté avec le type
 * (bug, feature, support, vulnérabilité) et le message, puis ouvre le client mail.
 */
function ReportForm() {
  const [type, setType] = useState('bug');
  const [msg, setMsg] = useState('');
  const [sent, setSent] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!msg.trim()) return;
    // Construire un mailto préformaté
    const subject = encodeURIComponent(`[Petrix ${type === 'bug' ? 'Bug' : type === 'feature' ? 'Feature Request' : 'Support'}]`);
    const body = encodeURIComponent(`Type : ${type}\n\nMessage :\n${msg}`);
    window.location.href = `mailto:nikirezi@outlook.fr?subject=${subject}&body=${body}`;
    setSent(true);
    setMsg('');
  };

  if (sent) {
    return (
      <div className="flex flex-col items-center gap-3 py-8 text-green-600 dark:text-green-400">
        <CheckCircle2 className="h-10 w-10" />
        <p className="font-semibold">Message envoyé — merci !</p>
        <button onClick={() => setSent(false)} className="text-xs text-gray-400 hover:underline">Nouveau message</button>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="label">Type de signalement</label>
        <select className="input" value={type} onChange={e => setType(e.target.value)}>
          <option value="bug">Bug / Erreur</option>
          <option value="feature">Suggestion d'amélioration</option>
          <option value="support">Demande d'assistance</option>
          <option value="security">Vulnérabilité de sécurité</option>
        </select>
      </div>
      <div>
        <label className="label">Message</label>
        <textarea
          className="input min-h-[120px] resize-y"
          placeholder="Décrivez votre problème ou suggestion en détail…"
          value={msg}
          onChange={e => setMsg(e.target.value)}
          required
        />
      </div>
      <button type="submit" disabled={!msg.trim()}
        className="btn btn-primary btn-md w-full">
        <Mail className="mr-2 h-4 w-4" /> Envoyer par e-mail
      </button>
      <p className="text-xs text-gray-400 text-center">
        Ouvre votre client mail avec le message pré-rempli à nikirezi@outlook.fr
      </p>
    </form>
  );
}

// ─── Ressources ───────────────────────────────────────────────────────────────

const RESOURCES = [
  { icon: Shield,    label: 'ANSSI-BP-028 v2.0',          href: 'https://www.ssi.gouv.fr/guide/recommandations-de-securite-relatives-a-un-systeme-gnulinux/', desc: 'Référentiel de durcissement GNU/Linux' },
  { icon: BookOpen,  label: 'CERT-FR — Alertes',           href: 'https://www.cert.ssi.gouv.fr/alerte/', desc: 'Alertes de sécurité CERT-FR' },
  { icon: AlertTriangle, label: 'CVE Database',            href: 'https://cve.mitre.org/', desc: 'Base de données des vulnérabilités CVE' },
  { icon: GitBranch, label: 'Dépôt GitLab Petrix',        href: 'https://gitlab.com/petrix1/petrix', desc: 'Code source du projet' },
];

// ─── Main ─────────────────────────────────────────────────────────────────────

/**
 * Page de support Petrix.
 * Compose la FAQ accordéon, le formulaire de signalement par email et les liens utiles
 * (documentation, GitLab, stack technique).
 */
export default function SupportPage() {
  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white flex items-center gap-2">
          <HelpCircle className="h-6 w-6 text-primary-600" /> Support & Aide
        </h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
          Foire aux questions, signalement et ressources
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* FAQ */}
        <div className="lg:col-span-2 space-y-3">
          <h2 className="text-base font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <MessageSquare className="h-4 w-4 text-primary-600" /> Questions fréquentes
          </h2>
          {FAQ.map((item, i) => <FaqItem key={i} item={item} />)}
        </div>

        {/* Colonne droite */}
        <div className="space-y-6">

          {/* Agent download quick links */}
          <div className="rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-700 dark:bg-gray-800">
            <h3 className="font-bold text-gray-900 dark:text-white text-sm mb-3 flex items-center gap-2">
              <Download className="h-4 w-4 text-primary-600" /> Agents d'audit
            </h3>
            <div className="space-y-2">
              {[
                { os: 'Linux',   param: 'linux',   ext: '.sh',   cmd: 'sudo bash petrix_agent_linux.sh' },
                { os: 'macOS',   param: 'macos',   ext: '.sh',   cmd: 'sudo bash petrix_agent_macos.sh' },
                { os: 'Windows', param: 'windows', ext: '.ps1',  cmd: '.\\petrix_agent_windows.ps1' },
              ].map(a => (
                <a
                  key={a.param}
                  href={`/api/v1/hardening/agent-script/${a.param}`}
                  download
                  className="flex items-center justify-between rounded-lg border border-gray-100 dark:border-gray-700 px-3 py-2 hover:border-primary-300 hover:bg-primary-50 dark:hover:bg-primary-900/10 transition-colors"
                >
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{a.os} {a.ext}</span>
                  <FileCode className="h-3.5 w-3.5 text-primary-600" />
                </a>
              ))}
            </div>
          </div>

          {/* Contact / Signalement */}
          <div className="rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-700 dark:bg-gray-800">
            <h3 className="font-bold text-gray-900 dark:text-white text-sm mb-4 flex items-center gap-2">
              <Mail className="h-4 w-4 text-primary-600" /> Signalement
            </h3>
            <ReportForm />
          </div>

          {/* Ressources */}
          <div className="rounded-xl border border-gray-200 bg-white p-5 dark:border-gray-700 dark:bg-gray-800">
            <h3 className="font-bold text-gray-900 dark:text-white text-sm mb-3 flex items-center gap-2">
              <BookOpen className="h-4 w-4 text-primary-600" /> Ressources
            </h3>
            <div className="space-y-2">
              {RESOURCES.map(r => (
                <a
                  key={r.label}
                  href={r.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-start gap-2.5 rounded-lg border border-gray-100 dark:border-gray-700 p-2.5 hover:border-primary-300 hover:bg-primary-50 dark:hover:bg-primary-900/10 transition-colors group"
                >
                  <r.icon className="h-4 w-4 text-primary-600 shrink-0 mt-0.5" />
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-semibold text-gray-800 dark:text-gray-200 group-hover:text-primary-700 dark:group-hover:text-primary-400">
                      {r.label}
                    </p>
                    <p className="text-xs text-gray-400">{r.desc}</p>
                  </div>
                  <ExternalLink className="h-3 w-3 text-gray-300 group-hover:text-primary-400 shrink-0 mt-0.5" />
                </a>
              ))}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
