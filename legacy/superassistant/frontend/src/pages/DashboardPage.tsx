import { useEffect, useState } from 'react';
import { tasksAPI, aiAPI } from '../api/client';
import toast from 'react-hot-toast';
import { CheckCircle2, Clock, AlertCircle } from 'lucide-react';

export default function DashboardPage() {
  const [tasks, setTasks] = useState<any[]>([]);
  const [prioritization, setPrioritization] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadTasks();
  }, []);

  const loadTasks = async () => {
    try {
      const response = await tasksAPI.getAll({ status: 'todo,in_progress' });
      setTasks(response.data);
    } catch (error) {
      toast.error('Erreur lors du chargement des tâches');
    }
  };

  const getPrioritization = async () => {
    setLoading(true);
    try {
      const response = await aiAPI.prioritize({});
      setPrioritization(response.data);
      toast.success('Priorisation effectuée !');
    } catch (error) {
      toast.error('Erreur lors de la priorisation');
    } finally {
      setLoading(false);
    }
  };

  const stats = {
    total: tasks.length,
    todo: tasks.filter((t: any) => t.status === 'todo').length,
    in_progress: tasks.filter((t: any) => t.status === 'in_progress').length,
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Dashboard
        </h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          Vue d'ensemble de votre productivité
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card">
          <div className="flex items-center">
            <div className="p-3 bg-primary-100 dark:bg-primary-900 rounded-lg">
              <CheckCircle2 className="w-6 h-6 text-primary-600 dark:text-primary-400" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                Total Tâches
              </p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {stats.total}
              </p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="p-3 bg-yellow-100 dark:bg-yellow-900 rounded-lg">
              <Clock className="w-6 h-6 text-yellow-600 dark:text-yellow-400" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                À faire
              </p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {stats.todo}
              </p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="p-3 bg-blue-100 dark:bg-blue-900 rounded-lg">
              <AlertCircle className="w-6 h-6 text-blue-600 dark:text-blue-400" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600 dark:text-gray-400">
                En cours
              </p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">
                {stats.in_progress}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Priorisation IA */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">
            🤖 Priorisation IA
          </h2>
          <button
            onClick={getPrioritization}
            disabled={loading}
            className="btn btn-primary"
          >
            {loading ? 'Analyse en cours...' : 'Analyser mes tâches'}
          </button>
        </div>

        {prioritization && (
          <div className="space-y-4">
            <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <h3 className="font-semibold text-blue-900 dark:text-blue-300 mb-2">
                Analyse
              </h3>
              <p className="text-blue-800 dark:text-blue-200">
                {prioritization.analysis}
              </p>
            </div>

            <div>
              <h3 className="font-semibold text-gray-900 dark:text-white mb-3">
                Top 5 Priorités
              </h3>
              <div className="space-y-2">
                {prioritization.top_tasks.map((task: any, index: number) => (
                  <div
                    key={task.task_id}
                    className="flex items-start p-3 bg-gray-50 dark:bg-gray-700 rounded-lg"
                  >
                    <span className="flex items-center justify-center w-6 h-6 bg-primary-600 text-white text-sm font-bold rounded-full mr-3">
                      {index + 1}
                    </span>
                    <div className="flex-1">
                      <p className="font-medium text-gray-900 dark:text-white">
                        {task.title}
                      </p>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                        {task.justification}
                      </p>
                      <div className="mt-2">
                        <div className="w-full bg-gray-200 dark:bg-gray-600 rounded-full h-2">
                          <div
                            className="bg-primary-600 h-2 rounded-full"
                            style={{ width: `${task.priority_score}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
              <h3 className="font-semibold text-green-900 dark:text-green-300 mb-2">
                Planning Journalier Suggéré
              </h3>
              <p className="text-green-800 dark:text-green-200 whitespace-pre-wrap">
                {prioritization.daily_plan}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
