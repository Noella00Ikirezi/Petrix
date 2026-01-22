import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  ArrowLeft,
  CheckCircle,
  XCircle,
  AlertCircle,
  MinusCircle,
  HelpCircle,
  Sparkles,
  Wrench,
  Save,
  RefreshCw,
  Lock,
  ChevronDown,
  ChevronRight,
  Download,
  Play,
  FileCheck,
} from 'lucide-react';
import { api } from '../../api/client';
import { EvidenceManager } from './EvidenceManager';
import toast from 'react-hot-toast';

interface AssessmentViewProps {
  clientId: string;
  assessmentId: string;
  onBack: () => void;
}

interface ComplianceRecord {
  id: string;
  status: string;
  compliance_level: number | null;
  gap_description: string | null;
  findings: string | null;
  recommendations: string | null;
  ai_assessment: string | null;
  ai_recommendations: string | null;
  requirement: {
    id: string;
    code: string;
    title: string;
    description: string | null;
    category: string;
    priority: string;
    acceptance_criteria: string | null;
    evidence_required: string[];
  };
  remediation_actions_count: number;
  evidence_count?: number;
}

interface Assessment {
  id: string;
  name: string;
  description: string | null;
  assessment_date: string;
  total_requirements: number;
  compliant_count: number;
  partially_compliant_count: number;
  non_compliant_count: number;
  not_applicable_count: number;
  not_assessed_count: number;
  compliance_score: number | null;
  status: string;
  is_final: boolean;
}

interface RemediationAction {
  id: string;
  title: string;
  description: string | null;
  action_type: string;
  priority: string;
  status: string;
  estimated_effort: string | null;
  due_date: string | null;
  implementation_steps: any[];
  ai_generated: boolean;
}

export function AssessmentView({ clientId, assessmentId, onBack }: AssessmentViewProps) {
  const [expandedRecord, setExpandedRecord] = useState<string | null>(null);
  const [selectedRecord, setSelectedRecord] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string | null>(null);
  const [evidenceModalRecord, setEvidenceModalRecord] = useState<string | null>(null);
  const queryClient = useQueryClient();

  // Fetch assessment
  const { data: assessment, isLoading: assessLoading } = useQuery<Assessment>({
    queryKey: ['assessment', assessmentId],
    queryFn: async () => {
      const response = await api.get(`/clients/${clientId}/assessments/${assessmentId}`);
      return response.data;
    },
  });

  // Fetch compliance records
  const { data: records, isLoading: recordsLoading } = useQuery<ComplianceRecord[]>({
    queryKey: ['assessment-records', assessmentId, statusFilter],
    queryFn: async () => {
      let url = `/clients/${clientId}/assessments/${assessmentId}/records`;
      if (statusFilter) url += `?status_filter=${statusFilter}`;
      const response = await api.get(url);
      return response.data;
    },
  });

  // Update compliance status mutation
  const updateStatusMutation = useMutation({
    mutationFn: async ({ recordId, data }: { recordId: string; data: any }) => {
      await api.patch(
        `/clients/${clientId}/assessments/${assessmentId}/records/${recordId}`,
        data
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assessment-records', assessmentId] });
      queryClient.invalidateQueries({ queryKey: ['assessment', assessmentId] });
      toast.success('Statut mis a jour');
    },
    onError: () => {
      toast.error('Erreur lors de la mise a jour');
    },
  });

  // Finalize assessment mutation
  const finalizeMutation = useMutation({
    mutationFn: async () => {
      await api.post(`/clients/${clientId}/assessments/${assessmentId}/finalize`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assessment', assessmentId] });
      toast.success('Evaluation finalisee');
    },
    onError: () => {
      toast.error('Erreur lors de la finalisation');
    },
  });

  // Generate remediation plan mutation
  const generateRemediationMutation = useMutation({
    mutationFn: async (recordId: string) => {
      const response = await api.post(
        `/clients/${clientId}/assessments/${assessmentId}/records/${recordId}/actions/generate`
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['assessment-records', assessmentId] });
      toast.success('Plan de remediation genere');
    },
    onError: () => {
      toast.error('Erreur lors de la generation');
    },
  });

  // AI assess mutation
  const aiAssessMutation = useMutation({
    mutationFn: async (recordId: string) => {
      const response = await api.post(
        `/clients/${clientId}/assessments/${assessmentId}/records/${recordId}/ai-assess`,
        { evidence: {} }
      );
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['assessment-records', assessmentId] });
      if (data.success) {
        toast.success('Evaluation IA terminee');
      } else {
        toast.error(data.error || 'Evaluation IA impossible');
      }
    },
    onError: () => {
      toast.error('Erreur lors de l\'evaluation IA');
    },
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'compliant':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'partially_compliant':
        return <AlertCircle className="w-5 h-5 text-yellow-500" />;
      case 'non_compliant':
        return <XCircle className="w-5 h-5 text-red-500" />;
      case 'not_applicable':
        return <MinusCircle className="w-5 h-5 text-gray-400" />;
      default:
        return <HelpCircle className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusLabel = (status: string) => {
    const labels: Record<string, string> = {
      compliant: 'Conforme',
      partially_compliant: 'Partiellement conforme',
      non_compliant: 'Non conforme',
      not_applicable: 'Non applicable',
      not_assessed: 'Non evalue',
    };
    return labels[status] || status;
  };

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

  const handleStatusChange = (recordId: string, newStatus: string) => {
    updateStatusMutation.mutate({
      recordId,
      data: { status: newStatus },
    });
  };

  const isLoading = assessLoading || recordsLoading;

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
            <h1 className="text-2xl font-bold text-gray-900">
              {assessment?.name || 'Evaluation'}
            </h1>
            <p className="text-gray-600">
              {assessment?.assessment_date
                ? new Date(assessment.assessment_date).toLocaleDateString('fr-FR')
                : ''}
              {assessment?.is_final && (
                <span className="ml-2 inline-flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded bg-green-100 text-green-700">
                  <Lock className="w-3 h-3" />
                  Finalisee
                </span>
              )}
            </p>
          </div>
        </div>

        {assessment && !assessment.is_final && (
          <div className="flex gap-3">
            <button
              onClick={() => finalizeMutation.mutate()}
              disabled={finalizeMutation.isPending}
              className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50"
            >
              <Lock className="w-4 h-4" />
              Finaliser l'evaluation
            </button>
          </div>
        )}
      </div>

      {/* Stats */}
      {assessment && (
        <div className="grid grid-cols-2 md:grid-cols-6 gap-4">
          <div className="bg-white rounded-lg shadow-sm border p-4 text-center">
            <p className="text-2xl font-bold text-gray-900">{assessment.total_requirements}</p>
            <p className="text-xs text-gray-500">Total</p>
          </div>
          <div className="bg-white rounded-lg shadow-sm border p-4 text-center">
            <p className="text-2xl font-bold text-green-600">{assessment.compliant_count}</p>
            <p className="text-xs text-gray-500">Conformes</p>
          </div>
          <div className="bg-white rounded-lg shadow-sm border p-4 text-center">
            <p className="text-2xl font-bold text-yellow-600">{assessment.partially_compliant_count}</p>
            <p className="text-xs text-gray-500">Partiels</p>
          </div>
          <div className="bg-white rounded-lg shadow-sm border p-4 text-center">
            <p className="text-2xl font-bold text-red-600">{assessment.non_compliant_count}</p>
            <p className="text-xs text-gray-500">Non-conformes</p>
          </div>
          <div className="bg-white rounded-lg shadow-sm border p-4 text-center">
            <p className="text-2xl font-bold text-gray-400">{assessment.not_assessed_count}</p>
            <p className="text-xs text-gray-500">Non evalues</p>
          </div>
          <div className="bg-white rounded-lg shadow-sm border p-4 text-center">
            <p className="text-2xl font-bold text-blue-600">
              {assessment.compliance_score?.toFixed(1) || 0}%
            </p>
            <p className="text-xs text-gray-500">Score</p>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-2 flex-wrap">
        {[
          { value: null, label: 'Tous', count: assessment?.total_requirements },
          { value: 'not_assessed', label: 'Non evalues', count: assessment?.not_assessed_count },
          { value: 'compliant', label: 'Conformes', count: assessment?.compliant_count },
          { value: 'partially_compliant', label: 'Partiels', count: assessment?.partially_compliant_count },
          { value: 'non_compliant', label: 'Non-conformes', count: assessment?.non_compliant_count },
          { value: 'not_applicable', label: 'N/A', count: assessment?.not_applicable_count },
        ].map(filter => (
          <button
            key={filter.value || 'all'}
            onClick={() => setStatusFilter(filter.value)}
            className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
              statusFilter === filter.value
                ? 'bg-blue-100 text-blue-700'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {filter.label} ({filter.count || 0})
          </button>
        ))}
      </div>

      {/* Records List */}
      <div className="bg-white rounded-lg shadow-sm border">
        {isLoading ? (
          <div className="p-8 text-center">
            <RefreshCw className="w-8 h-8 animate-spin mx-auto text-blue-500" />
          </div>
        ) : records && records.length > 0 ? (
          <div className="divide-y">
            {records.map((record) => (
              <div key={record.id} className="hover:bg-gray-50 transition-colors">
                <div
                  className="p-4 cursor-pointer"
                  onClick={() => setExpandedRecord(expandedRecord === record.id ? null : record.id)}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-4">
                      {getStatusIcon(record.status)}
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-mono text-gray-500">
                            {record.requirement.code}
                          </span>
                          <span className={`px-2 py-0.5 text-xs font-medium rounded ${getPriorityColor(record.requirement.priority)}`}>
                            {record.requirement.priority}
                          </span>
                        </div>
                        <h3 className="font-medium text-gray-900 mt-1">
                          {record.requirement.title}
                        </h3>
                        {record.gap_description && (
                          <p className="text-sm text-red-600 mt-1">
                            Ecart: {record.gap_description}
                          </p>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-3">
                      {record.evidence_count !== undefined && record.evidence_count > 0 && (
                        <span className="flex items-center gap-1 text-xs text-green-600 bg-green-50 px-2 py-1 rounded">
                          <FileCheck className="w-3 h-3" />
                          {record.evidence_count} preuve{record.evidence_count > 1 ? 's' : ''}
                        </span>
                      )}

                      {record.remediation_actions_count > 0 && (
                        <span className="flex items-center gap-1 text-xs text-orange-600 bg-orange-50 px-2 py-1 rounded">
                          <Wrench className="w-3 h-3" />
                          {record.remediation_actions_count} actions
                        </span>
                      )}

                      {!assessment?.is_final && (
                        <select
                          value={record.status}
                          onChange={(e) => {
                            e.stopPropagation();
                            handleStatusChange(record.id, e.target.value);
                          }}
                          onClick={(e) => e.stopPropagation()}
                          className="text-sm border rounded-lg px-3 py-1.5 focus:ring-2 focus:ring-blue-500"
                        >
                          <option value="not_assessed">Non evalue</option>
                          <option value="compliant">Conforme</option>
                          <option value="partially_compliant">Partiellement conforme</option>
                          <option value="non_compliant">Non conforme</option>
                          <option value="not_applicable">Non applicable</option>
                        </select>
                      )}

                      {expandedRecord === record.id ? (
                        <ChevronDown className="w-5 h-5 text-gray-400" />
                      ) : (
                        <ChevronRight className="w-5 h-5 text-gray-400" />
                      )}
                    </div>
                  </div>
                </div>

                {/* Expanded Details */}
                {expandedRecord === record.id && (
                  <div className="px-4 pb-4 pt-0">
                    <div className="ml-9 space-y-4 border-t pt-4">
                      {record.requirement.description && (
                        <div>
                          <h4 className="text-sm font-medium text-gray-700">Description</h4>
                          <p className="text-sm text-gray-600 mt-1">{record.requirement.description}</p>
                        </div>
                      )}

                      {record.requirement.acceptance_criteria && (
                        <div>
                          <h4 className="text-sm font-medium text-gray-700">Criteres d'acceptation</h4>
                          <p className="text-sm text-gray-600 mt-1">{record.requirement.acceptance_criteria}</p>
                        </div>
                      )}

                      {record.requirement.evidence_required?.length > 0 && (
                        <div>
                          <h4 className="text-sm font-medium text-gray-700">Preuves requises</h4>
                          <ul className="list-disc list-inside text-sm text-gray-600 mt-1">
                            {record.requirement.evidence_required.map((evidence, idx) => (
                              <li key={idx}>{evidence}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* AI Assessment */}
                      {record.ai_assessment && (
                        <div className="bg-purple-50 rounded-lg p-3">
                          <h4 className="text-sm font-medium text-purple-700 flex items-center gap-2">
                            <Sparkles className="w-4 h-4" />
                            Analyse IA
                          </h4>
                          <p className="text-sm text-purple-600 mt-1">{record.ai_assessment}</p>
                          {record.ai_recommendations && (
                            <p className="text-sm text-purple-600 mt-2">
                              <strong>Recommandations:</strong> {record.ai_recommendations}
                            </p>
                          )}
                        </div>
                      )}

                      {/* Gap & Findings */}
                      {!assessment?.is_final && (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              Description de l'ecart
                            </label>
                            <textarea
                              defaultValue={record.gap_description || ''}
                              onBlur={(e) => {
                                if (e.target.value !== record.gap_description) {
                                  updateStatusMutation.mutate({
                                    recordId: record.id,
                                    data: { gap_description: e.target.value },
                                  });
                                }
                              }}
                              rows={2}
                              className="w-full text-sm px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                              placeholder="Decrire l'ecart constate..."
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              Constats
                            </label>
                            <textarea
                              defaultValue={record.findings || ''}
                              onBlur={(e) => {
                                if (e.target.value !== record.findings) {
                                  updateStatusMutation.mutate({
                                    recordId: record.id,
                                    data: { findings: e.target.value },
                                  });
                                }
                              }}
                              rows={2}
                              className="w-full text-sm px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                              placeholder="Constats et observations..."
                            />
                          </div>
                        </div>
                      )}

                      {/* Actions */}
                      <div className="flex gap-2 pt-2 flex-wrap">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setEvidenceModalRecord(record.id);
                          }}
                          className="flex items-center gap-2 px-3 py-1.5 text-sm bg-green-100 text-green-700 rounded-lg hover:bg-green-200 transition-colors"
                        >
                          <FileCheck className="w-4 h-4" />
                          Gerer les preuves
                          {record.evidence_count !== undefined && record.evidence_count > 0 && (
                            <span className="bg-green-600 text-white text-xs px-1.5 py-0.5 rounded-full">
                              {record.evidence_count}
                            </span>
                          )}
                        </button>

                        {!assessment?.is_final && (
                          <>
                            <button
                              onClick={() => aiAssessMutation.mutate(record.id)}
                              disabled={aiAssessMutation.isPending}
                              className="flex items-center gap-2 px-3 py-1.5 text-sm bg-purple-100 text-purple-700 rounded-lg hover:bg-purple-200 transition-colors disabled:opacity-50"
                            >
                              <Sparkles className="w-4 h-4" />
                              Evaluation IA
                            </button>

                            {(record.status === 'non_compliant' || record.status === 'partially_compliant') && (
                              <button
                                onClick={() => generateRemediationMutation.mutate(record.id)}
                                disabled={generateRemediationMutation.isPending}
                                className="flex items-center gap-2 px-3 py-1.5 text-sm bg-orange-100 text-orange-700 rounded-lg hover:bg-orange-200 transition-colors disabled:opacity-50"
                              >
                                <Wrench className="w-4 h-4" />
                                Generer plan de remediation
                              </button>
                            )}
                          </>
                        )}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="p-12 text-center">
            <p className="text-gray-500">Aucun enregistrement de conformite</p>
          </div>
        )}
      </div>

      {/* Evidence Manager Modal */}
      {evidenceModalRecord && (
        <EvidenceManager
          clientId={clientId}
          assessmentId={assessmentId}
          recordId={evidenceModalRecord}
          onClose={() => setEvidenceModalRecord(null)}
          onUpdate={() => {
            queryClient.invalidateQueries({ queryKey: ['assessment-records', assessmentId] });
          }}
        />
      )}
    </div>
  );
}
