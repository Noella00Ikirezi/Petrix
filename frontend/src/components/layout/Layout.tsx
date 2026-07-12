/**
 * Conteneur de mise en page principal de l'application authentifiée.
 * Compose la Sidebar (fixe à gauche), le Header (en haut) et la zone de contenu scrollable.
 * Gère l'overlay mobile pour masquer/afficher la sidebar sur petits écrans.
 */
import { ReactNode, useState } from 'react';
import Sidebar from './Sidebar';
import Header from './Header';

/** Props du Layout : children représente le contenu de la page active. */
interface LayoutProps {
  children: ReactNode;
}

/**
 * Layout applicatif : sidebar + header + main scrollable.
 * @param children - Contenu de la page à afficher dans la zone principale.
 */
export default function Layout({ children }: LayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div style={{ display: 'flex', height: '100vh', background: 'var(--bg)', overflow: 'hidden' }}>
      {/* Overlay mobile */}
      {sidebarOpen && (
        <div
          className="sidebar-overlay-lg"
          onClick={() => setSidebarOpen(false)}
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,.55)', zIndex: 40 }}
        />
      )}

      <Sidebar isOpen={sidebarOpen} />

      <div style={{ display: 'flex', flex: 1, flexDirection: 'column', overflow: 'hidden', minWidth: 0 }}>
        <Header onMenuClick={() => setSidebarOpen((v) => !v)} />
        <main
          className="animate-fade-up app-main"
          style={{ flex: 1, overflowY: 'auto', padding: 32 }}
        >
          {children}
        </main>
      </div>
    </div>
  );
}
