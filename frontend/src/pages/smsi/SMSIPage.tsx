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
  ChevronRight,
  ArrowLeft,
  Search,
  Eye,
  BookOpen,
} from 'lucide-react';
import { api } from '../../api/client';
import { ProjectWizard } from '../../components/smsi/ProjectWizard';
import { ProjectDetail } from '../../components/smsi/ProjectDetail';
import toast from 'react-hot-toast';

type ActiveView = 'main' | 'frameworks' | 'templates' | 'projects' | 'documents';

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

interface Framework {
  id: string;
  code: string;
  name: string;
  version: string;
  description: string;
  category: string;
  region: string;
  is_mandatory: boolean;
  total_controls: number;
  total_requirements: number;
  icon?: string;
  color?: string;
}

interface Template {
  id: string;
  code: string;
  name: string;
  document_type: string;
  description: string;
  output_formats: string[];
  min_security_level: string;
  version: string;
  tags: string[];
}

interface GeneratedDocument {
  id: string;
  code: string;
  name: string;
  document_type: string;
  version: string;
  status: string;
  ai_model_used?: string;
  ai_tokens_input: number;
  ai_tokens_output: number;
  ai_generation_time: number;
  created_at: string;
}

export function SMSIPage() {
  const [showWizard, setShowWizard] = useState(false);
  const [selectedProject, setSelectedProject] = useState<string | null>(null);
  const [activeView, setActiveView] = useState<ActiveView>('main');
  const [searchTerm, setSearchTerm] = useState('');
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

  // Fetch frameworks
  const { data: frameworks, isLoading: frameworksLoading } = useQuery<Framework[]>({
    queryKey: ['smsi-frameworks'],
    queryFn: async () => {
      const response = await api.get('/smsi/frameworks');
      return response.data;
    },
    enabled: activeView === 'frameworks',
  });

  // Fetch templates
  const { data: templates, isLoading: templatesLoading } = useQuery<Template[]>({
    queryKey: ['smsi-templates'],
    queryFn: async () => {
      const response = await api.get('/smsi/templates');
      return response.data;
    },
    enabled: activeView === 'templates',
  });

  // Fetch all documents
  const { data: documents, isLoading: documentsLoading } = useQuery<GeneratedDocument[]>({
    queryKey: ['smsi-all-documents'],
    queryFn: async () => {
      const response = await api.get('/smsi/documents');
      return response.data;
    },
    enabled: activeView === 'documents',
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

  // Frameworks List View
  if (activeView === 'frameworks') {
    const filteredFrameworks = frameworks?.filter(fw =>
      fw.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      fw.code.toLowerCase().includes(searchTerm.toLowerCase())
    ) || [];

    return (
      <div className="p-6 space-y-6">
        <div className="flex items-center gap-4">
          <button
            onClick={() => { setActiveView('main'); setSearchTerm(''); }}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Référentiels</h1>
            <p className="text-gray-600 dark:text-gray-400">{frameworks?.length || 0} référentiels disponibles</p>
          </div>
        </div>

        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Rechercher un référentiel..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {frameworksLoading ? (
          <div className="p-8 text-center">
            <RefreshCw className="w-8 h-8 animate-spin mx-auto text-blue-500" />
            <p className="mt-2 text-gray-600 dark:text-gray-400">Chargement...</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredFrameworks.map((fw) => (
              <div
                key={fw.id}
                className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-5 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg">
                      <Shield className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-gray-900 dark:text-white">{fw.name}</h3>
                      <span className="text-xs text-gray-500 dark:text-gray-400">{fw.code}</span>
                    </div>
                  </div>
                  <span className={`px-2 py-1 text-xs rounded-full ${fw.is_mandatory ? 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300' : 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'}`}>
                    {fw.is_mandatory ? 'Obligatoire' : 'Optionnel'}
                  </span>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-3 line-clamp-2">{fw.description}</p>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-500 dark:text-gray-400">v{fw.version} • {fw.region.toUpperCase()}</span>
                  <span className="text-blue-600 dark:text-blue-400 font-medium">{fw.total_controls} contrôles</span>
                </div>
              </div>
            ))}
          </div>
        )}

        {!frameworksLoading && filteredFrameworks.length === 0 && (
          <div className="text-center py-12">
            <Shield className="w-12 h-12 mx-auto text-gray-300 dark:text-gray-600" />
            <p className="mt-4 text-gray-500 dark:text-gray-400">Aucun référentiel trouvé</p>
          </div>
        )}
      </div>
    );
  }

  // Templates List View
  if (activeView === 'templates') {
    const filteredTemplates = templates?.filter(t =>
      t.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      t.code.toLowerCase().includes(searchTerm.toLowerCase()) ||
      t.document_type.toLowerCase().includes(searchTerm.toLowerCase())
    ) || [];

    const documentTypes = [...new Set(templates?.map(t => t.document_type) || [])];

    return (
      <div className="p-6 space-y-6">
        <div className="flex items-center gap-4">
          <button
            onClick={() => { setActiveView('main'); setSearchTerm(''); }}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Templates</h1>
            <p className="text-gray-600 dark:text-gray-400">{templates?.length || 0} templates disponibles</p>
          </div>
        </div>

        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Rechercher un template..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {templatesLoading ? (
          <div className="p-8 text-center">
            <RefreshCw className="w-8 h-8 animate-spin mx-auto text-blue-500" />
            <p className="mt-2 text-gray-600 dark:text-gray-400">Chargement...</p>
          </div>
        ) : (
          <div className="space-y-6">
            {documentTypes.map(docType => {
              const typeTemplates = filteredTemplates.filter(t => t.document_type === docType);
              if (typeTemplates.length === 0) return null;

              const typeLabels: Record<string, string> = {
                DIRECTIVE: 'Directives Stratégiques',
                POLICY: 'Politiques',
                PROCEDURE: 'Procédures',
                REGISTER: 'Registres',
                RECORD: 'Enregistrements',
                GUIDE: 'Guides',
                CHARTER: 'Chartes',
                PLAN: 'Plans',
                REPORT: 'Rapports',
                ANNEX: 'Annexes',
              };

              return (
                <div key={docType}>
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-3 flex items-center gap-2">
                    <BookOpen className="w-5 h-5 text-purple-500" />
                    {typeLabels[docType] || docType}
                    <span className="text-sm font-normal text-gray-500">({typeTemplates.length})</span>
                  </h2>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {typeTemplates.map((template) => (
                      <div
                        key={template.id}
                        className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4 hover:shadow-md transition-shadow"
                      >
                        <div className="flex items-start gap-3 mb-2">
                          <div className="p-2 bg-purple-100 dark:bg-purple-900 rounded-lg">
                            <FileText className="w-4 h-4 text-purple-600 dark:text-purple-400" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <h3 className="font-medium text-gray-900 dark:text-white truncate">{template.name}</h3>
                            <span className="text-xs text-gray-500 dark:text-gray-400">{template.code}</span>
                          </div>
                        </div>
                        <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2 mb-2">{template.description}</p>
                        <div className="flex flex-wrap gap-1">
                          {template.tags?.slice(0, 3).map(tag => (
                            <span key={tag} className="inline-block px-2 py-0.5 text-xs bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded">
                              {tag}
                            </span>
                          ))}
                          <span className="inline-block px-2 py-0.5 text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded">
                            {template.output_formats?.join(', ')}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {!templatesLoading && filteredTemplates.length === 0 && (
          <div className="text-center py-12">
            <FileText className="w-12 h-12 mx-auto text-gray-300 dark:text-gray-600" />
            <p className="mt-4 text-gray-500 dark:text-gray-400">Aucun template trouvé</p>
          </div>
        )}
      </div>
    );
  }

  // Projects List View
  if (activeView === 'projects') {
    const filteredProjects = projects?.filter(p =>
      p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.organization_name.toLowerCase().includes(searchTerm.toLowerCase())
    ) || [];

    return (
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button
              onClick={() => { setActiveView('main'); setSearchTerm(''); }}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            >
              <ArrowLeft className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            </button>
            <div>
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Projets SMSI</h1>
              <p className="text-gray-600 dark:text-gray-400">{projects?.length || 0} projets</p>
            </div>
          </div>
          <button
            onClick={() => setShowWizard(true)}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <Plus className="w-5 h-5" />
            Nouveau projet
          </button>
        </div>

        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Rechercher un projet..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {projectsLoading ? (
          <div className="p-8 text-center">
            <RefreshCw className="w-8 h-8 animate-spin mx-auto text-blue-500" />
            <p className="mt-2 text-gray-600 dark:text-gray-400">Chargement...</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredProjects.map((project) => (
              <div
                key={project.id}
                onClick={() => setSelectedProject(project.id)}
                className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-5 hover:shadow-md transition-shadow cursor-pointer"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-3">
                    {getStatusIcon(project.status)}
                    <div>
                      <h3 className="font-semibold text-gray-900 dark:text-white">{project.name}</h3>
                      <span className="text-sm text-gray-500 dark:text-gray-400">{project.organization_name}</span>
                    </div>
                  </div>
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                    project.status === 'completed'
                      ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
                      : project.status === 'generation'
                      ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300'
                      : project.status === 'review'
                      ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'
                      : 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
                  }`}>
                    {getStatusLabel(project.status)}
                  </span>
                </div>

                <p className="text-sm text-gray-600 dark:text-gray-400 mb-3 line-clamp-2">{project.description}</p>

                <div className="flex items-center gap-2 mb-3 flex-wrap">
                  {project.selected_frameworks.slice(0, 3).map((fw) => (
                    <span key={fw} className="px-2 py-1 text-xs bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded">
                      {fw}
                    </span>
                  ))}
                  {project.selected_frameworks.length > 3 && (
                    <span className="px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded">
                      +{project.selected_frameworks.length - 3}
                    </span>
                  )}
                </div>

                <div className="flex items-center justify-between">
                  <div className="flex-1 mr-4">
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
                  <div className="text-center">
                    <p className="text-lg font-semibold text-gray-900 dark:text-white">
                      {project.documents_generated}/{project.documents_total}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">Docs</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {!projectsLoading && filteredProjects.length === 0 && (
          <div className="text-center py-12">
            <FolderOpen className="w-12 h-12 mx-auto text-gray-300 dark:text-gray-600" />
            <p className="mt-4 text-gray-500 dark:text-gray-400">Aucun projet trouvé</p>
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
    );
  }

  // Documents List View
  if (activeView === 'documents') {
    const filteredDocuments = documents?.filter(d =>
      d.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      d.code.toLowerCase().includes(searchTerm.toLowerCase())
    ) || [];

    const getDocStatusStyle = (status: string) => {
      switch (status) {
        case 'final': return 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300';
        case 'draft': return 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300';
        case 'review': return 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300';
        default: return 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300';
      }
    };

    const getDocTypeLabel = (type: string) => {
      const labels: Record<string, string> = {
        DIRECTIVE: 'Directive',
        POLICY: 'Politique',
        PROCEDURE: 'Procédure',
        REGISTER: 'Registre',
        RECORD: 'Enregistrement',
        GUIDE: 'Guide',
        CHARTER: 'Charte',
        PLAN: 'Plan',
        REPORT: 'Rapport',
        ANNEX: 'Annexe',
      };
      return labels[type] || type;
    };

    return (
      <div className="p-6 space-y-6">
        <div className="flex items-center gap-4">
          <button
            onClick={() => { setActiveView('main'); setSearchTerm(''); }}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Documents générés</h1>
            <p className="text-gray-600 dark:text-gray-400">{documents?.length || 0} documents</p>
          </div>
        </div>

        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Rechercher un document..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>

        {documentsLoading ? (
          <div className="p-8 text-center">
            <RefreshCw className="w-8 h-8 animate-spin mx-auto text-blue-500" />
            <p className="mt-2 text-gray-600 dark:text-gray-400">Chargement...</p>
          </div>
        ) : (
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-700">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Document</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Type</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Status</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Version</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Créé le</th>
                  <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {filteredDocuments.map((doc) => (
                  <tr key={doc.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <FileText className="w-5 h-5 text-orange-500" />
                        <div>
                          <p className="font-medium text-gray-900 dark:text-white">{doc.name}</p>
                          <p className="text-xs text-gray-500 dark:text-gray-400">{doc.code}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                      {getDocTypeLabel(doc.document_type)}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${getDocStatusStyle(doc.status)}`}>
                        {doc.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                      v{doc.version}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500 dark:text-gray-400">
                      {new Date(doc.created_at).toLocaleDateString('fr-FR')}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button className="p-1 hover:bg-gray-100 dark:hover:bg-gray-600 rounded transition-colors">
                          <Eye className="w-4 h-4 text-gray-500 dark:text-gray-400" />
                        </button>
                        <button className="p-1 hover:bg-gray-100 dark:hover:bg-gray-600 rounded transition-colors">
                          <Download className="w-4 h-4 text-gray-500 dark:text-gray-400" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {!documentsLoading && filteredDocuments.length === 0 && (
          <div className="text-center py-12">
            <Download className="w-12 h-12 mx-auto text-gray-300 dark:text-gray-600" />
            <p className="mt-4 text-gray-500 dark:text-gray-400">Aucun document trouvé</p>
          </div>
        )}
      </div>
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

      {/* Stats Cards - Clickable */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <button
          onClick={() => setActiveView('frameworks')}
          className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4 hover:shadow-md hover:border-blue-300 dark:hover:border-blue-600 transition-all cursor-pointer text-left group"
        >
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 dark:bg-blue-900 rounded-lg group-hover:scale-110 transition-transform">
              <Shield className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Référentiels</p>
              <p className="text-xl font-semibold text-gray-900 dark:text-white">{stats?.frameworks_available || 0}</p>
            </div>
            <ChevronRight className="w-4 h-4 text-gray-400 ml-auto opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
        </button>

        <button
          onClick={() => setActiveView('templates')}
          className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4 hover:shadow-md hover:border-purple-300 dark:hover:border-purple-600 transition-all cursor-pointer text-left group"
        >
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-100 dark:bg-purple-900 rounded-lg group-hover:scale-110 transition-transform">
              <FileText className="w-5 h-5 text-purple-600 dark:text-purple-400" />
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Templates</p>
              <p className="text-xl font-semibold text-gray-900 dark:text-white">{stats?.templates_available || 0}</p>
            </div>
            <ChevronRight className="w-4 h-4 text-gray-400 ml-auto opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
        </button>

        <button
          onClick={() => setActiveView('projects')}
          className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4 hover:shadow-md hover:border-green-300 dark:hover:border-green-600 transition-all cursor-pointer text-left group"
        >
          <div className="flex items-center gap-3">
            <div className="p-2 bg-green-100 dark:bg-green-900 rounded-lg group-hover:scale-110 transition-transform">
              <FolderOpen className="w-5 h-5 text-green-600 dark:text-green-400" />
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Projets</p>
              <p className="text-xl font-semibold text-gray-900 dark:text-white">{stats?.user_projects || 0}</p>
            </div>
            <ChevronRight className="w-4 h-4 text-gray-400 ml-auto opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
        </button>

        <button
          onClick={() => setActiveView('documents')}
          className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 p-4 hover:shadow-md hover:border-orange-300 dark:hover:border-orange-600 transition-all cursor-pointer text-left group"
        >
          <div className="flex items-center gap-3">
            <div className="p-2 bg-orange-100 dark:bg-orange-900 rounded-lg group-hover:scale-110 transition-transform">
              <Download className="w-5 h-5 text-orange-600 dark:text-orange-400" />
            </div>
            <div>
              <p className="text-sm text-gray-600 dark:text-gray-400">Documents</p>
              <p className="text-xl font-semibold text-gray-900 dark:text-white">{stats?.documents_generated || 0}</p>
            </div>
            <ChevronRight className="w-4 h-4 text-gray-400 ml-auto opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>
        </button>

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
