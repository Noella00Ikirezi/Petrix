import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import Layout from './components/Layout/Layout'
import DashboardPage from './pages/DashboardPage'
import TasksPage from './pages/TasksPage'
import ProjectsPage from './pages/ProjectsPage'
import CalendarPage from './pages/CalendarPage'
import DocumentsPage from './pages/DocumentsPage'
import KnowledgePage from './pages/KnowledgePage'
import SettingsPage from './pages/SettingsPage'

function App() {
  return (
    <BrowserRouter>
      <Toaster position="top-right" />
      <Layout>
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/tasks" element={<TasksPage />} />
          <Route path="/projects" element={<ProjectsPage />} />
          <Route path="/calendar" element={<CalendarPage />} />
          <Route path="/documents" element={<DocumentsPage />} />
          <Route path="/knowledge" element={<KnowledgePage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  )
}

export default App
