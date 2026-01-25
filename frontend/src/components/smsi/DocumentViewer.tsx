import { useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface DocumentViewerProps {
  content: string;
  documentCode: string;
  documentName: string;
  documentType: string;
  version: string;
  organization: string;
  status: string;
  createdAt?: string;
}

// Color schemes for different document types
const DOCUMENT_COLORS: Record<string, { primary: string; secondary: string; accent: string }> = {
  DIRECTIVE: {
    primary: '#1e3a5f',      // Dark blue
    secondary: '#2563eb',    // Blue
    accent: '#3b82f6',       // Light blue
  },
  POLICY: {
    primary: '#14532d',      // Dark green
    secondary: '#16a34a',    // Green
    accent: '#22c55e',       // Light green
  },
  PROCEDURE: {
    primary: '#7c2d12',      // Dark orange
    secondary: '#ea580c',    // Orange
    accent: '#f97316',       // Light orange
  },
  REGISTER: {
    primary: '#581c87',      // Dark purple
    secondary: '#9333ea',    // Purple
    accent: '#a855f7',       // Light purple
  },
  ANNEX: {
    primary: '#1e3a5f',      // Dark blue
    secondary: '#0891b2',    // Cyan
    accent: '#06b6d4',       // Light cyan
  },
  DEFAULT: {
    primary: '#374151',      // Gray
    secondary: '#6b7280',    // Gray
    accent: '#9ca3af',       // Light gray
  },
};

export function DocumentViewer({
  content,
  documentCode,
  documentName,
  documentType,
  version,
  organization,
  status,
  createdAt,
}: DocumentViewerProps) {
  const colors = DOCUMENT_COLORS[documentType] || DOCUMENT_COLORS.DEFAULT;
  const date = createdAt ? new Date(createdAt).toLocaleDateString('fr-FR') : new Date().toLocaleDateString('fr-FR');

  // Parse metadata from content if present
  const { cleanContent, metadata } = useMemo(() => {
    let meta: Record<string, string> = {};
    let clean = content;

    // Extract YAML frontmatter if present
    const yamlMatch = content.match(/^---\n([\s\S]*?)\n---/);
    if (yamlMatch) {
      clean = content.replace(yamlMatch[0], '').trim();
      const yamlContent = yamlMatch[1];
      yamlContent.split('\n').forEach(line => {
        const [key, ...valueParts] = line.split(':');
        if (key && valueParts.length) {
          meta[key.trim()] = valueParts.join(':').trim().replace(/^["']|["']$/g, '');
        }
      });
    }

    return { cleanContent: clean, metadata: meta };
  }, [content]);

  const statusLabels: Record<string, string> = {
    draft: 'Brouillon',
    review: 'En révision',
    approved: 'Validé',
    published: 'Publié',
  };

  const typeLabels: Record<string, string> = {
    DIRECTIVE: 'Directive Stratégique',
    POLICY: 'Politique',
    PROCEDURE: 'Procédure',
    REGISTER: 'Registre',
    ANNEX: 'Annexe',
    CHECKLIST: 'Checklist',
    REPORT: 'Rapport',
    MATRIX: 'Matrice',
    TEMPLATE: 'Template',
    SCHEMA: 'Schéma',
  };

  return (
    <div className="document-viewer bg-white dark:bg-slate-900 min-h-full">
      {/* Cover Page / Header */}
      <div
        className="document-header relative overflow-hidden"
        style={{
          background: `linear-gradient(135deg, ${colors.primary} 0%, ${colors.secondary} 100%)`,
        }}
      >
        {/* Decorative elements */}
        <div className="absolute top-0 right-0 w-64 h-64 opacity-10">
          <svg viewBox="0 0 200 200" className="w-full h-full">
            <path
              fill="white"
              d="M40,-65.5C51.2,-58.2,59.4,-45.6,65.8,-31.8C72.2,-18,76.8,-3.1,74.8,10.9C72.8,24.9,64.2,38,52.8,47.8C41.4,57.6,27.2,64,12.1,68.5C-3,73,-19,75.6,-33.5,71.2C-48,66.8,-61,55.4,-68.5,41.2C-76,27,-78,10,-76.1,-6.5C-74.2,-23,-68.4,-39,-57.6,-50.8C-46.8,-62.6,-31,-70.2,-15.1,-73.3C0.8,-76.4,28.8,-72.8,40,-65.5Z"
              transform="translate(100 100)"
            />
          </svg>
        </div>

        <div className="relative z-10 px-8 py-12">
          {/* Organization name - Large and prominent */}
          <div className="mb-8">
            <h1 className="text-4xl md:text-5xl font-bold text-white tracking-tight">
              {organization}
            </h1>
            <div className="mt-2 w-24 h-1 bg-white/50 rounded-full"></div>
          </div>

          {/* Document type badge */}
          <div className="mb-6">
            <span
              className="inline-block px-4 py-2 text-sm font-semibold rounded-lg"
              style={{ backgroundColor: 'rgba(255,255,255,0.2)', color: 'white' }}
            >
              {typeLabels[documentType] || documentType}
            </span>
          </div>

          {/* Document title */}
          <h2 className="text-2xl md:text-3xl font-semibold text-white mb-8 leading-tight max-w-3xl">
            {documentName}
          </h2>

          {/* Metadata table */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-white/90">
            <div className="bg-white/10 rounded-lg p-4">
              <p className="text-xs text-white/60 uppercase tracking-wider mb-1">Code Document</p>
              <p className="font-semibold">{documentCode}</p>
            </div>
            <div className="bg-white/10 rounded-lg p-4">
              <p className="text-xs text-white/60 uppercase tracking-wider mb-1">Version</p>
              <p className="font-semibold">{version}</p>
            </div>
            <div className="bg-white/10 rounded-lg p-4">
              <p className="text-xs text-white/60 uppercase tracking-wider mb-1">Date</p>
              <p className="font-semibold">{date}</p>
            </div>
            <div className="bg-white/10 rounded-lg p-4">
              <p className="text-xs text-white/60 uppercase tracking-wider mb-1">Statut</p>
              <p className="font-semibold">{statusLabels[status] || status}</p>
            </div>
          </div>

          {/* Classification badge */}
          <div className="mt-6 flex items-center gap-4">
            <span className="px-3 py-1 bg-yellow-500/20 text-yellow-200 text-sm font-medium rounded-full border border-yellow-400/30">
              Classification: {metadata.classification || 'Interne'}
            </span>
            <span className="px-3 py-1 bg-white/10 text-white/80 text-sm rounded-full">
              Propriétaire: {metadata.owner || 'RSSI'}
            </span>
          </div>
        </div>
      </div>

      {/* Document Body */}
      <div className="document-body px-8 py-10 max-w-4xl mx-auto">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            // Headings with PSSIG-style numbering colors
            h1: ({ children, ...props }) => (
              <h1
                className="text-3xl font-bold mt-12 mb-6 pb-3 border-b-2 text-gray-900 dark:text-white"
                style={{ borderColor: colors.secondary }}
                {...props}
              >
                {children}
              </h1>
            ),
            h2: ({ children, ...props }) => (
              <h2
                className="text-2xl font-semibold mt-10 mb-4 text-gray-800 dark:text-gray-100 flex items-center gap-3"
                {...props}
              >
                <span
                  className="inline-block w-1 h-8 rounded-full"
                  style={{ backgroundColor: colors.secondary }}
                ></span>
                {children}
              </h2>
            ),
            h3: ({ children, ...props }) => (
              <h3
                className="text-xl font-semibold mt-8 mb-3 text-gray-700 dark:text-gray-200"
                style={{ color: colors.secondary }}
                {...props}
              >
                {children}
              </h3>
            ),
            h4: ({ children, ...props }) => (
              <h4
                className="text-lg font-medium mt-6 mb-2 text-gray-700 dark:text-gray-300"
                {...props}
              >
                {children}
              </h4>
            ),

            // Paragraphs
            p: ({ children, ...props }) => (
              <p className="text-gray-700 dark:text-gray-300 leading-relaxed mb-4" {...props}>
                {children}
              </p>
            ),

            // Lists with custom styling
            ul: ({ children, ...props }) => (
              <ul className="list-none space-y-2 mb-6 ml-4" {...props}>
                {children}
              </ul>
            ),
            ol: ({ children, ...props }) => (
              <ol className="list-decimal space-y-2 mb-6 ml-6 text-gray-700 dark:text-gray-300" {...props}>
                {children}
              </ol>
            ),
            li: ({ children, ...props }) => (
              <li className="text-gray-700 dark:text-gray-300 flex items-start gap-2" {...props}>
                <span
                  className="inline-block w-2 h-2 rounded-full mt-2 flex-shrink-0"
                  style={{ backgroundColor: colors.accent }}
                ></span>
                <span>{children}</span>
              </li>
            ),

            // Tables with professional styling
            table: ({ children, ...props }) => (
              <div className="overflow-x-auto my-6 rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm">
                <table className="w-full border-collapse" {...props}>
                  {children}
                </table>
              </div>
            ),
            thead: ({ children, ...props }) => (
              <thead
                style={{ backgroundColor: colors.primary }}
                {...props}
              >
                {children}
              </thead>
            ),
            th: ({ children, ...props }) => (
              <th
                className="px-4 py-3 text-left text-sm font-semibold text-white border-b border-white/20"
                {...props}
              >
                {children}
              </th>
            ),
            tbody: ({ children, ...props }) => (
              <tbody className="bg-white dark:bg-slate-800 divide-y divide-gray-200 dark:divide-gray-700" {...props}>
                {children}
              </tbody>
            ),
            tr: ({ children, ...props }) => (
              <tr className="hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors" {...props}>
                {children}
              </tr>
            ),
            td: ({ children, ...props }) => (
              <td className="px-4 py-3 text-sm text-gray-700 dark:text-gray-300" {...props}>
                {children}
              </td>
            ),

            // Blockquotes for important notes
            blockquote: ({ children, ...props }) => (
              <blockquote
                className="my-6 p-4 rounded-lg border-l-4"
                style={{
                  borderColor: colors.secondary,
                  backgroundColor: `${colors.secondary}10`,
                }}
                {...props}
              >
                <div className="text-gray-700 dark:text-gray-300 italic">
                  {children}
                </div>
              </blockquote>
            ),

            // Code blocks
            code: ({ className, children, ...props }) => {
              const isBlock = className?.includes('language-');
              if (isBlock) {
                return (
                  <pre className="my-4 p-4 rounded-lg bg-slate-900 dark:bg-slate-950 overflow-x-auto">
                    <code className="text-sm text-gray-100 font-mono" {...props}>
                      {children}
                    </code>
                  </pre>
                );
              }
              return (
                <code
                  className="px-2 py-1 rounded text-sm font-mono"
                  style={{
                    backgroundColor: `${colors.secondary}20`,
                    color: colors.primary,
                  }}
                  {...props}
                >
                  {children}
                </code>
              );
            },

            // Horizontal rules
            hr: () => (
              <hr className="my-8 border-0 h-px bg-gradient-to-r from-transparent via-gray-300 dark:via-gray-600 to-transparent" />
            ),

            // Strong/Bold text
            strong: ({ children, ...props }) => (
              <strong className="font-semibold text-gray-900 dark:text-white" {...props}>
                {children}
              </strong>
            ),

            // Links
            a: ({ children, href, ...props }) => (
              <a
                href={href}
                className="font-medium underline underline-offset-2 transition-colors"
                style={{ color: colors.secondary }}
                {...props}
              >
                {children}
              </a>
            ),
          }}
        >
          {cleanContent}
        </ReactMarkdown>
      </div>

      {/* Footer */}
      <div
        className="document-footer px-8 py-6 mt-8 border-t"
        style={{ borderColor: `${colors.secondary}30` }}
      >
        <div className="max-w-4xl mx-auto flex items-center justify-between text-sm text-gray-500 dark:text-gray-400">
          <div>
            <p className="font-medium" style={{ color: colors.secondary }}>{organization}</p>
            <p>Document de référence SMSI</p>
          </div>
          <div className="text-right">
            <p>{documentCode} - Version {version}</p>
            <p>Généré le {date}</p>
          </div>
        </div>
      </div>

      {/* Print styles - embedded for export compatibility */}
      <style>{`
        @media print {
          .document-viewer {
            background: white !important;
          }
          .document-header {
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
          }
          .document-body {
            color: black !important;
          }
          .document-body h1,
          .document-body h2,
          .document-body h3,
          .document-body h4 {
            color: black !important;
          }
          .document-body p,
          .document-body li,
          .document-body td {
            color: #333 !important;
          }
          thead {
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
          }
        }
      `}</style>
    </div>
  );
}
