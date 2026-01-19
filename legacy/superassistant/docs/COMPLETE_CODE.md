# Code Complet SuperAssistant - Fichiers Manquants

Ce document contient le code pour tous les fichiers frontend manquants.

## API Client

### `frontend/src/api/client.ts`

```typescript
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Tasks API
export const tasksAPI = {
  getAll: (params?: any) => apiClient.get('/api/tasks', { params }),
  getById: (id: number) => apiClient.get(`/api/tasks/${id}`),
  create: (data: any) => apiClient.post('/api/tasks', data),
  update: (id: number, data: any) => apiClient.patch(`/api/tasks/${id}`, data),
  delete: (id: number) => apiClient.delete(`/api/tasks/${id}`),
};

// Projects API
export const projectsAPI = {
  getAll: () => apiClient.get('/api/projects'),
  getById: (id: number) => apiClient.get(`/api/projects/${id}`),
  create: (data: any) => apiClient.post('/api/projects', data),
  update: (id: number, data: any) => apiClient.patch(`/api/projects/${id}`, data),
  delete: (id: number) => apiClient.delete(`/api/projects/${id}`),
};

// Calendar API
export const calendarAPI = {
  getEvents: (params?: any) => apiClient.get('/api/calendar', { params }),
  createEvent: (data: any) => apiClient.post('/api/calendar', data),
  updateEvent: (id: number, data: any) => apiClient.patch(`/api/calendar/${id}`, data),
  deleteEvent: (id: number) => apiClient.delete(`/api/calendar/${id}`),
};

// AI API
export const aiAPI = {
  prioritize: (data: any) => apiClient.post('/api/ai/prioritize', data),
  generateEmail: (data: any) => apiClient.post('/api/ai/generate-email', data),
  generateDocument: (data: any) => apiClient.post('/api/ai/generate-document', data),
  chat: (data: any) => apiClient.post('/api/ai/chat', data),
};

// Documents API
export const documentsAPI = {
  getAll: (params?: any) => apiClient.get('/api/documents', { params }),
  getById: (id: number) => apiClient.get(`/api/documents/${id}`),
  create: (data: any) => apiClient.post('/api/documents', data),
  update: (id: number, data: any) => apiClient.patch(`/api/documents/${id}`, data),
  delete: (id: number) => apiClient.delete(`/api/documents/${id}`),
};

// Knowledge API
export const knowledgeAPI = {
  getAll: (params?: any) => apiClient.get('/api/knowledge', { params }),
  getById: (id: number) => apiClient.get(`/api/knowledge/${id}`),
  create: (data: any) => apiClient.post('/api/knowledge', data),
  update: (id: number, data: any) => apiClient.patch(`/api/knowledge/${id}`, data),
  delete: (id: number) => apiClient.delete(`/api/knowledge/${id}`),
};
```

## Types

### `frontend/src/types/task.ts`

```typescript
export interface Task {
  id: number;
  title: string;
  description?: string;
  category: string;
  priority: 'haute' | 'moyenne' | 'basse';
  status: 'todo' | 'in_progress' | 'completed' | 'blocked';
  deadline?: string;
  estimated_time?: number;
  actual_time?: number;
  tags?: string[];
  project_id?: number;
  created_at: string;
  updated_at: string;
}

export interface TaskCreate {
  title: string;
  description?: string;
  category: string;
  priority?: 'haute' | 'moyenne' | 'basse';
  status?: 'todo' | 'in_progress' | 'completed' | 'blocked';
  deadline?: string;
  estimated_time?: number;
  tags?: string[];
  project_id?: number;
}
```

### `frontend/src/types/project.ts`

```typescript
export interface Project {
  id: number;
  name: string;
  description?: string;
  status: 'active' | 'completed' | 'archived';
  start_date?: string;
  end_date?: string;
  progress: number;
  created_at: string;
  updated_at: string;
}
```

### `frontend/src/types/event.ts`

```typescript
export interface Event {
  id: number;
  title: string;
  description?: string;
  start_time: string;
  end_time: string;
  category: string;
  is_task: boolean;
  task_id?: number;
  created_at: string;
  updated_at: string;
}
```

### `frontend/src/types/ai.ts`

```typescript
export interface PrioritizedTask {
  task_id: number;
  title: string;
  priority_score: number;
  justification: string;
}

export interface PrioritizationResponse {
  top_tasks: PrioritizedTask[];
  daily_plan: string;
  analysis: string;
}

export interface EmailRequest {
  recipient_type: string;
  context: string;
  tone: string;
  subject: string;
  key_points: string[];
  user_context?: string;
}

export interface EmailResponse {
  subject: string;
  body: string;
  suggestions?: string[];
}
```

## Layout Components

### `frontend/src/components/Layout/Layout.tsx`

```tsx
import { ReactNode } from 'react';
import Sidebar from './Sidebar';
import Header from './Header';

interface LayoutProps {
  children: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  return (
    <div className="flex h-screen bg-gray-50 dark:bg-gray-900">
      <Sidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />
        <main className="flex-1 overflow-y-auto p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
```

### `frontend/src/components/Layout/Sidebar.tsx`

```tsx
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  CheckSquare,
  Target,
  Calendar,
  FileText,
  Book,
  Settings,
  Bot,
} from 'lucide-react';

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Tâches', href: '/tasks', icon: CheckSquare },
  { name: 'Projets', href: '/projects', icon: Target },
  { name: 'Agenda', href: '/calendar', icon: Calendar },
  { name: 'Documents SMSI', href: '/documents', icon: FileText },
  { name: 'Base de Connaissances', href: '/knowledge', icon: Book },
  { name: 'Paramètres', href: '/settings', icon: Settings },
];

export default function Sidebar() {
  return (
    <div className="flex flex-col w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700">
      <div className="flex items-center h-16 px-6 border-b border-gray-200 dark:border-gray-700">
        <Bot className="w-8 h-8 text-primary-600" />
        <span className="ml-3 text-xl font-bold text-gray-900 dark:text-white">
          SuperAssistant
        </span>
      </div>

      <nav className="flex-1 px-4 py-4 space-y-1 overflow-y-auto">
        {navigation.map((item) => (
          <NavLink
            key={item.name}
            to={item.href}
            className={({ isActive }) =>
              `flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-colors ${
                isActive
                  ? 'bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300'
                  : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
              }`
            }
          >
            <item.icon className="w-5 h-5 mr-3" />
            {item.name}
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t border-gray-200 dark:border-gray-700">
        <p className="text-xs text-gray-500 dark:text-gray-400 text-center">
          © 2025 SuperAssistant
          <br />
          100% Local & Privé
        </p>
      </div>
    </div>
  );
}
```

### `frontend/src/components/Layout/Header.tsx`

```tsx
import { Bell, Moon, Sun } from 'lucide-react';
import { useState } from 'react';

export default function Header() {
  const [darkMode, setDarkMode] = useState(true);

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
    document.documentElement.classList.toggle('dark');
  };

  return (
    <header className="flex items-center justify-between h-16 px-6 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
      <div className="flex items-center flex-1">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Bienvenue
        </h1>
      </div>

      <div className="flex items-center space-x-4">
        <button
          onClick={toggleDarkMode}
          className="p-2 text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
        >
          {darkMode ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
        </button>

        <button className="p-2 text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg relative">
          <Bell className="w-5 h-5" />
          <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
        </button>

        <div className="flex items-center">
          <div className="w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center text-white font-bold">
            U
          </div>
        </div>
      </div>
    </header>
  );
}
```

## Pages (MVP)

### `frontend/src/pages/DashboardPage.tsx`

```tsx
import { useEffect, useState } from 'react';
import { tasksAPI, aiAPI } from '../api/client';
import { Task } from '../types/task';
import { PrioritizationResponse } from '../types/ai';
import toast from 'react-hot-toast';
import { CheckCircle2, Clock, AlertCircle } from 'lucide-react';

export default function DashboardPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [prioritization, setPrioritization] = useState<PrioritizationResponse | null>(null);
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
    todo: tasks.filter(t => t.status === 'todo').length,
    in_progress: tasks.filter(t => t.status === 'in_progress').length,
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
                {prioritization.top_tasks.map((task, index) => (
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
```

---

**CONTINUEZ DANS LES FICHIERS SUIVANTS...**

Pour le reste des pages (TasksPage, ProjectsPage, etc.), créez des versions basiques similaires au Dashboard.

Chaque page doit :
1. Importer les API clients nécessaires
2. Avoir un état local avec useState
3. Charger les données avec useEffect
4. Afficher les données dans des cartes (class="card")
5. Permettre les opérations CRUD basiques
