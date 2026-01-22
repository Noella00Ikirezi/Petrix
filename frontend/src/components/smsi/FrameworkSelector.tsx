import { Check, Shield, AlertTriangle, Info } from 'lucide-react';

interface Framework {
  code: string;
  name: string;
  version: string;
  description: string;
  category: string;
  is_mandatory: boolean;
  color?: string;
}

interface FrameworkSelectorProps {
  frameworks: Framework[];
  selected: string[];
  onToggle: (code: string) => void;
}

const FRAMEWORK_COLORS: Record<string, string> = {
  iso_27001: 'blue',
  iso_27002: 'blue',
  dora: 'purple',
  nis2: 'indigo',
  rgpd: 'green',
  pci_dss: 'orange',
  eu_ai_act: 'pink',
  nist_csf: 'cyan',
  soc2: 'teal',
  enisa: 'violet',
};

const FRAMEWORK_ICONS: Record<string, string> = {
  iso_27001: '🔐',
  iso_27002: '🔒',
  dora: '🏦',
  nis2: '🇪🇺',
  rgpd: '👤',
  pci_dss: '💳',
  eu_ai_act: '🤖',
  nist_csf: '🛡️',
  soc2: '✅',
  enisa: '🔑',
};

export function FrameworkSelector({ frameworks, selected, onToggle }: FrameworkSelectorProps) {
  const groupedFrameworks = frameworks.reduce((acc, fw) => {
    const category = fw.category || 'general';
    if (!acc[category]) acc[category] = [];
    acc[category].push(fw);
    return acc;
  }, {} as Record<string, Framework[]>);

  const categoryLabels: Record<string, string> = {
    general: 'Standards internationaux',
    eu: 'Réglementations européennes',
    financial: 'Secteur financier',
    industry: 'Standards sectoriels',
  };

  return (
    <div className="space-y-6">
      {Object.entries(groupedFrameworks).map(([category, fws]) => (
        <div key={category}>
          <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
            <Shield className="w-4 h-4" />
            {categoryLabels[category] || category}
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {fws.map((fw) => {
              const isSelected = selected.includes(fw.code);
              const color = FRAMEWORK_COLORS[fw.code] || 'gray';
              const icon = FRAMEWORK_ICONS[fw.code] || '📋';

              return (
                <div
                  key={fw.code}
                  onClick={() => onToggle(fw.code)}
                  className={`relative p-4 border-2 rounded-xl cursor-pointer transition-all duration-200 ${
                    isSelected
                      ? `border-${color}-500 bg-${color}-50 shadow-sm`
                      : 'border-gray-200 hover:border-gray-300 hover:shadow-sm'
                  }`}
                >
                  {/* Selection indicator */}
                  <div
                    className={`absolute top-3 right-3 w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all ${
                      isSelected
                        ? `border-${color}-500 bg-${color}-500`
                        : 'border-gray-300'
                    }`}
                  >
                    {isSelected && <Check className="w-4 h-4 text-white" />}
                  </div>

                  {/* Content */}
                  <div className="pr-8">
                    <div className="flex items-center gap-2">
                      <span className="text-xl">{icon}</span>
                      <div>
                        <h4 className="font-semibold text-gray-900">{fw.name}</h4>
                        <span className="text-xs text-gray-500">v{fw.version}</span>
                      </div>
                    </div>

                    <p className="text-sm text-gray-600 mt-2 line-clamp-2">
                      {fw.description}
                    </p>

                    {/* Tags */}
                    <div className="flex items-center gap-2 mt-3">
                      {fw.is_mandatory && (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-red-100 text-red-700 text-xs rounded-full">
                          <AlertTriangle className="w-3 h-3" />
                          Obligatoire
                        </span>
                      )}
                      <span className={`px-2 py-0.5 bg-${color}-100 text-${color}-700 text-xs rounded-full`}>
                        {fw.category}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ))}

      {/* Info box */}
      <div className="flex items-start gap-3 p-4 bg-blue-50 rounded-lg border border-blue-200">
        <Info className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
        <div className="text-sm text-blue-800">
          <p className="font-medium">Mapping automatique</p>
          <p className="mt-1">
            Les contrôles sont automatiquement mappés entre les référentiels sélectionnés.
            Un document unique peut satisfaire plusieurs exigences.
          </p>
        </div>
      </div>
    </div>
  );
}
