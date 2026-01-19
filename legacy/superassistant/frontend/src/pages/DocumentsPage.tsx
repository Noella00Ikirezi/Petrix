import { useState } from 'react';
import { aiAPI, documentsAPI } from '../api/client';
import toast from 'react-hot-toast';
import { FileText, Sparkles } from 'lucide-react';

export default function DocumentsPage() {
  const [generating, setGenerating] = useState(false);
  const [generatedDoc, setGeneratedDoc] = useState<any>(null);
  const [formData, setFormData] = useState({
    doc_type: 'politique',
    title: '',
    scope: '',
    requirements: [''],
  });

  const generateDocument = async () => {
    if (!formData.title || !formData.scope) {
      toast.error('Veuillez remplir tous les champs requis');
      return;
    }

    setGenerating(true);
    try {
      const response = await aiAPI.generateDocument({
        ...formData,
        requirements: formData.requirements.filter(r => r.trim() !== ''),
      });
      setGeneratedDoc(response.data);
      toast.success('Document généré avec succès !');
    } catch (error) {
      toast.error('Erreur lors de la génération');
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Documents SMSI
        </h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Générez des documents conformes ISO 27001 / ANSSI
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Formulaire de génération */}
        <div className="card">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
            <Sparkles className="inline w-6 h-6 mr-2 text-primary-600" />
            Générateur IA
          </h2>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Type de document
              </label>
              <select
                className="select"
                value={formData.doc_type}
                onChange={(e) => setFormData({...formData, doc_type: e.target.value})}
              >
                <option value="politique">Politique de sécurité</option>
                <option value="procedure">Procédure</option>
                <option value="guide">Guide utilisateur</option>
                <option value="registre">Registre</option>
                <option value="rapport">Rapport d'audit</option>
                <option value="cr">Compte-rendu</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Titre
              </label>
              <input
                type="text"
                className="input"
                placeholder="Ex: Politique de gestion des mots de passe"
                value={formData.title}
                onChange={(e) => setFormData({...formData, title: e.target.value})}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Périmètre/Contexte
              </label>
              <textarea
                className="textarea"
                rows={3}
                placeholder="Décrivez le périmètre et le contexte du document..."
                value={formData.scope}
                onChange={(e) => setFormData({...formData, scope: e.target.value})}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Exigences spécifiques
              </label>
              {formData.requirements.map((req, index) => (
                <input
                  key={index}
                  type="text"
                  className="input mb-2"
                  placeholder="Ex: Conformité RGPD"
                  value={req}
                  onChange={(e) => {
                    const newReqs = [...formData.requirements];
                    newReqs[index] = e.target.value;
                    setFormData({...formData, requirements: newReqs});
                  }}
                />
              ))}
              <button
                onClick={() => setFormData({...formData, requirements: [...formData.requirements, '']})}
                className="btn btn-secondary text-sm"
              >
                + Ajouter une exigence
              </button>
            </div>

            <button
              onClick={generateDocument}
              disabled={generating}
              className="btn btn-primary w-full"
            >
              {generating ? 'Génération en cours...' : 'Générer le document'}
            </button>
          </div>
        </div>

        {/* Aperçu du document */}
        <div className="card">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-4">
            <FileText className="inline w-6 h-6 mr-2" />
            Aperçu
          </h2>

          {generatedDoc ? (
            <div className="space-y-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                  {generatedDoc.title}
                </h3>
              </div>

              <div className="prose dark:prose-invert max-w-none">
                <pre className="whitespace-pre-wrap text-sm bg-gray-50 dark:bg-gray-900 p-4 rounded-lg overflow-auto max-h-96">
                  {generatedDoc.content}
                </pre>
              </div>

              {generatedDoc.compliance_notes && generatedDoc.compliance_notes.length > 0 && (
                <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                  <h4 className="font-semibold text-blue-900 dark:text-blue-300 mb-2">
                    Notes de conformité
                  </h4>
                  <ul className="list-disc list-inside text-sm text-blue-800 dark:text-blue-200">
                    {generatedDoc.compliance_notes.map((note: string, i: number) => (
                      <li key={i}>{note}</li>
                    ))}
                  </ul>
                </div>
              )}

              <button
                onClick={async () => {
                  try {
                    await documentsAPI.create({
                      title: generatedDoc.title,
                      type: formData.doc_type,
                      content: generatedDoc.content,
                      status: 'draft',
                    });
                    toast.success('Document sauvegardé !');
                  } catch (error) {
                    toast.error('Erreur lors de la sauvegarde');
                  }
                }}
                className="btn btn-primary w-full"
              >
                Sauvegarder le document
              </button>
            </div>
          ) : (
            <div className="text-center text-gray-500 dark:text-gray-400 py-12">
              Générez un document pour voir l'aperçu
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
