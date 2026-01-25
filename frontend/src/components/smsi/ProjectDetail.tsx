import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ArrowLeft,
  FileText,
  Play,
  Download,
  RefreshCw,
  CheckCircle,
  Clock,
  AlertCircle,
  Sparkles,
  Eye,
  Trash2,
  MoreVertical,
  Edit3,
  Package,
  ChevronDown,
} from 'lucide-react';
import { api } from '../../api/client';
import toast from 'react-hot-toast';
import { DocumentEditor } from './DocumentEditor';

interface ProjectDetailProps {
  projectId: string;
  onBack: () => void;
}

interface SMSIProject {
  id: string;
  name: string;
  description: string;
  status: string;
  organization_name: string;
  organization_type: string;
  organization_size: string;
  industry_sector: string;
  selected_frameworks: string[];
  security_level: string;
  pack_type: string;  // essential, standard, advanced
  completion_percentage: number;
  documents_generated: number;
  documents_total: number;
  created_at: string;
  updated_at: string;
}

interface GeneratedDocument {
  id: string;
  code: string;
  name: string;
  document_type: string;
  version: string;
  status: string;
  ai_model_used: string;
  ai_tokens_input: number;
  ai_tokens_output: number;
  ai_generation_time: number;
  created_at: string;
}

interface GenerationResult {
  project_id: string;
  generated: { id: string; code: string; name: string; status: string }[];
  errors: { template_code: string; error: string }[];
  stats: {
    total_templates: number;
    generated: number;
    failed: number;
    tokens_used: number;
    generation_time: number;
  };
}

// Pack information
const PACK_INFO = {
  essential: { name: 'Pack Essentiel', docs: '~20 documents', description: 'PME, démarrage rapide' },
  standard: { name: 'Pack Standard', docs: '~50 documents', description: 'ISO 27001 + RGPD complet' },
  advanced: { name: 'Pack Avancé', docs: '~100 documents', description: 'Multi-normes complet' },
};

export function ProjectDetail({ projectId, onBack }: ProjectDetailProps) {
  const queryClient = useQueryClient();
  const [isGenerating, setIsGenerating] = useState(false);
  const [selectedDocumentId, setSelectedDocumentId] = useState<string | null>(null);
  const [selectedPack, setSelectedPack] = useState<string>('advanced');  // Default to advanced
  const [showPackSelector, setShowPackSelector] = useState(false);

  // Fetch project details
  const { data: project, isLoading: projectLoading } = useQuery<SMSIProject>({
    queryKey: ['smsi-project', projectId],
    queryFn: async () => {
      const response = await api.get(`/smsi/projects/${projectId}`);
      return response.data;
    },
  });

  // Fetch project documents
  const { data: documents, isLoading: documentsLoading, refetch: refetchDocs } = useQuery<GeneratedDocument[]>({
    queryKey: ['smsi-project-documents', projectId],
    queryFn: async () => {
      const response = await api.get(`/smsi/projects/${projectId}/documents`);
      return response.data;
    },
  });

  // Generate documents mutation
  const generateMutation = useMutation({
    mutationFn: async (packType: string) => {
      const response = await api.post(`/smsi/projects/${projectId}/generate?pack_type=${packType}`);
      return response.data as GenerationResult;
    },
    onMutate: () => {
      setIsGenerating(true);
    },
    onSuccess: (result) => {
      setIsGenerating(false);
      queryClient.invalidateQueries({ queryKey: ['smsi-project', projectId] });
      queryClient.invalidateQueries({ queryKey: ['smsi-project-documents', projectId] });
      queryClient.invalidateQueries({ queryKey: ['smsi-projects'] });
      queryClient.invalidateQueries({ queryKey: ['smsi-stats'] });

      if (result.errors.length === 0) {
        toast.success(
          `${result.stats.generated} documents générés en ${result.stats.generation_time.toFixed(1)}s`
        );
      } else {
        toast.success(
          `${result.stats.generated} documents générés, ${result.stats.failed} erreurs`
        );
      }
    },
    onError: (error: any) => {
      setIsGenerating(false);
      toast.error(error.response?.data?.detail || 'Erreur lors de la génération');
    },
  });

  // Export document mutation
  const exportMutation = useMutation({
    mutationFn: async ({ documentId, format }: { documentId: string; format: string }) => {
      const response = await api.post(
        `/smsi/documents/${documentId}/export`,
        { format },
        { responseType: 'blob' }
      );
      return { blob: response.data, documentId, format };
    },
    onSuccess: ({ blob, documentId, format }) => {
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `document_${documentId}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      toast.success('Document exporté');
    },
    onError: () => {
      toast.error("Erreur lors de l'export");
    },
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'final':
      case 'approved':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'draft':
        return <Clock className="w-4 h-4 text-yellow-500" />;
      case 'review':
        return <AlertCircle className="w-4 h-4 text-blue-500" />;
      default:
        return <FileText className="w-4 h-4 text-gray-500" />;
    }
  };

  const getStatusLabel = (status: string) => {
    const labels: Record<string, string> = {
      draft: 'Brouillon',
      review: 'Révision',
      approved: 'Approuvé',
      final: 'Final',
    };
    return labels[status] || status;
  };

  const getDocTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      DIRECTIVE: 'Directive Stratégique',
      POLICY: 'Politique',
      PROCEDURE: 'Procédure',
      REGISTER: 'Registre',
      CHECKLIST: 'Checklist',
      ANNEX: 'Annexe',
      TEMPLATE: 'Template',
      SCHEMA: 'Schéma',
      REPORT: 'Rapport',
      MATRIX: 'Matrice',
    };
    return labels[type] || type;
  };

  const getSecurityLevelLabel = (level: string) => {
    const labels: Record<string, string> = {
      n1_standard: 'N1 - Standard',
      n2_reinforced: 'N2 - Renforcé',
      n3_critical: 'N3 - Critique',
    };
    return labels[level] || level;
  };

  if (projectLoading) {
    return (
      <div className="p-8 text-center">
        <RefreshCw className="w-8 h-8 animate-spin mx-auto text-blue-500" />
        <p className="mt-2 text-gray-600 dark:text-gray-400">Chargement du projet...</p>
      </div>
    );
  }

  if (!project) {
    return (
      <div className="p-8 text-center">
        <AlertCircle className="w-8 h-8 mx-auto text-red-500" />
        <p className="mt-2 text-gray-600 dark:text-gray-400">Projet introuvable</p>
        <button onClick={onBack} className="mt-4 text-blue-600 dark:text-blue-400 hover:underline">
          Retour
        </button>
      </div>
    );
  }

  // Afficher l'éditeur de document si un document est sélectionné
  if (selectedDocumentId) {
    return (
      <DocumentEditor
        documentId={selectedDocumentId}
        onBack={() => {
          setSelectedDocumentId(null);
          refetchDocs(); // Rafraîchir la liste des documents après édition
        }}
      />
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={onBack}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{project.name}</h1>
            <p className="text-gray-600 dark:text-gray-400">{project.organization_name}</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Pack Selector */}
          <div className="relative">
            <button
              onClick={() => setShowPackSelector(!showPackSelector)}
              className="flex items-center gap-2 px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
            >
              <Package className="w-4 h-4" />
              <span>{PACK_INFO[selectedPack as keyof typeof PACK_INFO]?.name || 'Pack Avancé'}</span>
              <ChevronDown className="w-4 h-4" />
            </button>

            {showPackSelector && (
              <div className="absolute right-0 mt-2 w-72 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 z-50">
                {Object.entries(PACK_INFO).map(([key, info]) => (
                  <button
                    key={key}
                    onClick={() => {
                      setSelectedPack(key);
                      setShowPackSelector(false);
                    }}
                    className={`w-full text-left px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors first:rounded-t-lg last:rounded-b-lg ${
                      selectedPack === key ? 'bg-blue-50 dark:bg-blue-900/30' : ''
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-gray-900 dark:text-white">{info.name}</span>
                      <span className="text-sm text-blue-600 dark:text-blue-400 font-semibold">{info.docs}</span>
                    </div>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">{info.description}</p>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Generate Button */}
          <button
            onClick={() => generateMutation.mutate(selectedPack)}
            disabled={isGenerating || project.status === 'generation'}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${
              isGenerating || project.status === 'generation'
                ? 'bg-gray-100 dark:bg-gray-700 text-gray-400 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
          >
            {isGenerating ? (
              <>
                <RefreshCw className="w-5 h-5 animate-spin" />
                Génération en cours...
              </>
            ) : (
              <>
                <Sparkles className="w-5 h-5" />
                Générer les documents
              </>
            )}
          </button>
        </div>
      </div>

      {/* Project Info Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4">
          <p className="text-sm text-gray-600 dark:text-gray-400">Statut</p>
          <p className="text-lg font-semibold capitalize text-gray-900 dark:text-white">{project.status}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4">
          <p className="text-sm text-gray-600 dark:text-gray-400">Niveau de sécurité</p>
          <p className="text-lg font-semibold text-gray-900 dark:text-white">{getSecurityLevelLabel(project.security_level)}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4">
          <p className="text-sm text-gray-600 dark:text-gray-400">Référentiels</p>
          <p className="text-lg font-semibold text-gray-900 dark:text-white">{project.selected_frameworks.length}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4">
          <p className="text-sm text-gray-600 dark:text-gray-400">Documents</p>
          <p className="text-lg font-semibold text-gray-900 dark:text-white">
            {project.documents_generated} / {project.documents_total}
          </p>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Progression</span>
          <span className="text-sm font-medium text-gray-900 dark:text-white">{project.completion_percentage}%</span>
        </div>
        <div className="h-3 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-blue-500 to-blue-600 transition-all duration-500"
            style={{ width: `${project.completion_percentage}%` }}
          />
        </div>
      </div>

      {/* Frameworks */}
      {project.selected_frameworks.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4">
          <h3 className="font-medium text-gray-900 dark:text-white mb-3">Référentiels sélectionnés</h3>
          <div className="flex flex-wrap gap-2">
            {project.selected_frameworks.map((fw) => (
              <span
                key={fw}
                className="px-3 py-1 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded-full text-sm font-medium"
              >
                {fw}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Generated Documents */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Documents générés</h2>
          <button
            onClick={() => refetchDocs()}
            className="p-2 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>

        {documentsLoading ? (
          <div className="p-8 text-center">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto text-blue-500" />
          </div>
        ) : documents && documents.length > 0 ? (
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {documents.map((doc) => (
              <div key={doc.id} className="p-4 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                <div className="flex items-center justify-between">
                  <div
                    className="flex items-center gap-3 flex-1 cursor-pointer"
                    onClick={() => setSelectedDocumentId(doc.id)}
                  >
                    {getStatusIcon(doc.status)}
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-white hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
                        {doc.name}
                      </h4>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {doc.code} • {getDocTypeLabel(doc.document_type)} • v{doc.version}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-4">
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      {doc.ai_tokens_input + doc.ai_tokens_output} tokens •{' '}
                      {doc.ai_generation_time.toFixed(1)}s
                    </span>

                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => setSelectedDocumentId(doc.id)}
                        className="p-2 text-blue-500 hover:text-blue-700 hover:bg-blue-50 dark:hover:bg-blue-900/50 rounded-lg transition-colors"
                        title="Éditer le document"
                      >
                        <Edit3 className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => exportMutation.mutate({ documentId: doc.id, format: 'md' })}
                        className="p-2 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                        title="Télécharger en Markdown"
                      >
                        <Download className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => exportMutation.mutate({ documentId: doc.id, format: 'docx' })}
                        className="px-3 py-1 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded text-sm font-medium hover:bg-blue-200 dark:hover:bg-blue-800 transition-colors"
                      >
                        DOCX
                      </button>
                      <button
                        onClick={() => exportMutation.mutate({ documentId: doc.id, format: 'pdf' })}
                        className="px-3 py-1 bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300 rounded text-sm font-medium hover:bg-red-200 dark:hover:bg-red-800 transition-colors"
                      >
                        PDF
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-12 text-center">
            <FileText className="w-12 h-12 mx-auto text-gray-300 dark:text-gray-600" />
            <h3 className="mt-4 text-lg font-medium text-gray-900 dark:text-white">Aucun document généré</h3>
            <p className="mt-2 text-gray-500 dark:text-gray-400">
              Sélectionnez un pack et cliquez sur "Générer les documents" pour créer votre SMSI
            </p>

            {/* Pack Selection Cards */}
            <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4 max-w-3xl mx-auto">
              {Object.entries(PACK_INFO).map(([key, info]) => (
                <button
                  key={key}
                  onClick={() => setSelectedPack(key)}
                  className={`p-4 rounded-lg border-2 transition-all text-left ${
                    selectedPack === key
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/30'
                      : 'border-gray-200 dark:border-gray-700 hover:border-blue-300 dark:hover:border-blue-600'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold text-gray-900 dark:text-white">{info.name}</span>
                    {selectedPack === key && (
                      <CheckCircle className="w-5 h-5 text-blue-500" />
                    )}
                  </div>
                  <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">{info.docs}</p>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{info.description}</p>
                </button>
              ))}
            </div>

            <button
              onClick={() => generateMutation.mutate(selectedPack)}
              disabled={isGenerating}
              className="mt-6 inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 font-medium"
            >
              <Sparkles className="w-5 h-5" />
              Générer {PACK_INFO[selectedPack as keyof typeof PACK_INFO]?.docs || '~100 documents'}
            </button>
          </div>
        )}
      </div>

      {/* Generation in progress indicator */}
      {isGenerating && (
        <div className="fixed bottom-4 right-4 bg-blue-600 text-white px-4 py-3 rounded-lg shadow-lg flex items-center gap-3">
          <RefreshCw className="w-5 h-5 animate-spin" />
          <div>
            <p className="font-medium">Génération en cours...</p>
            <p className="text-sm text-blue-200">
              Mistral AI génère vos documents ({PACK_INFO[selectedPack as keyof typeof PACK_INFO]?.docs || '~100'})
            </p>
          </div>
        </div>
      )}

      {/* Click outside to close pack selector */}
      {showPackSelector && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => setShowPackSelector(false)}
        />
      )}
    </div>
  );
}
