import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  FileText,
  Plus,
  Upload,
  Link,
  Check,
  X,
  Clock,
  AlertTriangle,
  Trash2,
  Eye,
  Download,
  RefreshCw,
  Calendar,
  Tag,
  ExternalLink,
} from 'lucide-react';
import { api } from '../../api/client';
import toast from 'react-hot-toast';

interface EvidenceManagerProps {
  clientId: string;
  assessmentId: string;
  recordId: string;
  requirementCode?: string;
  onClose: () => void;
  onUpdate?: () => void;
}

interface Evidence {
  id: string;
  name: string;
  description: string | null;
  evidence_type: string;
  file_name: string | null;
  file_size: number | null;
  mime_type: string | null;
  external_url: string | null;
  valid_from: string | null;
  valid_until: string | null;
  is_expired: boolean;
  is_verified: boolean;
  verified_at: string | null;
  verification_notes: string | null;
  tags: string[];
  created_at: string;
}

const evidenceTypes = [
  { value: 'document', label: 'Document' },
  { value: 'screenshot', label: 'Capture ecran' },
  { value: 'log', label: 'Journal/Log' },
  { value: 'config', label: 'Configuration' },
  { value: 'report', label: 'Rapport' },
  { value: 'certificate', label: 'Certificat' },
  { value: 'policy', label: 'Politique' },
  { value: 'procedure', label: 'Procedure' },
  { value: 'attestation', label: 'Attestation' },
  { value: 'other', label: 'Autre' },
];

export function EvidenceManager({
  clientId,
  assessmentId,
  recordId,
  requirementCode,
  onClose,
  onUpdate,
}: EvidenceManagerProps) {
  const [showAddForm, setShowAddForm] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    evidence_type: 'document',
    external_url: '',
    valid_from: '',
    valid_until: '',
    tags: '',
  });
  const queryClient = useQueryClient();

  // Fetch evidence list
  const { data: evidenceList, isLoading } = useQuery<Evidence[]>({
    queryKey: ['evidence', recordId],
    queryFn: async () => {
      const response = await api.get(
        `/clients/${clientId}/assessments/${assessmentId}/records/${recordId}/evidence`
      );
      return response.data;
    },
  });

  // Create evidence mutation
  const createMutation = useMutation({
    mutationFn: async (data: any) => {
      await api.post(
        `/clients/${clientId}/assessments/${assessmentId}/records/${recordId}/evidence`,
        {
          ...data,
          compliance_record_id: recordId,
          tags: data.tags ? data.tags.split(',').map((t: string) => t.trim()).filter(Boolean) : [],
          valid_from: data.valid_from || null,
          valid_until: data.valid_until || null,
        }
      );
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['evidence', recordId] });
      onUpdate?.();
      setShowAddForm(false);
      setFormData({
        name: '',
        description: '',
        evidence_type: 'document',
        external_url: '',
        valid_from: '',
        valid_until: '',
        tags: '',
      });
      toast.success('Preuve ajoutee');
    },
    onError: () => {
      toast.error('Erreur lors de l\'ajout');
    },
  });

  // Verify evidence mutation
  const verifyMutation = useMutation({
    mutationFn: async ({ evidenceId, isVerified, notes }: { evidenceId: string; isVerified: boolean; notes?: string }) => {
      await api.post(`/clients/${clientId}/evidence/${evidenceId}/verify`, {
        is_verified: isVerified,
        verification_notes: notes,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['evidence', recordId] });
      onUpdate?.();
      toast.success('Statut mis a jour');
    },
    onError: () => {
      toast.error('Erreur lors de la verification');
    },
  });

  // Delete evidence mutation
  const deleteMutation = useMutation({
    mutationFn: async (evidenceId: string) => {
      await api.delete(`/clients/${clientId}/evidence/${evidenceId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['evidence', recordId] });
      onUpdate?.();
      toast.success('Preuve supprimee');
    },
    onError: () => {
      toast.error('Erreur lors de la suppression');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate(formData);
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'document':
      case 'policy':
      case 'procedure':
        return <FileText className="w-4 h-4" />;
      case 'certificate':
      case 'attestation':
        return <Check className="w-4 h-4" />;
      case 'screenshot':
        return <Eye className="w-4 h-4" />;
      default:
        return <FileText className="w-4 h-4" />;
    }
  };

  const formatFileSize = (bytes: number | null) => {
    if (!bytes) return '';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="p-6 border-b flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-gray-900">Gestion des preuves</h2>
            <p className="text-sm text-gray-600">Exigence: {requirementCode}</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Add Button */}
          {!showAddForm && (
            <button
              onClick={() => setShowAddForm(true)}
              className="w-full mb-4 p-4 border-2 border-dashed border-gray-300 rounded-lg hover:border-blue-400 hover:bg-blue-50 transition-colors flex items-center justify-center gap-2 text-gray-600 hover:text-blue-600"
            >
              <Plus className="w-5 h-5" />
              Ajouter une preuve
            </button>
          )}

          {/* Add Form */}
          {showAddForm && (
            <form onSubmit={handleSubmit} className="mb-6 p-4 bg-gray-50 rounded-lg">
              <h3 className="font-semibold mb-4">Nouvelle preuve</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Nom *
                  </label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                    required
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="Ex: Politique de securite v2.1"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Type
                  </label>
                  <select
                    value={formData.evidence_type}
                    onChange={(e) => setFormData(prev => ({ ...prev, evidence_type: e.target.value }))}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    {evidenceTypes.map(type => (
                      <option key={type.value} value={type.value}>{type.label}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Lien externe
                  </label>
                  <input
                    type="url"
                    value={formData.external_url}
                    onChange={(e) => setFormData(prev => ({ ...prev, external_url: e.target.value }))}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="https://..."
                  />
                </div>

                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description
                  </label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                    rows={2}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="Description de la preuve..."
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Valide a partir du
                  </label>
                  <input
                    type="date"
                    value={formData.valid_from}
                    onChange={(e) => setFormData(prev => ({ ...prev, valid_from: e.target.value }))}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Valide jusqu'au
                  </label>
                  <input
                    type="date"
                    value={formData.valid_until}
                    onChange={(e) => setFormData(prev => ({ ...prev, valid_until: e.target.value }))}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Tags (separes par des virgules)
                  </label>
                  <input
                    type="text"
                    value={formData.tags}
                    onChange={(e) => setFormData(prev => ({ ...prev, tags: e.target.value }))}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                    placeholder="audit, 2024, iso27001"
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2 mt-4">
                <button
                  type="button"
                  onClick={() => setShowAddForm(false)}
                  className="px-4 py-2 text-gray-600 hover:bg-gray-200 rounded-lg transition-colors"
                >
                  Annuler
                </button>
                <button
                  type="submit"
                  disabled={createMutation.isPending}
                  className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
                >
                  {createMutation.isPending ? 'Ajout...' : 'Ajouter'}
                </button>
              </div>
            </form>
          )}

          {/* Evidence List */}
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <RefreshCw className="w-6 h-6 animate-spin text-blue-500" />
            </div>
          ) : evidenceList && evidenceList.length > 0 ? (
            <div className="space-y-3">
              {evidenceList.map((evidence) => (
                <div
                  key={evidence.id}
                  className={`p-4 rounded-lg border ${
                    evidence.is_expired ? 'bg-red-50 border-red-200' :
                    evidence.is_verified ? 'bg-green-50 border-green-200' :
                    'bg-white border-gray-200'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3">
                      <div className={`p-2 rounded-lg ${
                        evidence.is_expired ? 'bg-red-100' :
                        evidence.is_verified ? 'bg-green-100' : 'bg-gray-100'
                      }`}>
                        {getTypeIcon(evidence.evidence_type)}
                      </div>
                      <div>
                        <h4 className="font-medium text-gray-900">{evidence.name}</h4>
                        <div className="flex items-center gap-2 mt-1 text-xs text-gray-500">
                          <span className="px-2 py-0.5 bg-gray-100 rounded">
                            {evidenceTypes.find(t => t.value === evidence.evidence_type)?.label}
                          </span>
                          {evidence.file_name && (
                            <span>{evidence.file_name} ({formatFileSize(evidence.file_size)})</span>
                          )}
                        </div>
                        {evidence.description && (
                          <p className="text-sm text-gray-600 mt-1">{evidence.description}</p>
                        )}
                        {evidence.tags.length > 0 && (
                          <div className="flex items-center gap-1 mt-2">
                            <Tag className="w-3 h-3 text-gray-400" />
                            {evidence.tags.map((tag, idx) => (
                              <span key={idx} className="px-1.5 py-0.5 bg-gray-100 rounded text-xs">
                                {tag}
                              </span>
                            ))}
                          </div>
                        )}
                        {(evidence.valid_from || evidence.valid_until) && (
                          <div className="flex items-center gap-2 mt-2 text-xs text-gray-500">
                            <Calendar className="w-3 h-3" />
                            {evidence.valid_from && (
                              <span>Du {new Date(evidence.valid_from).toLocaleDateString('fr-FR')}</span>
                            )}
                            {evidence.valid_until && (
                              <span>au {new Date(evidence.valid_until).toLocaleDateString('fr-FR')}</span>
                            )}
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center gap-2">
                      {/* Status badges */}
                      {evidence.is_expired && (
                        <span className="px-2 py-1 bg-red-100 text-red-700 text-xs font-medium rounded flex items-center gap-1">
                          <AlertTriangle className="w-3 h-3" />
                          Expiree
                        </span>
                      )}
                      {evidence.is_verified && (
                        <span className="px-2 py-1 bg-green-100 text-green-700 text-xs font-medium rounded flex items-center gap-1">
                          <Check className="w-3 h-3" />
                          Verifiee
                        </span>
                      )}
                      {!evidence.is_verified && !evidence.is_expired && (
                        <span className="px-2 py-1 bg-yellow-100 text-yellow-700 text-xs font-medium rounded flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          En attente
                        </span>
                      )}

                      {/* Actions */}
                      <div className="flex items-center gap-1 ml-2">
                        {evidence.external_url && (
                          <a
                            href={evidence.external_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
                            title="Ouvrir le lien"
                          >
                            <ExternalLink className="w-4 h-4" />
                          </a>
                        )}
                        {!evidence.is_verified && (
                          <button
                            onClick={() => verifyMutation.mutate({ evidenceId: evidence.id, isVerified: true })}
                            className="p-1.5 text-gray-400 hover:text-green-600 hover:bg-green-50 rounded transition-colors"
                            title="Verifier"
                          >
                            <Check className="w-4 h-4" />
                          </button>
                        )}
                        {evidence.is_verified && (
                          <button
                            onClick={() => verifyMutation.mutate({ evidenceId: evidence.id, isVerified: false })}
                            className="p-1.5 text-gray-400 hover:text-orange-600 hover:bg-orange-50 rounded transition-colors"
                            title="Retirer verification"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        )}
                        <button
                          onClick={() => {
                            if (confirm('Supprimer cette preuve ?')) {
                              deleteMutation.mutate(evidence.id);
                            }
                          }}
                          className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                          title="Supprimer"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                  </div>

                  {evidence.verification_notes && (
                    <div className="mt-3 pt-3 border-t text-sm text-gray-600">
                      <span className="font-medium">Notes de verification:</span> {evidence.verification_notes}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-12">
              <FileText className="w-12 h-12 mx-auto text-gray-300" />
              <h3 className="mt-4 text-lg font-medium text-gray-900">Aucune preuve</h3>
              <p className="mt-2 text-gray-500">
                Ajoutez des preuves pour documenter la conformite
              </p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t bg-gray-50 flex justify-between items-center">
          <p className="text-sm text-gray-500">
            {evidenceList?.length || 0} preuve(s) - {evidenceList?.filter(e => e.is_verified).length || 0} verifiee(s)
          </p>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
          >
            Fermer
          </button>
        </div>
      </div>
    </div>
  );
}
