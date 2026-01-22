import { FileText, Download, RefreshCw, Trash2, Eye, CheckCircle, Clock } from 'lucide-react';

interface ProjectCardProps {
  project: {
    id: string;
    name: string;
    organization_name: string;
    status: string;
    completion_percentage: number;
    documents_generated: number;
    documents_total: number;
    selected_frameworks: string[];
    created_at: string;
  };
  onView: (id: string) => void;
  onDelete: (id: string) => void;
}

export function ProjectCard({ project, onView, onDelete }: ProjectCardProps) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-700';
      case 'generation':
        return 'bg-yellow-100 text-yellow-700';
      case 'review':
        return 'bg-blue-100 text-blue-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border p-6 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{project.name}</h3>
          <p className="text-sm text-gray-500 mt-1">{project.organization_name}</p>
        </div>
        <span className={`px-3 py-1 text-xs font-medium rounded-full ${getStatusColor(project.status)}`}>
          {project.status}
        </span>
      </div>

      {/* Frameworks */}
      <div className="flex flex-wrap gap-1 mt-3">
        {project.selected_frameworks.slice(0, 4).map((fw) => (
          <span key={fw} className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded">
            {fw.toUpperCase()}
          </span>
        ))}
        {project.selected_frameworks.length > 4 && (
          <span className="px-2 py-0.5 bg-gray-100 text-gray-600 text-xs rounded">
            +{project.selected_frameworks.length - 4}
          </span>
        )}
      </div>

      {/* Progress */}
      <div className="mt-4">
        <div className="flex justify-between text-sm text-gray-600 mb-1">
          <span>Documents</span>
          <span>{project.documents_generated}/{project.documents_total}</span>
        </div>
        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-blue-500 transition-all"
            style={{ width: `${project.completion_percentage}%` }}
          />
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-2 mt-4 pt-4 border-t">
        <button
          onClick={() => onView(project.id)}
          className="flex-1 flex items-center justify-center gap-2 px-3 py-2 text-sm text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
        >
          <Eye className="w-4 h-4" />
          Voir
        </button>
        <button
          onClick={() => onDelete(project.id)}
          className="p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
