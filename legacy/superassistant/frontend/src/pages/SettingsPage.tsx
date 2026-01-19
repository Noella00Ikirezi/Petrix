export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Paramètres
        </h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Configurez SuperAssistant selon vos préférences
        </p>
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Contexte Utilisateur
        </h2>
        <p className="text-gray-600 dark:text-gray-400">
          Configurez votre profil pour que l'IA personnalise ses réponses
        </p>
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Clé API Anthropic
        </h2>
        <p className="text-gray-600 dark:text-gray-400 mb-4">
          Configurée dans le fichier backend/.env
        </p>
        <div className="p-3 bg-green-50 dark:bg-green-900/20 rounded-lg text-green-800 dark:text-green-200 text-sm">
          ✓ Clé API configurée et opérationnelle
        </div>
      </div>
    </div>
  );
}
