import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  FileText,
  Plus,
  FolderOpen,
  Shield,
  Download,
  RefreshCw,
  CheckCircle,
  Clock,
  AlertCircle,
  Sparkles,
  Settings,
  ChevronRight,
} from 'lucide-react';
import { api } from '../../api/client';
import { ProjectWizard } from '../../components/smsi/ProjectWizard';
import { ProjectDetail } from '../../components/smsi/ProjectDetail';
import toast from 'react-hot-toast';

interface SMSIProject {
  id: string;
  name: string;
  description: string;
  status: string;
  organization_name: string;
  selected_frameworks: string[];
  security_level: string;
  completion_percentage: number;
  documents_generated: number;
  documents_total: number;
  created_at: string;
}

interface SMSIStats {
  frameworks_available: number;
  templates_available: number;
  user_projects: number;
  documents_generated: number;
  ai_tokens_used: number;
}

export function SMSIPage() {
  const [showWizard, setShowWizard] = useState(false);
  const [selectedProject, setSelectedProject] = useState<string | null>(null);
  const queryClient = useQueryClient();

  // Fetch projects
  const { data: projects, isLoading: projectsLoading } = useQuery<SMSIProject[]>({
    queryKey: ['smsi-projects'],
    queryFn: async () => {
      const response = await api.get('/smsi/projects');
      return response.data;
    },
  });

  // Fetch stats
  const { data: stats } = useQuery<SMSIStats>({
    queryKey: ['smsi-stats'],
    queryFn: async () => {
      const response = await api.get('/smsi/stats');
      return response.data;
    },
  });

  // Delete project mutation
  const deleteMutation = useMutation({
    mutationFn: async (projectId: string) => {
      await api.delete(`/smsi/projects/${projectId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['smsi-projects'] });
      queryClient.invalidateQueries({ queryKey: ['smsi-stats'] });
      toast.success('Projet supprimé');
    },
    onError: () => {
      toast.error('Erreur lors de la suppression');
    },
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'generation':
      case 'assessment':
        return <Clock className="w-5 h-5 text-yellow-500" />;
      case 'review':
        return <AlertCircle className="w-5 h-5 text-blue-500" />;
      default:
        return <FileText className="w-5 h-5 text-gray-500" />;
    }
  };

  const getStatusLabel = (status: string) => {
    const labels: Record<string, string> = {
      created: 'Créé',
      assessment: 'Évaluation',
      generation: 'Génération',
      review: 'Révision',
      completed: 'Terminé',
      archived: 'Archivé',
    };
    return labels[status] || status;
  };

  if (showWizard) {
    return (
      <ProjectWizard
        onClose={() => setShowWizard(false)}
        onComplete={() => {
          setShowWizard(false);
          queryClient.invalidateQueries({ queryKey: ['smsi-projects'] });
          queryClient.invalidateQueries({ queryKey: ['smsi-stats'] });
        }}
      />
    );
  }

  if (selectedProject) {
    return (
      <ProjectDetail
        projectId={selectedProject}
        onBack={() => setSelectedProject(null)}
      />
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">SMSI Generator</h1>
          <p className="text-gray-600 dark:text-gray-300 mt-1">
            Générez votre Système de Management de la Sécurité de l'Information avec l'IA
          </p>
        </div>
        <button
          onClick={() => setShowWizard(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          <Plus className="w-5 h-5" />
          Nouveau SMSI
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
              <Shield className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Référentiels</p>
              <p className="text-xl font-semibold text-gray-900 dark:text-white">{stats?.frameworks_available || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-100 dark:bg-purple-900 rounded-lg">
              <FileText className="w-5 h-5 text-purple-600 dark:text-purple-400" />
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Templates</p>
              <p className="text-xl font-semibold text-gray-900 dark:text-white">{stats?.templates_available || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-100 dark:bg-green-900 rounded-lg">
              <FolderOpen className="w-5 h-5 text-green-600 dark:text-green-400" />
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Projets</p>
              <p className="text-xl font-semibold text-gray-900 dark:text-white">{stats?.user_projects || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-orange-100 dark:bg-orange-900 rounded-lg">
              <Download className="w-5 h-5 text-orange-600 dark:text-orange-400" />
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Documents</p>
              <p className="text-xl font-semibold text-gray-900 dark:text-white">{stats?.documents_generated || 0}</p>
            </div>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-cyan-100 dark:bg-cyan-900 rounded-lg">
              <Sparkles className="w-5 h-5 text-cyan-600 dark:text-cyan-400" />
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Tokens IA</p>
              <p className="text-xl font-semibold text-gray-900 dark:text-white">
                {stats?.ai_tokens_used ? (stats.ai_tokens_used / 1000).toFixed(1) + 'k' : '0'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Frameworks Overview */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-6">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2 text-gray-900 dark:text-white">
          <Shield className="w-5 h-5 text-blue-600 dark:text-blue-400" />
          Référentiels supportés
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3">
          {[
            { name: 'ISO 27001', color: 'bg-blue-500' },
            { name: 'DORA', color: 'bg-purple-500' },
            { name: 'NIS2', color: 'bg-indigo-500' },
            { name: 'RGPD', color: 'bg-green-500' },
            { name: 'PCI DSS', color: 'bg-orange-500' },
            { name: 'EU AI Act', color: 'bg-pink-500' },
            { name: 'NIST CSF', color: 'bg-cyan-500' },
          ].map((fw) => (
            <div
              key={fw.name}
              className="flex items-center gap-2 p-2 rounded-lg bg-gray-50 dark:bg-gray-700 hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
            >
              <div className={`w-2 h-2 rounded-full ${fw.color}`} />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-200">{fw.name}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Projects List */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex justify-between items-center">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Mes projets SMSI</h2>
          <button
            onClick={() => queryClient.invalidateQueries({ queryKey: ['smsi-projects'] })}
            className="p-2 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>

        {projectsLoading ? (
          <div className="p-8 text-center">
            <RefreshCw className="w-8 h-8 animate-spin mx-auto text-blue-500" />
            <p className="mt-2 text-gray-600 dark:text-gray-400">Chargement...</p>
          </div>
        ) : projects && projects.length > 0 ? (
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {projects.map((project) => (
              <div
                key={project.id}
                className="p-4 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors cursor-pointer"
                onClick={() => setSelectedProject(project.id)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    {getStatusIcon(project.status)}
                    <div>
                      <h3 className="font-medium text-gray-900 dark:text-white">{project.name}</h3>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {project.organization_name} • {project.selected_frameworks.length} référentiels
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-6">
                    {/* Progress */}
                    <div className="w-32">
                      <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mb-1">
                        <span>Progression</span>
                        <span>{project.completion_percentage}%</span>
                      </div>
                      <div className="h-2 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-blue-500 transition-all duration-300"
                          style={{ width: `${project.completion_percentage}%` }}
                        />
                      </div>
                    </div>

                    {/* Documents count */}
                    <div className="text-center">
                      <p className="text-lg font-semibold text-gray-900 dark:text-white">
                        {project.documents_generated}/{project.documents_total}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">Documents</p>
                    </div>

                    {/* Status badge */}
                    <span
                      className={`px-3 py-1 text-xs font-medium rounded-full ${
                        project.status === 'completed'
                          ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
                          : project.status === 'generation'
                          ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300'
                          : project.status === 'review'
                          ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'
                          : 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
                      }`}
                    >
                      {getStatusLabel(project.status)}
                    </span>

                    <ChevronRight className="w-5 h-5 text-gray-400" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="p-12 text-center">
            <FolderOpen className="w-12 h-12 mx-auto text-gray-300 dark:text-gray-600" />
            <h3 className="mt-4 text-lg font-medium text-gray-900 dark:text-white">Aucun projet SMSI</h3>
            <p className="mt-2 text-gray-500 dark:text-gray-400">
              Créez votre premier projet pour générer un SMSI complet avec l'IA
            </p>
            <button
              onClick={() => setShowWizard(true)}
              className="mt-4 inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              <Plus className="w-4 h-4" />
              Créer un projet
            </button>
          </div>
        )}
      </div>

      {/* Features Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-lg p-6 text-white">
          <Sparkles className="w-8 h-8 mb-3" />
          <h3 className="text-lg font-semibold mb-2">Génération IA</h3>
          <p className="text-blue-100 text-sm">
            Documents générés par Mistral AI, modèle européen open-source respectant le RGPD
          </p>
        </div>

        <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-lg p-6 text-white">
          <Shield className="w-8 h-8 mb-3" />
          <h3 className="text-lg font-semibold mb-2">Multi-normes</h3>
          <p className="text-purple-100 text-sm">
            ISO 27001, DORA, NIS2, RGPD, PCI DSS, EU AI Act et autres référentiels intégrés
          </p>
        </div>

        <div className="bg-gradient-to-br from-green-500 to-green-600 rounded-lg p-6 text-white">
          <Download className="w-8 h-8 mb-3" />
          <h3 className="text-lg font-semibold mb-2">Export multi-format</h3>
          <p className="text-green-100 text-sm">
            DOCX, PDF, Excel, HTML, Markdown, PowerPoint et CSV disponibles
          </p>
        </div>
      </div>
    </div>
  );
}
