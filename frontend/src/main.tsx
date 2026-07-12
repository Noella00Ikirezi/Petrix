/**
 * Point d'entrée de l'application React.
 * Monte l'arbre de providers : QueryClientProvider (React Query), BrowserRouter (routing),
 * Toaster (notifications), et initialise le mode sombre par défaut via localStorage.
 */
import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import App from './App';
import './index.css';

// Dark mode par défaut
if (localStorage.getItem('darkMode') !== 'false') {
  document.documentElement.classList.add('dark');
  if (!localStorage.getItem('darkMode')) localStorage.setItem('darkMode', 'true');
}

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
        <App />
        <Toaster position="top-right" />
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>
);
