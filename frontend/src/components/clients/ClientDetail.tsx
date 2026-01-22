import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ArrowLeft,
  Building2,
  FileText,
  ClipboardCheck,
  AlertTriangle,
  CheckCircle,
  Clock,
  Plus,
  Play,
  Sparkles,
  TrendingUp,
  ChevronDown,
  ChevronRight,
  Download,
  RefreshCw,
  Target,
  Wrench,
} from 'lucide-react';
import { api } from '../../api/client';
import { RequirementForm } from './RequirementForm';
import { AssessmentView } from './AssessmentView';
import { ClientDashboard } from './ClientDashboard';
import toast from 'react-hot-toast';

interface ClientDetailProps {
  clientId: string;
  onBack: () => void;
}

interface ClientStats {
  client_id: string;
  client_name: string;
  total_requirements: number;
  compliant: number;
  partially_compliant: number;
  non_compliant: number;
  not_assessed: number;
  compliance_score: number;
  open_actions: number;
  overdue_actions: number;
}

interface Requirement {
  id: string;
  code: string;
  title: string;
  description: string | null;
  category: string;
  priority: string;
  is_active: boolean;
  is_mandatory: boolean;
  framework_mappings: any[];
}

interface Assessment {
  id: string;
  name: string;
  description: string | null;
  assessment_date: string;
  total_requirements: number;
  compliant_count: number;
  non_compliant_count: number;
  compliance_score: number | null;
  status: string;
  is_final: boolean;
}

export function ClientDetail({ clientId, onBack }: ClientDetailProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'requirements' | 'assessments' | 'actions'>('overview');
  const [showRequirementForm, setShowRequirementForm] = useState(false);
  const [selectedAssessment, setSelectedAssessment] = useState<string | null>(null);
  const queryClient = useQueryClient();

  // Fetch client stats
  const { data: stats, isLoading: statsLoading } = useQuery<ClientStats>({
    queryKey: ['client-stats', clientId],
    queryFn: async () => {
      const response = await api.get(`/clients/${clientId}/stats`);
      return response.data;
    },
  });

  // Fetch requirements
  const { data: requirementsData, isLoading: reqLoading } = useQuery({
    queryKey: ['client-requirements', clientId],
    queryFn: async () => {
      const response = await api.get(`/clients/${clientId}/requirements`);
      return response.data;
    },
  });

  // Fetch assessments
  const { data: assessments, isLoading: assessLoading } = useQuery<Assessment[]>({
    queryKey: ['client-assessments', clientId],
    queryFn: async () => {
      const response = await api.get(`/clients/${clientId}/assessments`);
      return response.data;
    },
  });

  // Create assessment mutation
  const createAssessmentMutation = useMutation({
    mutationFn: async () => {
      const response = await api.post(`/clients/${clientId}/assessments`, {
        name: `Evaluation ${new Date().toLocaleDateString('fr-FR')}`,
        description: 'Evaluation de conformite',
      });
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['client-assessments', clientId] });
      toast.success('Evaluation creee');
      setSelectedAssessment(data.id);
    },
    onError: () => {
      toast.error('Erreur lors de la creation');
    },
  });

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical':
        return 'bg-red-100 text-red-700';
      case 'high':
        return 'bg-orange-100 text-orange-700';
      case 'medium':
        return 'bg-yellow-100 text-yellow-700';
      case 'low':
        return 'bg-green-100 text-green-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  const getCategoryLabel = (category: string) => {
    const labels: Record<string, string> = {
      security: 'Securite',
      privacy: 'Confidentialite',
      availability: 'Disponibilite',
      integrity: 'Integrite',
      audit: 'Audit',
      reporting: 'Reporting',
      sla: 'SLA',
      contractual: 'Contractuel',
      regulatory: 'Reglementaire',
      technical: 'Technique',
      organizational: 'Organisationnel',
    };
    return labels[category] || category;
  };

  if (selectedAssessment) {
    return (
      <AssessmentView
        clientId={clientId}
        assessmentId={selectedAssessment}
        onBack={() => {
          setSelectedAssessment(null);
          queryClient.invalidateQueries({ queryKey: ['client-stats', clientId] });
        }}
      />
    );
  }

  if (showRequirementForm) {
    return (
      <RequirementForm
        clientId={clientId}
        onClose={() => setShowRequirementForm(false)}
        onSuccess={() => {
          setShowRequirementForm(false);
          queryClient.invalidateQueries({ queryKey: ['client-requirements', clientId] });
          queryClient.invalidateQueries({ queryKey: ['client-stats', clientId] });
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
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{stats?.client_name || 'Client'}</h1>
            <p className="text-gray-600">Gestion des exigences et conformite</p>
          </div>
        </div>

        <div className="flex gap-3">
          <button
            onClick={() => setShowRequirementForm(true)}
            className="flex items-center gap-2 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <Plus className="w-4 h-4" />
            Nouvelle Exigence
          </button>
          <button
            onClick={() => createAssessmentMutation.mutate()}
            disabled={createAssessmentMutation.isPending || !requirementsData?.items?.length}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
          >
            <Play className="w-4 h-4" />
            Nouvelle Evaluation
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      {statsLoading ? (
        <div className="h-24 flex items-center justify-center">
          <RefreshCw className="w-6 h-6 animate-spin text-blue-500" />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div className="bg-white rounded-lg shadow-sm border p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <FileText className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Exigences</p>
                <p className="text-xl font-semibold">{stats?.total_requirements || 0}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm border p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <CheckCircle className="w-5 h-5 text-green-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Conformes</p>
                <p className="text-xl font-semibold text-green-600">{stats?.compliant || 0}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm border p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-red-100 rounded-lg">
                <AlertTriangle className="w-5 h-5 text-red-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Non-conformes</p>
                <p className="text-xl font-semibold text-red-600">{stats?.non_compliant || 0}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm border p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-100 rounded-lg">
                <TrendingUp className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Score</p>
                <p className="text-xl font-semibold">{stats?.compliance_score?.toFixed(1) || 0}%</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm border p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-orange-100 rounded-lg">
                <Wrench className="w-5 h-5 text-orange-600" />
              </div>
              <div>
                <p className="text-sm text-gray-600">Actions</p>
                <p className="text-xl font-semibold">
                  {stats?.open_actions || 0}
                  {stats?.overdue_actions ? (
                    <span className="text-sm text-red-500 ml-1">({stats.overdue_actions} en retard)</span>
                  ) : null}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Compliance Score Bar */}
      {stats && stats.total_requirements > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h3 className="text-sm font-medium text-gray-700 mb-3">Repartition de la conformite</h3>
          <div className="h-4 bg-gray-200 rounded-full overflow-hidden flex">
            <div
              className="bg-green-500 transition-all duration-500"
              style={{ width: `${(stats.compliant / stats.total_requirements) * 100}%` }}
              title={`Conformes: ${stats.compliant}`}
            />
            <div
              className="bg-yellow-500 transition-all duration-500"
              style={{ width: `${(stats.partially_compliant / stats.total_requirements) * 100}%` }}
              title={`Partiellement conformes: ${stats.partially_compliant}`}
            />
            <div
              className="bg-red-500 transition-all duration-500"
              style={{ width: `${(stats.non_compliant / stats.total_requirements) * 100}%` }}
              title={`Non-conformes: ${stats.non_compliant}`}
            />
            <div
              className="bg-gray-400 transition-all duration-500"
              style={{ width: `${(stats.not_assessed / stats.total_requirements) * 100}%` }}
              title={`Non evalues: ${stats.not_assessed}`}
            />
          </div>
          <div className="flex gap-6 mt-3 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-green-500 rounded" />
              <span>Conforme ({stats.compliant})</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-yellow-500 rounded" />
              <span>Partiel ({stats.partially_compliant})</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-red-500 rounded" />
              <span>Non-conforme ({stats.non_compliant})</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-gray-400 rounded" />
              <span>Non evalue ({stats.not_assessed})</span>
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b">
        <nav className="flex gap-6">
          {[
            { id: 'overview', label: 'Vue d\'ensemble', icon: Building2 },
            { id: 'requirements', label: 'Exigences', icon: FileText },
            { id: 'assessments', label: 'Evaluations', icon: ClipboardCheck },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-4 py-3 border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-gray-600 hover:text-gray-900'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'requirements' && (
        <div className="bg-white rounded-lg shadow-sm border">
          {reqLoading ? (
            <div className="p-8 text-center">
              <RefreshCw className="w-6 h-6 animate-spin mx-auto text-blue-500" />
            </div>
          ) : requirementsData?.items?.length > 0 ? (
            <div className="divide-y">
              {requirementsData.items.map((req: Requirement) => (
                <div key={req.id} className="p-4 hover:bg-gray-50 transition-colors">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3">
                        <span className="text-sm font-mono text-gray-500">{req.code}</span>
                        <span className={`px-2 py-0.5 text-xs font-medium rounded ${getPriorityColor(req.priority)}`}>
                          {req.priority}
                        </span>
                        <span className="px-2 py-0.5 text-xs font-medium rounded bg-blue-100 text-blue-700">
                          {getCategoryLabel(req.category)}
                        </span>
                        {req.is_mandatory && (
                          <span className="px-2 py-0.5 text-xs font-medium rounded bg-purple-100 text-purple-700">
                            Obligatoire
                          </span>
                        )}
                      </div>
                      <h3 className="mt-1 font-medium text-gray-900">{req.title}</h3>
                      {req.description && (
                        <p className="mt-1 text-sm text-gray-600 line-clamp-2">{req.description}</p>
                      )}
                      {req.framework_mappings?.length > 0 && (
                        <div className="mt-2 flex gap-2">
                          {req.framework_mappings.slice(0, 3).map((mapping: any, idx: number) => (
                            <span key={idx} className="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded">
                              {mapping.framework}: {mapping.control}
                            </span>
                          ))}
                          {req.framework_mappings.length > 3 && (
                            <span className="text-xs text-gray-500">+{req.framework_mappings.length - 3}</span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-12 text-center">
              <FileText className="w-12 h-12 mx-auto text-gray-300" />
              <h3 className="mt-4 text-lg font-medium text-gray-900">Aucune exigence</h3>
              <p className="mt-2 text-gray-500">Ajoutez des exigences pour ce client</p>
              <button
                onClick={() => setShowRequirementForm(true)}
                className="mt-4 inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                <Plus className="w-4 h-4" />
                Ajouter une exigence
              </button>
            </div>
          )}
        </div>
      )}

      {activeTab === 'assessments' && (
        <div className="bg-white rounded-lg shadow-sm border">
          {assessLoading ? (
            <div className="p-8 text-center">
              <RefreshCw className="w-6 h-6 animate-spin mx-auto text-blue-500" />
            </div>
          ) : assessments && assessments.length > 0 ? (
            <div className="divide-y">
              {assessments.map((assessment) => (
                <div
                  key={assessment.id}
                  className="p-4 hover:bg-gray-50 transition-colors cursor-pointer"
                  onClick={() => setSelectedAssessment(assessment.id)}
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="flex items-center gap-3">
                        <h3 className="font-medium text-gray-900">{assessment.name}</h3>
                        {assessment.is_final ? (
                          <span className="px-2 py-0.5 text-xs font-medium rounded bg-green-100 text-green-700">
                            Finalise
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 text-xs font-medium rounded bg-yellow-100 text-yellow-700">
                            En cours
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-500 mt-1">
                        {new Date(assessment.assessment_date).toLocaleDateString('fr-FR')} - {assessment.total_requirements} exigences
                      </p>
                    </div>
                    <div className="flex items-center gap-6">
                      {assessment.compliance_score !== null && (
                        <div className="text-center">
                          <p className="text-2xl font-bold text-blue-600">
                            {assessment.compliance_score.toFixed(1)}%
                          </p>
                          <p className="text-xs text-gray-500">Score</p>
                        </div>
                      )}
                      <div className="flex items-center gap-4 text-sm">
                        <div className="text-center">
                          <p className="font-semibold text-green-600">{assessment.compliant_count}</p>
                          <p className="text-xs text-gray-500">Conformes</p>
                        </div>
                        <div className="text-center">
                          <p className="font-semibold text-red-600">{assessment.non_compliant_count}</p>
                          <p className="text-xs text-gray-500">Non-conformes</p>
                        </div>
                      </div>
                      <ChevronRight className="w-5 h-5 text-gray-400" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-12 text-center">
              <ClipboardCheck className="w-12 h-12 mx-auto text-gray-300" />
              <h3 className="mt-4 text-lg font-medium text-gray-900">Aucune evaluation</h3>
              <p className="mt-2 text-gray-500">
                Lancez une evaluation pour verifier la conformite aux exigences
              </p>
              <button
                onClick={() => createAssessmentMutation.mutate()}
                disabled={createAssessmentMutation.isPending || !requirementsData?.items?.length}
                className="mt-4 inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                <Play className="w-4 h-4" />
                Lancer une evaluation
              </button>
            </div>
          )}
        </div>
      )}

      {activeTab === 'overview' && (
        <ClientDashboard clientId={clientId} />
      )}
    </div>
  );
}
