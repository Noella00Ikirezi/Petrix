import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Search, Shield, AlertTriangle } from 'lucide-react';
import { vulnsApi } from '@/api/client';

export default function VulnerabilitiesPage() {
  const [search, setSearch] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  const { data, isLoading } = useQuery({
    queryKey: ['vulnerabilities', search, severityFilter, statusFilter],
    queryFn: () =>
      vulnsApi.list({
        search: search || undefined,
        severity: severityFilter || undefined,
        status: statusFilter || undefined,
      }),
  });

  const vulns = data?.items || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Vulnerabilities
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Track and manage security vulnerabilities
        </p>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
          <input
            type="text"
            placeholder="Search vulnerabilities..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="input pl-10"
          />
        </div>
        <select
          value={severityFilter}
          onChange={(e) => setSeverityFilter(e.target.value)}
          className="input w-40"
        >
          <option value="">All Severities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
          <option value="info">Info</option>
        </select>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="input w-40"
        >
          <option value="">All Statuses</option>
          <option value="open">Open</option>
          <option value="in_progress">In Progress</option>
          <option value="resolved">Resolved</option>
          <option value="accepted">Accepted</option>
          <option value="false_positive">False Positive</option>
        </select>
      </div>

      {/* Table */}
      <div className="card overflow-hidden p-0">
        {isLoading ? (
          <div className="flex h-64 items-center justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-500 border-t-transparent" />
          </div>
        ) : vulns.length === 0 ? (
          <div className="flex h-64 flex-col items-center justify-center text-gray-500">
            <Shield className="mb-2 h-12 w-12" />
            <p>No vulnerabilities found</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-700">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                    Title
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                    Severity
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                    CVSS
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                    CVE
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-400">
                    Discovered
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 bg-white dark:divide-gray-700 dark:bg-gray-800">
                {vulns.map((vuln: Vuln) => (
                  <tr key={vuln.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                    <td className="px-6 py-4">
                      <div className="flex items-center">
                        <AlertTriangle
                          className={`mr-3 h-5 w-5 ${getSeverityColor(vuln.severity)}`}
                        />
                        <div>
                          <div className="font-medium text-gray-900 dark:text-white">
                            {vuln.title}
                          </div>
                          <div className="max-w-md truncate text-sm text-gray-500 dark:text-gray-400">
                            {vuln.description || '-'}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td className="whitespace-nowrap px-6 py-4">
                      <SeverityBadge severity={vuln.severity} />
                    </td>
                    <td className="whitespace-nowrap px-6 py-4">
                      <StatusBadge status={vuln.status} />
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-900 dark:text-white">
                      {vuln.cvss_score ? vuln.cvss_score.toFixed(1) : '-'}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm">
                      {vuln.cve_ids && vuln.cve_ids.length > 0 ? (
                        <span className="text-primary-600 dark:text-primary-400">
                          {vuln.cve_ids[0]}
                          {vuln.cve_ids.length > 1 && ` +${vuln.cve_ids.length - 1}`}
                        </span>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500 dark:text-gray-400">
                      {new Date(vuln.discovered_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

interface Vuln {
  id: string;
  title: string;
  description: string | null;
  severity: string;
  status: string;
  cvss_score: number | null;
  cve_ids: string[];
  discovered_at: string;
}

function getSeverityColor(severity: string): string {
  const colors: Record<string, string> = {
    critical: 'text-red-500',
    high: 'text-orange-500',
    medium: 'text-yellow-500',
    low: 'text-green-500',
    info: 'text-gray-500',
  };
  return colors[severity] || 'text-gray-500';
}

function SeverityBadge({ severity }: { severity: string }) {
  const styles: Record<string, string> = {
    critical: 'badge-critical',
    high: 'badge-high',
    medium: 'badge-medium',
    low: 'badge-low',
    info: 'badge-info',
  };

  return <span className={`badge ${styles[severity] || ''}`}>{severity}</span>;
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    open: 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300',
    in_progress: 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300',
    resolved: 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300',
    accepted: 'bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300',
    false_positive: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
  };

  return (
    <span className={`badge ${styles[status] || ''}`}>
      {status.replace('_', ' ')}
    </span>
  );
}
