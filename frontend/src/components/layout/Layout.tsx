import { ReactNode, useState } from 'react';
import Sidebar from './Sidebar';
import Header from './Header';

interface LayoutProps {
  children: ReactNode;
}

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
