import { useEffect, useState } from 'react';
import { tasksAPI } from '../api/client';
import toast from 'react-hot-toast';
import { Plus, Filter } from 'lucide-react';

export default function TasksPage() {
  const [tasks, setTasks] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    loadTasks();
  }, [filter]);

  const loadTasks = async () => {
    setLoading(true);
    try {
      const params = filter !== 'all' ? { status: filter } : {};
      const response = await tasksAPI.getAll(params);
      setTasks(response.data);
    } catch (error) {
      toast.error('Erreur lors du chargement des tâches');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Tâches
          </h1>
          <p className="mt-2 text-gray-600 dark:text-gray-400">
            Gérez vos tâches et améliorez votre productivité
          </p>
        </div>
        <button className="btn btn-primary">
          <Plus className="w-5 h-5 mr-2" />
          Nouvelle tâche
        </button>
      </div>

      {/* Filtres */}
      <div className="flex space-x-2">
        {['all', 'todo', 'in_progress', 'completed'].map((status) => (
          <button
            key={status}
            onClick={() => setFilter(status)}
            className={`px-4 py-2 rounded-lg text-sm font-medium ${
              filter === status
                ? 'bg-primary-600 text-white'
                : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
            }`}
          >
            {status === 'all' ? 'Toutes' :
             status === 'todo' ? 'À faire' :
             status === 'in_progress' ? 'En cours' : 'Terminées'}
          </button>
        ))}
      </div>

      {/* Liste des tâches */}
      <div className="grid gap-4">
        {loading ? (
          <div className="card text-center py-8">Chargement...</div>
        ) : tasks.length === 0 ? (
          <div className="card text-center py-8 text-gray-500 dark:text-gray-400">
            Aucune tâche trouvée
          </div>
        ) : (
          tasks.map((task) => (
            <div key={task.id} className="card hover:shadow-lg transition-shadow">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                      {task.title}
                    </h3>
                    <span className={`px-2 py-1 text-xs rounded-full ${
                      task.priority === 'haute' ? 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300' :
                      task.priority === 'moyenne' ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300' :
                      'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300'
                    }`}>
                      {task.priority}
                    </span>
                  </div>
                  {task.description && (
                    <p className="mt-2 text-gray-600 dark:text-gray-400">
                      {task.description}
                    </p>
                  )}
                  <div className="mt-3 flex items-center space-x-4 text-sm text-gray-500 dark:text-gray-400">
                    <span className="px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded">
                      {task.category}
                    </span>
                    {task.deadline && (
                      <span>📅 {new Date(task.deadline).toLocaleDateString('fr-FR')}</span>
                    )}
                    {task.estimated_time && (
                      <span>⏱️ {task.estimated_time}h</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
