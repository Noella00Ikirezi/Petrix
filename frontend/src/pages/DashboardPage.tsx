import { useQuery } from '@tanstack/react-query';
import {
  Server,
  Shield,
  Scan,
  AlertTriangle,
  TrendingUp,
  Activity,
} from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { dashboardApi } from '@/api/client';

const SEVERITY_COLORS = {
  critical: '#dc2626',
  high: '#ea580c',
  medium: '#f59e0b',
  low: '#84cc16',
  info: '#6b7280',
};

export default function DashboardPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['dashboard'],
    queryFn: dashboardApi.get,
  });

  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-500 border-t-transparent" />
      </div>
    );
  }

  const stats = data?.stats;
  const vulnBySeverity = data?.vuln_by_severity || {};
  const recentScans = data?.recent_scans || [];
  const vulnTrends = data?.vuln_trends || [];

  // Prepare pie chart data
  const pieData = Object.entries(vulnBySeverity)
    .filter(([, value]) => (value as number) > 0)
    .map(([key, value]) => ({
      name: key,
      value: value as number,
      color: SEVERITY_COLORS[key as keyof typeof SEVERITY_COLORS],
    }));

  // Prepare trend chart data (last 7 days)
  const trendData = vulnTrends.slice(-7).map((t: { date: string; critical: number; high: number; medium: number }) => ({
    date: new Date(t.date).toLocaleDateString('en', { weekday: 'short' }),
    critical: t.critical,
    high: t.high,
    medium: t.medium,
  }));

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Dashboard
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Overview of your security posture
        </p>
      </div>

      {/* Stats cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total Assets"
          value={stats?.total_assets || 0}
          subtitle={`${stats?.active_assets || 0} active`}
          icon={Server}
          color="blue"
        />
        <StatCard
          title="Open Vulnerabilities"
          value={stats?.open_vulnerabilities || 0}
          subtitle={`${stats?.critical_vulnerabilities || 0} critical`}
          icon={Shield}
          color="red"
        />
        <StatCard
          title="Completed Scans"
          value={stats?.completed_scans || 0}
          subtitle={`${stats?.running_scans || 0} running`}
          icon={Scan}
          color="green"
        />
        <StatCard
          title="Average Score"
          value={stats?.average_score ? `${stats.average_score}%` : 'N/A'}
          subtitle="From completed scans"
          icon={TrendingUp}
          color="purple"
        />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Vulnerability trend */}
        <div className="card">
          <h2 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">
            Vulnerability Trend (7 days)
          </h2>
          <div className="h-64">
            {trendData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={trendData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Line
                    type="monotone"
                    dataKey="critical"
                    stroke={SEVERITY_COLORS.critical}
                    strokeWidth={2}
                  />
                  <Line
                    type="monotone"
                    dataKey="high"
                    stroke={SEVERITY_COLORS.high}
                    strokeWidth={2}
                  />
                  <Line
                    type="monotone"
                    dataKey="medium"
                    stroke={SEVERITY_COLORS.medium}
                    strokeWidth={2}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-full items-center justify-center text-gray-500">
                No data available
              </div>
            )}
          </div>
        </div>

        {/* Vulnerability by severity */}
        <div className="card">
          <h2 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">
            Vulnerabilities by Severity
          </h2>
          <div className="h-64">
            {pieData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    dataKey="value"
                    label={({ name, value }) => `${name}: ${value}`}
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-full items-center justify-center text-gray-500">
                No vulnerabilities found
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Recent scans */}
      <div className="card">
        <h2 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">
          Recent Scans
        </h2>
        {recentScans.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700">
                  <th className="pb-3 text-left text-sm font-medium text-gray-500 dark:text-gray-400">
                    Name
                  </th>
                  <th className="pb-3 text-left text-sm font-medium text-gray-500 dark:text-gray-400">
                    Status
                  </th>
                  <th className="pb-3 text-left text-sm font-medium text-gray-500 dark:text-gray-400">
                    Grade
                  </th>
                  <th className="pb-3 text-left text-sm font-medium text-gray-500 dark:text-gray-400">
                    Score
                  </th>
                  <th className="pb-3 text-left text-sm font-medium text-gray-500 dark:text-gray-400">
                    Date
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {recentScans.map((scan: { id: string; name: string; status: string; grade: string; score: number; created_at: string }) => (
                  <tr key={scan.id}>
                    <td className="py-3 text-sm text-gray-900 dark:text-white">
                      {scan.name}
                    </td>
                    <td className="py-3">
                      <StatusBadge status={scan.status} />
                    </td>
                    <td className="py-3">
                      <GradeBadge grade={scan.grade} />
                    </td>
                    <td className="py-3 text-sm text-gray-900 dark:text-white">
                      {scan.score ? `${scan.score}%` : '-'}
                    </td>
                    <td className="py-3 text-sm text-gray-500 dark:text-gray-400">
                      {new Date(scan.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="py-8 text-center text-gray-500">
            <Activity className="mx-auto mb-2 h-8 w-8" />
            <p>No scans yet</p>
          </div>
        )}
      </div>
    </div>
  );
}

// Stat card component
function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  color,
}: {
  title: string;
  value: string | number;
  subtitle: string;
  icon: React.ElementType;
  color: 'blue' | 'red' | 'green' | 'purple';
}) {
  const colors = {
    blue: 'bg-blue-100 text-blue-600 dark:bg-blue-900 dark:text-blue-400',
    red: 'bg-red-100 text-red-600 dark:bg-red-900 dark:text-red-400',
    green: 'bg-green-100 text-green-600 dark:bg-green-900 dark:text-green-400',
    purple:
      'bg-purple-100 text-purple-600 dark:bg-purple-900 dark:text-purple-400',
  };

  return (
    <div className="card">
      <div className="flex items-center gap-4">
        <div className={`rounded-lg p-3 ${colors[color]}`}>
          <Icon className="h-6 w-6" />
        </div>
        <div>
          <p className="text-sm text-gray-500 dark:text-gray-400">{title}</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">
            {value}
          </p>
          <p className="text-xs text-gray-500 dark:text-gray-400">{subtitle}</p>
        </div>
      </div>
    </div>
  );
}

// Status badge
function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    completed: 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300',
    running: 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300',
    pending: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300',
    failed: 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300',
  };

  return (
    <span className={`badge ${styles[status] || styles.pending}`}>
      {status}
    </span>
  );
}

// Grade badge
function GradeBadge({ grade }: { grade: string | null }) {
  if (!grade) return <span className="text-gray-400">-</span>;

  const styles: Record<string, string> = {
    A: 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300',
    B: 'bg-lime-100 text-lime-700 dark:bg-lime-900 dark:text-lime-300',
    C: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300',
    D: 'bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-300',
    F: 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300',
  };

  return (
    <span className={`badge ${styles[grade] || ''}`}>
      {grade}
    </span>
  );
}
