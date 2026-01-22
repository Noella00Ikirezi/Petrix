import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import {
  ArrowLeft,
  FileText,
  Plus,
  Trash2,
  Save,
  X,
} from 'lucide-react';
import { api } from '../../api/client';
import toast from 'react-hot-toast';

interface RequirementFormProps {
  clientId: string;
  requirement?: any;
  onClose: () => void;
  onSuccess: () => void;
}

export function RequirementForm({ clientId, requirement, onClose, onSuccess }: RequirementFormProps) {
  const [formData, setFormData] = useState({
    code: requirement?.code || '',
    title: requirement?.title || '',
    description: requirement?.description || '',
    category: requirement?.category || 'security',
    priority: requirement?.priority || 'medium',
    source: requirement?.source || '',
    source_reference: requirement?.source_reference || '',
    acceptance_criteria: requirement?.acceptance_criteria || '',
    evidence_required: requirement?.evidence_required?.join('\n') || '',
    sla_target: requirement?.sla_target || '',
    review_frequency: requirement?.review_frequency || '',
    is_mandatory: requirement?.is_mandatory ?? true,
    framework_mappings: requirement?.framework_mappings || [],
  });

  const [newMapping, setNewMapping] = useState({ framework: '', control: '', description: '' });

  const createMutation = useMutation({
    mutationFn: async (data: any) => {
      const payload = {
        ...data,
        evidence_required: data.evidence_required
          ? data.evidence_required.split('\n').map((e: string) => e.trim()).filter(Boolean)
          : [],
      };

      if (requirement) {
        await api.patch(`/clients/${clientId}/requirements/${requirement.id}`, payload);
      } else {
        await api.post(`/clients/${clientId}/requirements`, payload);
      }
    },
    onSuccess: () => {
      toast.success(requirement ? 'Exigence mise a jour' : 'Exigence creee');
      onSuccess();
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Erreur lors de la sauvegarde');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate(formData);
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value, type } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : value,
    }));
  };

  const addFrameworkMapping = () => {
    if (newMapping.framework && newMapping.control) {
      setFormData(prev => ({
        ...prev,
        framework_mappings: [...prev.framework_mappings, { ...newMapping }],
      }));
      setNewMapping({ framework: '', control: '', description: '' });
    }
  };

  const removeFrameworkMapping = (index: number) => {
    setFormData(prev => ({
      ...prev,
      framework_mappings: prev.framework_mappings.filter((_: any, i: number) => i !== index),
    }));
  };

  const categories = [
    { value: 'security', label: 'Securite' },
    { value: 'privacy', label: 'Confidentialite' },
    { value: 'availability', label: 'Disponibilite' },
    { value: 'integrity', label: 'Integrite' },
    { value: 'audit', label: 'Audit' },
    { value: 'reporting', label: 'Reporting' },
    { value: 'sla', label: 'SLA' },
    { value: 'contractual', label: 'Contractuel' },
    { value: 'regulatory', label: 'Reglementaire' },
    { value: 'technical', label: 'Technique' },
    { value: 'organizational', label: 'Organisationnel' },
  ];

  const frameworks = [
    'ISO 27001',
    'ISO 27002',
    'DORA',
    'NIS2',
    'RGPD',
    'PCI DSS',
    'SOC2',
    'NIST CSF',
    'EU AI Act',
    'HDS',
    'SecNumCloud',
  ];

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={onClose}
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            {requirement ? 'Modifier l\'exigence' : 'Nouvelle exigence'}
          </h1>
          <p className="text-gray-600">
            Definissez une exigence client a verifier
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Basic Info */}
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <FileText className="w-5 h-5 text-blue-600" />
            Informations de base
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Code de l'exigence *
              </label>
              <input
                type="text"
                name="code"
                value={formData.code}
                onChange={handleChange}
                required
                className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="EX: SEC-001"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Priorite
              </label>
              <select
                name="priority"
                value={formData.priority}
                onChange={handleChange}
                className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="low">Basse</option>
                <option value="medium">Moyenne</option>
                <option value="high">Haute</option>
                <option value="critical">Critique</option>
              </select>
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Titre *
              </label>
              <input
                type="text"
                name="title"
                value={formData.title}
                onChange={handleChange}
                required
                className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Titre de l'exigence"
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description
              </label>
              <textarea
                name="description"
                value={formData.description}
                onChange={handleChange}
                rows={3}
                className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Description detaillee de l'exigence..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Categorie
              </label>
              <select
                name="category"
                value={formData.category}
                onChange={handleChange}
                className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                {categories.map(cat => (
                  <option key={cat.value} value={cat.value}>{cat.label}</option>
                ))}
              </select>
            </div>

            <div className="flex items-center">
              <label className="flex items-center gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  name="is_mandatory"
                  checked={formData.is_mandatory}
                  onChange={handleChange}
                  className="w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <span className="text-sm font-medium text-gray-700">Exigence obligatoire</span>
              </label>
            </div>
          </div>
        </div>

        {/* Source & Reference */}
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h2 className="text-lg font-semibold mb-4">Source et reference</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Source
              </label>
              <input
                type="text"
                name="source"
                value={formData.source}
                onChange={handleChange}
                className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Ex: Contrat de service, Annexe securite..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Reference
              </label>
              <input
                type="text"
                name="source_reference"
                value={formData.source_reference}
                onChange={handleChange}
                className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Ex: Article 5.2, Clause 12..."
              />
            </div>
          </div>
        </div>

        {/* Framework Mappings */}
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h2 className="text-lg font-semibold mb-4">Mappings referentiels</h2>

          {formData.framework_mappings.length > 0 && (
            <div className="mb-4 space-y-2">
              {formData.framework_mappings.map((mapping: any, index: number) => (
                <div key={index} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                  <span className="font-medium text-sm">{mapping.framework}</span>
                  <span className="text-gray-400">-</span>
                  <span className="text-sm">{mapping.control}</span>
                  {mapping.description && (
                    <span className="text-xs text-gray-500">({mapping.description})</span>
                  )}
                  <button
                    type="button"
                    onClick={() => removeFrameworkMapping(index)}
                    className="ml-auto p-1 text-red-500 hover:bg-red-50 rounded"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-4 gap-3">
            <select
              value={newMapping.framework}
              onChange={(e) => setNewMapping(prev => ({ ...prev, framework: e.target.value }))}
              className="px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="">Referentiel</option>
              {frameworks.map(fw => (
                <option key={fw} value={fw}>{fw}</option>
              ))}
            </select>
            <input
              type="text"
              value={newMapping.control}
              onChange={(e) => setNewMapping(prev => ({ ...prev, control: e.target.value }))}
              className="px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Controle (ex: A.5.1)"
            />
            <input
              type="text"
              value={newMapping.description}
              onChange={(e) => setNewMapping(prev => ({ ...prev, description: e.target.value }))}
              className="px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              placeholder="Description (optionnel)"
            />
            <button
              type="button"
              onClick={addFrameworkMapping}
              className="flex items-center justify-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
            >
              <Plus className="w-4 h-4" />
              Ajouter
            </button>
          </div>
        </div>

        {/* Acceptance Criteria */}
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h2 className="text-lg font-semibold mb-4">Criteres d'acceptation</h2>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Criteres d'acceptation
              </label>
              <textarea
                name="acceptance_criteria"
                value={formData.acceptance_criteria}
                onChange={handleChange}
                rows={3}
                className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Criteres permettant de valider la conformite..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Preuves requises (une par ligne)
              </label>
              <textarea
                name="evidence_required"
                value={formData.evidence_required}
                onChange={handleChange}
                rows={3}
                className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Politique de securite&#10;Rapport d'audit&#10;Capture d'ecran de configuration..."
              />
            </div>
          </div>
        </div>

        {/* SLA */}
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h2 className="text-lg font-semibold mb-4">SLA et frequence</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Objectif SLA
              </label>
              <input
                type="text"
                name="sla_target"
                value={formData.sla_target}
                onChange={handleChange}
                className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Ex: 99.9% disponibilite, 4h resolution..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Frequence de revue
              </label>
              <select
                name="review_frequency"
                value={formData.review_frequency}
                onChange={handleChange}
                className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="">Non definie</option>
                <option value="weekly">Hebdomadaire</option>
                <option value="monthly">Mensuelle</option>
                <option value="quarterly">Trimestrielle</option>
                <option value="biannual">Semestrielle</option>
                <option value="annual">Annuelle</option>
              </select>
            </div>
          </div>
        </div>

        {/* Actions */}
        <div className="flex justify-end gap-4">
          <button
            type="button"
            onClick={onClose}
            className="flex items-center gap-2 px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <X className="w-4 h-4" />
            Annuler
          </button>
          <button
            type="submit"
            disabled={createMutation.isPending}
            className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
          >
            <Save className="w-4 h-4" />
            {createMutation.isPending ? 'Enregistrement...' : 'Enregistrer'}
          </button>
        </div>
      </form>
    </div>
  );
}
