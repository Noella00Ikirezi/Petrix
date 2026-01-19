import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Plus,
  Search,
  Scan,
  Play,
  Square,
  Trash2,
  Clock,
  CheckCircle,
  XCircle,
  Loader2,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { scansApi } from '@/api/client';

export default function ScansPage() {
  const [search, setSearch] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['scans'],
    queryFn: () => scansApi.list(),
    refetchInterval: 5000, // Refresh every 5s for running scans
  });

  const startMutation = useMutation({
    mutationFn: scansApi.start,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scans'] });
      toast.success('Scan started');
    },
    onError: () => toast.error('Failed to start scan'),
  });

  const cancelMutation = useMutation({
    mutationFn: scansApi.cancel,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scans'] });
      toast.success('Scan cancelled');
    },
    onError: () => toast.error('Failed to cancel scan'),
  });

  const deleteMutation = useMutation({
    mutationFn: scansApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scans'] });
      toast.success('Scan deleted');
    },
    onError: () => toast.error('Failed to delete scan'),
  });

  const scans = data?.items || [];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Scans
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Run security scans on your infrastructure
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="btn btn-primary btn-md"
        >
          <Plus className="mr-2 h-4 w-4" />
          New Scan
        </button>
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
        <input
          type="text"
          placeholder="Search scans..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="input pl-10"
        />
      </div>

      {/* Scans list */}
      <div className="space-y-4">
        {isLoading ? (
          <div className="flex h-64 items-center justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-500 border-t-transparent" />
          </div>
        ) : scans.length === 0 ? (
          <div className="card flex h-64 flex-col items-center justify-center text-gray-500">
            <Scan className="mb-2 h-12 w-12" />
            <p>No scans yet</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="btn btn-primary btn-sm mt-4"
            >
              Create your first scan
            </button>
          </div>
        ) : (
          scans
            .filter((s: ScanItem) =>
              s.name.toLowerCase().includes(search.toLowerCase())
            )
            .map((scan: ScanItem) => (
              <ScanCard
                key={scan.id}
                scan={scan}
                onStart={() => startMutation.mutate(scan.id)}
                onCancel={() => cancelMutation.mutate(scan.id)}
                onDelete={() => {
                  if (confirm('Delete this scan?')) {
                    deleteMutation.mutate(scan.id);
                  }
                }}
              />
            ))
        )}
      </div>

      {/* Create modal */}
      {showCreateModal && (
        <CreateScanModal onClose={() => setShowCreateModal(false)} />
      )}
    </div>
  );
}

interface ScanItem {
  id: string;
  name: string;
  scan_type: string;
  status: string;
  progress: number;
  grade: string | null;
  score: number | null;
  findings_summary: {
    critical: number;
    high: number;
    medium: number;
    low: number;
    info: number;
  };
  current_phase: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  duration_seconds: number | null;
}

function ScanCard({
  scan,
  onStart,
  onCancel,
  onDelete,
}: {
  scan: ScanItem;
  onStart: () => void;
  onCancel: () => void;
  onDelete: () => void;
}) {
  const isRunning = scan.status === 'running';
  const isPending = scan.status === 'pending';
  const isCompleted = scan.status === 'completed';
  const isFailed = scan.status === 'failed';

  return (
    <div className="card">
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-4">
          <div
            className={`rounded-lg p-3 ${
              isCompleted
                ? 'bg-green-100 text-green-600 dark:bg-green-900 dark:text-green-400'
                : isRunning
                ? 'bg-blue-100 text-blue-600 dark:bg-blue-900 dark:text-blue-400'
                : isFailed
                ? 'bg-red-100 text-red-600 dark:bg-red-900 dark:text-red-400'
                : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400'
            }`}
          >
            {isRunning ? (
              <Loader2 className="h-6 w-6 animate-spin" />
            ) : isCompleted ? (
              <CheckCircle className="h-6 w-6" />
            ) : isFailed ? (
              <XCircle className="h-6 w-6" />
            ) : (
              <Clock className="h-6 w-6" />
            )}
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 dark:text-white">
              {scan.name}
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              Type: {scan.scan_type} | Created:{' '}
              {new Date(scan.created_at).toLocaleString()}
            </p>
            {isRunning && scan.current_phase && (
              <p className="mt-1 text-sm text-blue-600 dark:text-blue-400">
                Phase: {scan.current_phase}
              </p>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Grade badge */}
          {scan.grade && <GradeBadge grade={scan.grade} />}

          {/* Status badge */}
          <StatusBadge status={scan.status} />

          {/* Actions */}
          {isPending && (
            <button
              onClick={onStart}
              className="btn btn-primary btn-sm"
              title="Start scan"
            >
              <Play className="h-4 w-4" />
            </button>
          )}
          {isRunning && (
            <button
              onClick={onCancel}
              className="btn btn-secondary btn-sm"
              title="Cancel scan"
            >
              <Square className="h-4 w-4" />
            </button>
          )}
          {!isRunning && (
            <button
              onClick={onDelete}
              className="btn btn-secondary btn-sm text-red-600 hover:bg-red-100 dark:text-red-400 dark:hover:bg-red-900"
              title="Delete scan"
            >
              <Trash2 className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>

      {/* Progress bar for running scans */}
      {isRunning && (
        <div className="mt-4">
          <div className="mb-1 flex justify-between text-sm">
            <span className="text-gray-600 dark:text-gray-400">Progress</span>
            <span className="text-gray-900 dark:text-white">{scan.progress}%</span>
          </div>
          <div className="h-2 w-full rounded-full bg-gray-200 dark:bg-gray-700">
            <div
              className="h-2 rounded-full bg-primary-600 transition-all"
              style={{ width: `${scan.progress}%` }}
            />
          </div>
        </div>
      )}

      {/* Results for completed scans */}
      {isCompleted && scan.findings_summary && (
        <div className="mt-4 flex gap-4">
          <FindingCount
            label="Critical"
            count={scan.findings_summary.critical}
            color="red"
          />
          <FindingCount
            label="High"
            count={scan.findings_summary.high}
            color="orange"
          />
          <FindingCount
            label="Medium"
            count={scan.findings_summary.medium}
            color="yellow"
          />
          <FindingCount
            label="Low"
            count={scan.findings_summary.low}
            color="green"
          />
        </div>
      )}
    </div>
  );
}

function FindingCount({
  label,
  count,
  color,
}: {
  label: string;
  count: number;
  color: 'red' | 'orange' | 'yellow' | 'green';
}) {
  const colors = {
    red: 'text-red-600 dark:text-red-400',
    orange: 'text-orange-600 dark:text-orange-400',
    yellow: 'text-yellow-600 dark:text-yellow-400',
    green: 'text-green-600 dark:text-green-400',
  };

  return (
    <div className="text-center">
      <div className={`text-2xl font-bold ${colors[color]}`}>{count}</div>
      <div className="text-xs text-gray-500 dark:text-gray-400">{label}</div>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    completed: 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300',
    running: 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300',
    pending: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-300',
    failed: 'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300',
    cancelled: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300',
  };

  return <span className={`badge ${styles[status] || ''}`}>{status}</span>;
}

function GradeBadge({ grade }: { grade: string }) {
  const styles: Record<string, string> = {
    A: 'bg-green-500 text-white',
    B: 'bg-lime-500 text-white',
    C: 'bg-yellow-500 text-white',
    D: 'bg-orange-500 text-white',
    F: 'bg-red-500 text-white',
  };

  return (
    <span className={`badge text-lg font-bold ${styles[grade] || ''}`}>
      {grade}
    </span>
  );
}

function CreateScanModal({ onClose }: { onClose: () => void }) {
  const [formData, setFormData] = useState({
    name: '',
    scan_type: 'discovery',
    target: '',
  });
  const queryClient = useQueryClient();

  const createMutation = useMutation({
    mutationFn: scansApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['scans'] });
      toast.success('Scan created');
      onClose();
    },
    onError: () => toast.error('Failed to create scan'),
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    createMutation.mutate({
      name: formData.name,
      scan_type: formData.scan_type,
      targets: [{ type: 'ip', value: formData.target }],
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-lg bg-white p-6 dark:bg-gray-800">
        <h2 className="mb-4 text-xl font-bold text-gray-900 dark:text-white">
          Create New Scan
        </h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="label">Scan Name</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="input mt-1"
              placeholder="My Security Scan"
              required
            />
          </div>
          <div>
            <label className="label">Scan Type</label>
            <select
              value={formData.scan_type}
              onChange={(e) =>
                setFormData({ ...formData, scan_type: e.target.value })
              }
              className="input mt-1"
            >
              <option value="discovery">Discovery</option>
              <option value="vulnerability">Vulnerability</option>
              <option value="compliance">Compliance</option>
              <option value="full">Full Audit</option>
            </select>
          </div>
          <div>
            <label className="label">Target (IP or Hostname)</label>
            <input
              type="text"
              value={formData.target}
              onChange={(e) => setFormData({ ...formData, target: e.target.value })}
              className="input mt-1"
              placeholder="192.168.1.1 or server.example.com"
              required
            />
          </div>
          <div className="flex justify-end gap-3 pt-4">
            <button type="button" onClick={onClose} className="btn btn-secondary btn-md">
              Cancel
            </button>
            <button
              type="submit"
              disabled={createMutation.isPending}
              className="btn btn-primary btn-md"
            >
              {createMutation.isPending ? 'Creating...' : 'Create Scan'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
