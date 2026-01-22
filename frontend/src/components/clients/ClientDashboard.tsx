import { useQuery } from '@tanstack/react-query';
import {
  TrendingUp,
  TrendingDown,
  Minus,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Clock,
  FileText,
  Wrench,
  Shield,
  Target,
  Calendar,
  RefreshCw,
  ArrowUp,
  ArrowDown,
} from 'lucide-react';
import { api } from '../../api/client';

interface ClientDashboardProps {
  clientId: string;
}

interface AssessmentTrendPoint {
  assessment_id: string;
  assessment_name: string;
  date: string;
  compliance_score: number;
  compliant_count: number;
  partially_compliant_count: number;
  non_compliant_count: number;
  total_requirements: number;
}

interface CategoryScore {
  category: string;
  category_label: string;
  total: number;
  compliant: number;
  partially_compliant: number;
  non_compliant: number;
  not_assessed: number;
  score: number;
}

interface PriorityScore {
  priority: string;
  priority_label: string;
  total: number;
  compliant: number;
  non_compliant: number;
  score: number;
}

interface EvidenceStats {
  total_evidence: number;
  verified_evidence: number;
  pending_verification: number;
  expired_evidence: number;
  by_type: Record<string, number>;
}

interface DashboardData {
  client_id: string;
  client_name: string;
  client_code: string;
  total_requirements: number;
  current_compliance_score: number;
  previous_compliance_score: number | null;
  score_change: number | null;
  compliant_count: number;
  partially_compliant_count: number;
  non_compliant_count: number;
  not_assessed_count: number;
  not_applicable_count: number;
  total_actions: number;
  open_actions: number;
  overdue_actions: number;
  completed_actions: number;
  action_completion_rate: number;
  evidence_stats: EvidenceStats;
  assessment_trend: AssessmentTrendPoint[];
  by_category: CategoryScore[];
  by_priority: PriorityScore[];
  last_assessment_date: string | null;
  critical_non_compliant: number;
  high_priority_actions: number;
  days_since_last_assessment: number | null;
}

export function ClientDashboard({ clientId }: ClientDashboardProps) {
  const { data: dashboard, isLoading } = useQuery<DashboardData>({
    queryKey: ['client-dashboard', clientId],
    queryFn: async () => {
      const response = await api.get(`/clients/${clientId}/dashboard`);
      return response.data;
    },
    refetchInterval: 30000, // Refresh every 30 seconds
  });

  if (isLoading || !dashboard) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getScoreBgColor = (score: number) => {
    if (score >= 80) return 'bg-green-100';
    if (score >= 60) return 'bg-yellow-100';
    return 'bg-red-100';
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'bg-red-500';
      case 'high': return 'bg-orange-500';
      case 'medium': return 'bg-yellow-500';
      case 'low': return 'bg-green-500';
      default: return 'bg-gray-500';
    }
  };

  // Calculate max score for chart scaling
  const maxScore = Math.max(100, ...dashboard.assessment_trend.map(t => t.compliance_score));
  const chartHeight = 200;

  return (
    <div className="space-y-6">
      {/* Header with main score */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Score Card */}
        <div className={`rounded-xl p-6 ${getScoreBgColor(dashboard.current_compliance_score)}`}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Score de conformite</p>
              <p className={`text-5xl font-bold ${getScoreColor(dashboard.current_compliance_score)}`}>
                {dashboard.current_compliance_score.toFixed(1)}%
              </p>
              {dashboard.score_change !== null && (
                <div className="flex items-center gap-1 mt-2">
                  {dashboard.score_change > 0 ? (
                    <>
                      <ArrowUp className="w-4 h-4 text-green-600" />
                      <span className="text-sm text-green-600">+{dashboard.score_change.toFixed(1)}%</span>
                    </>
                  ) : dashboard.score_change < 0 ? (
                    <>
                      <ArrowDown className="w-4 h-4 text-red-600" />
                      <span className="text-sm text-red-600">{dashboard.score_change.toFixed(1)}%</span>
                    </>
                  ) : (
                    <>
                      <Minus className="w-4 h-4 text-gray-500" />
                      <span className="text-sm text-gray-500">Stable</span>
                    </>
                  )}
                  <span className="text-xs text-gray-500 ml-1">vs evaluation precedente</span>
                </div>
              )}
            </div>
            <div className={`p-4 rounded-full ${dashboard.current_compliance_score >= 80 ? 'bg-green-200' : dashboard.current_compliance_score >= 60 ? 'bg-yellow-200' : 'bg-red-200'}`}>
              <Target className={`w-8 h-8 ${getScoreColor(dashboard.current_compliance_score)}`} />
            </div>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h3 className="text-sm font-medium text-gray-600 mb-4">Repartition</h3>
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckCircle className="w-4 h-4 text-green-500" />
                <span className="text-sm">Conformes</span>
              </div>
              <span className="font-semibold text-green-600">{dashboard.compliant_count}</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-yellow-500" />
                <span className="text-sm">Partiels</span>
              </div>
              <span className="font-semibold text-yellow-600">{dashboard.partially_compliant_count}</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <XCircle className="w-4 h-4 text-red-500" />
                <span className="text-sm">Non-conformes</span>
              </div>
              <span className="font-semibold text-red-600">{dashboard.non_compliant_count}</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-gray-400" />
                <span className="text-sm">Non evalues</span>
              </div>
              <span className="font-semibold text-gray-500">{dashboard.not_assessed_count}</span>
            </div>
          </div>
        </div>

        {/* Key Alerts */}
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h3 className="text-sm font-medium text-gray-600 mb-4">Alertes cles</h3>
          <div className="space-y-3">
            {dashboard.critical_non_compliant > 0 && (
              <div className="flex items-center gap-3 p-3 bg-red-50 rounded-lg">
                <div className="p-2 bg-red-100 rounded">
                  <XCircle className="w-4 h-4 text-red-600" />
                </div>
                <div>
                  <p className="font-semibold text-red-700">{dashboard.critical_non_compliant}</p>
                  <p className="text-xs text-red-600">Non-conformites critiques</p>
                </div>
              </div>
            )}
            {dashboard.overdue_actions > 0 && (
              <div className="flex items-center gap-3 p-3 bg-orange-50 rounded-lg">
                <div className="p-2 bg-orange-100 rounded">
                  <Clock className="w-4 h-4 text-orange-600" />
                </div>
                <div>
                  <p className="font-semibold text-orange-700">{dashboard.overdue_actions}</p>
                  <p className="text-xs text-orange-600">Actions en retard</p>
                </div>
              </div>
            )}
            {dashboard.high_priority_actions > 0 && (
              <div className="flex items-center gap-3 p-3 bg-yellow-50 rounded-lg">
                <div className="p-2 bg-yellow-100 rounded">
                  <Wrench className="w-4 h-4 text-yellow-600" />
                </div>
                <div>
                  <p className="font-semibold text-yellow-700">{dashboard.high_priority_actions}</p>
                  <p className="text-xs text-yellow-600">Actions haute priorite</p>
                </div>
              </div>
            )}
            {dashboard.critical_non_compliant === 0 && dashboard.overdue_actions === 0 && (
              <div className="flex items-center gap-3 p-3 bg-green-50 rounded-lg">
                <div className="p-2 bg-green-100 rounded">
                  <CheckCircle className="w-4 h-4 text-green-600" />
                </div>
                <div>
                  <p className="font-semibold text-green-700">Tout va bien</p>
                  <p className="text-xs text-green-600">Aucune alerte critique</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Evolution Chart */}
      {dashboard.assessment_trend.length > 1 && (
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-blue-600" />
            Evolution du score de conformite
          </h3>
          <div className="relative" style={{ height: chartHeight + 60 }}>
            {/* Y-axis labels */}
            <div className="absolute left-0 top-0 bottom-10 w-12 flex flex-col justify-between text-xs text-gray-500">
              <span>100%</span>
              <span>75%</span>
              <span>50%</span>
              <span>25%</span>
              <span>0%</span>
            </div>

            {/* Chart area */}
            <div className="ml-14 mr-4 relative" style={{ height: chartHeight }}>
              {/* Grid lines */}
              <div className="absolute inset-0 flex flex-col justify-between">
                {[0, 1, 2, 3, 4].map(i => (
                  <div key={i} className="border-t border-gray-100 w-full" />
                ))}
              </div>

              {/* Bars */}
              <div className="absolute inset-0 flex items-end justify-around gap-2 px-2">
                {dashboard.assessment_trend.map((point, idx) => {
                  const height = (point.compliance_score / 100) * chartHeight;
                  const barColor = point.compliance_score >= 80 ? 'bg-green-500' :
                                   point.compliance_score >= 60 ? 'bg-yellow-500' : 'bg-red-500';

                  return (
                    <div key={point.assessment_id} className="flex flex-col items-center flex-1 max-w-20">
                      <div className="relative w-full flex justify-center">
                        <div
                          className={`${barColor} rounded-t transition-all duration-500 hover:opacity-80 cursor-pointer`}
                          style={{ height, width: '60%', minWidth: 20 }}
                          title={`${point.assessment_name}: ${point.compliance_score.toFixed(1)}%`}
                        >
                          <div className="absolute -top-6 left-1/2 transform -translate-x-1/2 text-xs font-semibold whitespace-nowrap">
                            {point.compliance_score.toFixed(0)}%
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* X-axis labels */}
            <div className="ml-14 mr-4 flex justify-around mt-2">
              {dashboard.assessment_trend.map((point) => (
                <div key={point.assessment_id} className="text-xs text-gray-500 text-center flex-1 max-w-20 truncate" title={point.assessment_name}>
                  {new Date(point.date).toLocaleDateString('fr-FR', { month: 'short', year: '2-digit' })}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Category and Priority Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* By Category */}
        {dashboard.by_category.length > 0 && (
          <div className="bg-white rounded-xl shadow-sm border p-6">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Shield className="w-5 h-5 text-purple-600" />
              Score par categorie
            </h3>
            <div className="space-y-4">
              {dashboard.by_category
                .sort((a, b) => a.score - b.score)
                .map((cat) => (
                <div key={cat.category}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium">{cat.category_label}</span>
                    <span className={`text-sm font-semibold ${getScoreColor(cat.score)}`}>
                      {cat.score.toFixed(0)}%
                    </span>
                  </div>
                  <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className={`h-full transition-all duration-500 ${
                        cat.score >= 80 ? 'bg-green-500' :
                        cat.score >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                      }`}
                      style={{ width: `${cat.score}%` }}
                    />
                  </div>
                  <div className="flex gap-4 mt-1 text-xs text-gray-500">
                    <span className="text-green-600">{cat.compliant} conf.</span>
                    <span className="text-yellow-600">{cat.partially_compliant} part.</span>
                    <span className="text-red-600">{cat.non_compliant} non-c.</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* By Priority */}
        {dashboard.by_priority.length > 0 && (
          <div className="bg-white rounded-xl shadow-sm border p-6">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <Target className="w-5 h-5 text-orange-600" />
              Score par priorite
            </h3>
            <div className="space-y-4">
              {['critical', 'high', 'medium', 'low'].map(pri => {
                const data = dashboard.by_priority.find(p => p.priority === pri);
                if (!data) return null;
                return (
                  <div key={pri}>
                    <div className="flex items-center justify-between mb-1">
                      <div className="flex items-center gap-2">
                        <div className={`w-3 h-3 rounded-full ${getPriorityColor(pri)}`} />
                        <span className="text-sm font-medium">{data.priority_label}</span>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-xs text-gray-500">{data.total} exig.</span>
                        <span className={`text-sm font-semibold ${getScoreColor(data.score)}`}>
                          {data.score.toFixed(0)}%
                        </span>
                      </div>
                    </div>
                    <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className={`h-full transition-all duration-500 ${
                          data.score >= 80 ? 'bg-green-500' :
                          data.score >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                        }`}
                        style={{ width: `${data.score}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* Actions & Evidence Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Actions Stats */}
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Wrench className="w-5 h-5 text-blue-600" />
            Actions de remediation
          </h3>
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div className="p-4 bg-blue-50 rounded-lg text-center">
              <p className="text-3xl font-bold text-blue-600">{dashboard.total_actions}</p>
              <p className="text-xs text-gray-600">Total actions</p>
            </div>
            <div className="p-4 bg-green-50 rounded-lg text-center">
              <p className="text-3xl font-bold text-green-600">{dashboard.action_completion_rate.toFixed(0)}%</p>
              <p className="text-xs text-gray-600">Taux completion</p>
            </div>
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
              <span className="text-sm">En cours</span>
              <span className="font-semibold text-blue-600">{dashboard.open_actions}</span>
            </div>
            <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
              <span className="text-sm">Terminees</span>
              <span className="font-semibold text-green-600">{dashboard.completed_actions}</span>
            </div>
            <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
              <span className="text-sm">En retard</span>
              <span className="font-semibold text-red-600">{dashboard.overdue_actions}</span>
            </div>
          </div>
        </div>

        {/* Evidence Stats */}
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <FileText className="w-5 h-5 text-purple-600" />
            Preuves documentees
          </h3>
          <div className="grid grid-cols-2 gap-4 mb-4">
            <div className="p-4 bg-purple-50 rounded-lg text-center">
              <p className="text-3xl font-bold text-purple-600">{dashboard.evidence_stats.total_evidence}</p>
              <p className="text-xs text-gray-600">Total preuves</p>
            </div>
            <div className="p-4 bg-green-50 rounded-lg text-center">
              <p className="text-3xl font-bold text-green-600">{dashboard.evidence_stats.verified_evidence}</p>
              <p className="text-xs text-gray-600">Verifiees</p>
            </div>
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
              <span className="text-sm">En attente verification</span>
              <span className="font-semibold text-yellow-600">{dashboard.evidence_stats.pending_verification}</span>
            </div>
            <div className="flex items-center justify-between p-2 bg-gray-50 rounded">
              <span className="text-sm">Expirees</span>
              <span className="font-semibold text-red-600">{dashboard.evidence_stats.expired_evidence}</span>
            </div>
          </div>
          {Object.keys(dashboard.evidence_stats.by_type).length > 0 && (
            <div className="mt-4 pt-4 border-t">
              <p className="text-xs text-gray-500 mb-2">Par type:</p>
              <div className="flex flex-wrap gap-2">
                {Object.entries(dashboard.evidence_stats.by_type).map(([type, count]) => (
                  <span key={type} className="px-2 py-1 bg-gray-100 rounded text-xs">
                    {type}: {count}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Last Assessment Info */}
      {dashboard.last_assessment_date && (
        <div className="bg-blue-50 rounded-xl p-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Calendar className="w-5 h-5 text-blue-600" />
            <div>
              <p className="text-sm font-medium text-blue-900">Derniere evaluation</p>
              <p className="text-xs text-blue-600">
                {new Date(dashboard.last_assessment_date).toLocaleDateString('fr-FR', {
                  day: 'numeric',
                  month: 'long',
                  year: 'numeric',
                })}
                {dashboard.days_since_last_assessment !== null && (
                  <span className="ml-2">
                    (il y a {dashboard.days_since_last_assessment} jour{dashboard.days_since_last_assessment > 1 ? 's' : ''})
                  </span>
                )}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
