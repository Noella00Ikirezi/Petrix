import { useEffect, useState } from 'react';
import { projectsAPI } from '../api/client';
import toast from 'react-hot-toast';
import { Plus } from 'lucide-react';

export default function ProjectsPage() {
  const [projects, setProjects] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    setLoading(true);
    try {
      const response = await projectsAPI.getAll();
      setProjects(response.data);
    } catch (error) {
      toast.error('Erreur lors du chargement des projets');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Projets
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Gérez vos projets et suivez leur avancement
          </p>
        </div>
        <button className="btn btn-primary">
          <Plus className="w-5 h-5 mr-2" />
          Nouveau projet
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {loading ? (
          <div className="card text-center py-8 col-span-full">Chargement...</div>
        ) : projects.length === 0 ? (
          <div className="card text-center py-8 col-span-full text-gray-500 dark:text-gray-400">
            Aucun projet trouvé
          </div>
        ) : (
          projects.map((project) => (
            <div key={project.id} className="card hover:shadow-lg transition-shadow">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white">
                  {project.name}
                </h3>
                <span className={`px-3 py-1 text-xs font-medium rounded-full ${
                  project.status === 'active' ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300' :
                  project.status === 'completed' ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300' :
                  'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
                }`}>
                  {project.status}
                </span>
              </div>

              {project.description && (
                <p className="text-gray-600 dark:text-gray-400 mb-4">
                  {project.description}
                </p>
              )}

              <div className="space-y-2">
                <div className="flex justify-between text-sm text-gray-600 dark:text-gray-400">
                  <span>Progression</span>
                  <span className="font-medium">{project.progress}%</span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div
                    className="bg-primary-600 h-2 rounded-full transition-all"
                    style={{ width: `${project.progress}%` }}
                  />
                </div>
              </div>

              {project.start_date && (
                <div className="mt-4 text-sm text-gray-500 dark:text-gray-400">
                  Début: {new Date(project.start_date).toLocaleDateString('fr-FR')}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
