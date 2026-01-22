import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import {
  X,
  ChevronLeft,
  ChevronRight,
  Building,
  Shield,
  FileText,
  Check,
  Sparkles,
  AlertCircle,
} from 'lucide-react';
import { api } from '../../api/client';
import toast from 'react-hot-toast';

interface ProjectWizardProps {
  onClose: () => void;
  onComplete: () => void;
}

interface Framework {
  id: string;
  code: string;
  name: string;
  version: string;
  description: string;
  category: string;
  is_mandatory: boolean;
  icon: string;
  color: string;
}

const STEPS = [
  { id: 'organization', title: 'Organisation', icon: Building },
  { id: 'frameworks', title: 'Référentiels', icon: Shield },
  { id: 'security', title: 'Niveau de sécurité', icon: FileText },
  { id: 'review', title: 'Récapitulatif', icon: Check },
];

const SECURITY_LEVELS = [
  {
    value: 'n1_standard',
    label: 'N1 - Standard',
    description: 'Niveau de base pour les organisations avec des risques modérés',
    color: 'green',
  },
  {
    value: 'n2_reinforced',
    label: 'N2 - Renforcé',
    description: 'Pour les organisations manipulant des données sensibles',
    color: 'orange',
  },
  {
    value: 'n3_critical',
    label: 'N3 - Critique',
    description: 'Pour les infrastructures critiques et données hautement sensibles',
    color: 'red',
  },
];

const ORGANIZATION_SIZES = [
  { value: 'tpe', label: 'TPE (< 10 salariés)' },
  { value: 'pme', label: 'PME (10-250 salariés)' },
  { value: 'eti', label: 'ETI (250-5000 salariés)' },
  { value: 'ge', label: 'Grande Entreprise (> 5000 salariés)' },
];

const INDUSTRY_SECTORS = [
  { value: 'finance', label: 'Finance / Banque / Assurance' },
  { value: 'healthcare', label: 'Santé' },
  { value: 'retail', label: 'Commerce / Distribution' },
  { value: 'industry', label: 'Industrie / Manufacturing' },
  { value: 'tech', label: 'Technologie / IT' },
  { value: 'public', label: 'Secteur Public' },
  { value: 'energy', label: 'Énergie / Utilities' },
  { value: 'transport', label: 'Transport / Logistique' },
  { value: 'other', label: 'Autre' },
];

export function ProjectWizard({ onClose, onComplete }: ProjectWizardProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    organization_name: '',
    organization_type: '',
    organization_size: '',
    industry_sector: '',
    selected_frameworks: [] as string[],
    security_level: 'n1_standard',
  });

  // Fetch frameworks
  const { data: frameworks } = useQuery<Framework[]>({
    queryKey: ['smsi-frameworks'],
    queryFn: async () => {
      const response = await api.get('/smsi/frameworks');
      return response.data;
    },
  });

  // Create project mutation
  const createMutation = useMutation({
    mutationFn: async (data: typeof formData) => {
      const response = await api.post('/smsi/projects', data);
      return response.data;
    },
    onSuccess: () => {
      toast.success('Projet SMSI créé avec succès !');
      onComplete();
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Erreur lors de la création');
    },
  });

  const updateFormData = (field: string, value: any) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const toggleFramework = (code: string) => {
    setFormData((prev) => ({
      ...prev,
      selected_frameworks: prev.selected_frameworks.includes(code)
        ? prev.selected_frameworks.filter((f) => f !== code)
        : [...prev.selected_frameworks, code],
    }));
  };

  const canProceed = () => {
    switch (currentStep) {
      case 0:
        return formData.name && formData.organization_name;
      case 1:
        return formData.selected_frameworks.length > 0;
      case 2:
        return formData.security_level;
      case 3:
        return true;
      default:
        return false;
    }
  };

  const handleNext = () => {
    if (currentStep < STEPS.length - 1) {
      setCurrentStep((prev) => prev + 1);
    } else {
      createMutation.mutate(formData);
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep((prev) => prev - 1);
    }
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 0:
        return (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Nom du projet SMSI *
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => updateFormData('name', e.target.value)}
                placeholder="Ex: SMSI Groupe 2026"
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Description
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => updateFormData('description', e.target.value)}
                placeholder="Description optionnelle du projet..."
                rows={3}
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Nom de l'organisation *
              </label>
              <input
                type="text"
                value={formData.organization_name}
                onChange={(e) => updateFormData('organization_name', e.target.value)}
                placeholder="Ex: Groupe ABC"
                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 dark:placeholder-gray-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Taille de l'organisation
                </label>
                <select
                  value={formData.organization_size}
                  onChange={(e) => updateFormData('organization_size', e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  <option value="">Sélectionner...</option>
                  {ORGANIZATION_SIZES.map((size) => (
                    <option key={size.value} value={size.value}>
                      {size.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Secteur d'activité
                </label>
                <select
                  value={formData.industry_sector}
                  onChange={(e) => updateFormData('industry_sector', e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                >
                  <option value="">Sélectionner...</option>
                  {INDUSTRY_SECTORS.map((sector) => (
                    <option key={sector.value} value={sector.value}>
                      {sector.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        );

      case 1:
        return (
          <div className="space-y-4">
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Sélectionnez les référentiels de conformité applicables à votre organisation :
            </p>

            <div className="grid grid-cols-2 gap-4">
              {frameworks?.map((fw) => (
                <div
                  key={fw.code}
                  onClick={() => toggleFramework(fw.code)}
                  className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
                    formData.selected_frameworks.includes(fw.code)
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/30'
                      : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="font-medium text-gray-900 dark:text-white">{fw.name}</h4>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Version {fw.version}</p>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">{fw.description}</p>
                    </div>
                    <div
                      className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${
                        formData.selected_frameworks.includes(fw.code)
                          ? 'border-blue-500 bg-blue-500'
                          : 'border-gray-300 dark:border-gray-500'
                      }`}
                    >
                      {formData.selected_frameworks.includes(fw.code) && (
                        <Check className="w-3 h-3 text-white" />
                      )}
                    </div>
                  </div>
                  {fw.is_mandatory && (
                    <span className="mt-2 inline-block text-xs px-2 py-1 bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300 rounded">
                      Obligatoire
                    </span>
                  )}
                </div>
              )) || (
                // Default frameworks if API not available
                [
                  { code: 'iso_27001', name: 'ISO 27001:2022', description: 'Standard international de sécurité' },
                  { code: 'dora', name: 'DORA', description: 'Résilience opérationnelle numérique (Finance)' },
                  { code: 'nis2', name: 'NIS2', description: 'Directive européenne cybersécurité' },
                  { code: 'rgpd', name: 'RGPD', description: 'Protection des données personnelles' },
                  { code: 'pci_dss', name: 'PCI DSS v4.0', description: 'Sécurité des paiements par carte' },
                  { code: 'eu_ai_act', name: 'EU AI Act', description: 'Règlement européen sur l\'IA' },
                ].map((fw) => (
                  <div
                    key={fw.code}
                    onClick={() => toggleFramework(fw.code)}
                    className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
                      formData.selected_frameworks.includes(fw.code)
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/30'
                        : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <h4 className="font-medium text-gray-900 dark:text-white">{fw.name}</h4>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{fw.description}</p>
                      </div>
                      <div
                        className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${
                          formData.selected_frameworks.includes(fw.code)
                            ? 'border-blue-500 bg-blue-500'
                            : 'border-gray-300 dark:border-gray-500'
                        }`}
                      >
                        {formData.selected_frameworks.includes(fw.code) && (
                          <Check className="w-3 h-3 text-white" />
                        )}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>

            <p className="text-sm text-gray-500 dark:text-gray-400 mt-4">
              {formData.selected_frameworks.length} référentiel(s) sélectionné(s)
            </p>
          </div>
        );

      case 2:
        return (
          <div className="space-y-4">
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Choisissez le niveau de sécurité adapté à votre organisation :
            </p>

            {SECURITY_LEVELS.map((level) => (
              <div
                key={level.value}
                onClick={() => updateFormData('security_level', level.value)}
                className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
                  formData.security_level === level.value
                    ? `border-${level.color}-500 bg-${level.color}-50 dark:bg-${level.color}-900/30`
                    : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium text-gray-900 dark:text-white">{level.label}</h4>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">{level.description}</p>
                  </div>
                  <div
                    className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${
                      formData.security_level === level.value
                        ? `border-${level.color}-500 bg-${level.color}-500`
                        : 'border-gray-300 dark:border-gray-500'
                    }`}
                  >
                    {formData.security_level === level.value && (
                      <Check className="w-3 h-3 text-white" />
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        );

      case 3:
        return (
          <div className="space-y-6">
            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-6">
              <h3 className="font-medium text-gray-900 dark:text-white mb-4">Récapitulatif du projet</h3>

              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Nom du projet</span>
                  <span className="font-medium text-gray-900 dark:text-white">{formData.name}</span>
                </div>

                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Organisation</span>
                  <span className="font-medium text-gray-900 dark:text-white">{formData.organization_name}</span>
                </div>

                {formData.organization_size && (
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Taille</span>
                    <span className="font-medium text-gray-900 dark:text-white">
                      {ORGANIZATION_SIZES.find((s) => s.value === formData.organization_size)?.label}
                    </span>
                  </div>
                )}

                {formData.industry_sector && (
                  <div className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-400">Secteur</span>
                    <span className="font-medium text-gray-900 dark:text-white">
                      {INDUSTRY_SECTORS.find((s) => s.value === formData.industry_sector)?.label}
                    </span>
                  </div>
                )}

                <div className="flex justify-between">
                  <span className="text-gray-600 dark:text-gray-400">Niveau de sécurité</span>
                  <span className="font-medium text-gray-900 dark:text-white">
                    {SECURITY_LEVELS.find((l) => l.value === formData.security_level)?.label}
                  </span>
                </div>

                <div className="pt-3 border-t border-gray-200 dark:border-gray-600">
                  <span className="text-gray-600 dark:text-gray-400">Référentiels sélectionnés</span>
                  <div className="flex flex-wrap gap-2 mt-2">
                    {formData.selected_frameworks.map((fw) => (
                      <span
                        key={fw}
                        className="px-2 py-1 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 text-sm rounded"
                      >
                        {fw.toUpperCase().replace('_', ' ')}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            <div className="flex items-start gap-3 p-4 bg-blue-50 dark:bg-blue-900/30 rounded-lg">
              <Sparkles className="w-5 h-5 text-blue-600 dark:text-blue-400 mt-0.5" />
              <div>
                <p className="text-sm text-blue-800 dark:text-blue-200">
                  <strong>Génération IA avec Mistral</strong> - Les documents seront générés par
                  un modèle d'IA européen, respectueux du RGPD. Vous pourrez réviser et modifier
                  chaque document après génération.
                </p>
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl w-full max-w-3xl max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Créer un nouveau SMSI</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-600 dark:text-gray-400" />
          </button>
        </div>

        {/* Progress Steps */}
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
          <div className="flex items-center justify-between">
            {STEPS.map((step, index) => {
              const Icon = step.icon;
              const isActive = index === currentStep;
              const isCompleted = index < currentStep;

              return (
                <div
                  key={step.id}
                  className={`flex items-center ${index < STEPS.length - 1 ? 'flex-1' : ''}`}
                >
                  <div className="flex items-center gap-2">
                    <div
                      className={`w-8 h-8 rounded-full flex items-center justify-center ${
                        isCompleted
                          ? 'bg-green-500 text-white'
                          : isActive
                          ? 'bg-blue-500 text-white'
                          : 'bg-gray-200 dark:bg-gray-600 text-gray-500 dark:text-gray-400'
                      }`}
                    >
                      {isCompleted ? <Check className="w-4 h-4" /> : <Icon className="w-4 h-4" />}
                    </div>
                    <span
                      className={`text-sm font-medium ${
                        isActive ? 'text-blue-600 dark:text-blue-400' : 'text-gray-500 dark:text-gray-400'
                      }`}
                    >
                      {step.title}
                    </span>
                  </div>
                  {index < STEPS.length - 1 && (
                    <div
                      className={`flex-1 h-0.5 mx-4 ${
                        isCompleted ? 'bg-green-500' : 'bg-gray-200 dark:bg-gray-600'
                      }`}
                    />
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[50vh]">{renderStepContent()}</div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
          <button
            onClick={handleBack}
            disabled={currentStep === 0}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
              currentStep === 0
                ? 'text-gray-400 cursor-not-allowed'
                : 'text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
            }`}
          >
            <ChevronLeft className="w-4 h-4" />
            Précédent
          </button>

          <button
            onClick={handleNext}
            disabled={!canProceed() || createMutation.isPending}
            className={`flex items-center gap-2 px-6 py-2 rounded-lg transition-colors ${
              canProceed() && !createMutation.isPending
                ? 'bg-blue-600 text-white hover:bg-blue-700'
                : 'bg-gray-300 dark:bg-gray-600 text-gray-500 dark:text-gray-400 cursor-not-allowed'
            }`}
          >
            {createMutation.isPending ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Création...
              </>
            ) : currentStep === STEPS.length - 1 ? (
              <>
                <Sparkles className="w-4 h-4" />
                Créer le projet
              </>
            ) : (
              <>
                Suivant
                <ChevronRight className="w-4 h-4" />
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
