import { useState, useEffect } from 'react';
import { useAuthStore } from '@/stores/authStore';
import { apiClient } from '@/api/client';

interface LicenseInfo {
  license_id: string;
  organization: string;
  tier: string;
  issued_at: string;
  expires_at: string;
  is_valid: boolean;
  days_remaining: number;
  features: {
    max_assets: number;
    max_users: number;
    max_scans_per_month: number;
    compliance_modules: boolean;
    ai_assistant: boolean;
    api_access: boolean;
    custom_reports: boolean;
    sso_integration: boolean;
    priority_support: boolean;
  };
}

interface SystemStats {
  total_assets: number;
  total_users: number;
  scans_this_month: number;
  license_limits: {
    max_assets: number;
    max_users: number;
    max_scans_per_month: number;
  };
  within_limits: boolean;
}

interface UpdateInfo {
  current_version: string;
  latest_version: string;
  update_available: boolean;
  release_notes?: string;
  is_security_update: boolean;
}

export default function Settings() {
  const { user } = useAuthStore();
  const [activeTab, setActiveTab] = useState<'general' | 'license' | 'updates'>('general');
  const [license, setLicense] = useState<LicenseInfo | null>(null);
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [updateInfo, setUpdateInfo] = useState<UpdateInfo | null>(null);
  const [licenseKey, setLicenseKey] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    if (activeTab === 'license') {
      fetchLicenseInfo();
      fetchStats();
    } else if (activeTab === 'updates') {
      fetchUpdateInfo();
    }
  }, [activeTab]);

  const fetchLicenseInfo = async () => {
    try {
      const response = await apiClient.get('/system/license/');
      setLicense(response.data);
    } catch (err) {
      console.error('Failed to fetch license:', err);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await apiClient.get('/system/stats/');
      setStats(response.data);
    } catch (err) {
      console.error('Failed to fetch stats:', err);
    }
  };

  const fetchUpdateInfo = async () => {
    try {
      const response = await apiClient.get('/system/updates/');
      setUpdateInfo(response.data);
    } catch (err) {
      console.error('Failed to fetch updates:', err);
    }
  };

  const activateLicense = async () => {
    setLoading(true);
    setError('');
    setSuccess('');

    try {
      const response = await apiClient.post('/system/license/activate/', {
        license_key: licenseKey,
      });
      setLicense(response.data);
      setSuccess('License activated successfully!');
      setLicenseKey('');
    } catch (err: unknown) {
      const error = err as { response?: { data?: { detail?: string } } };
      setError(error.response?.data?.detail || 'Failed to activate license');
    } finally {
      setLoading(false);
    }
  };

  const getTierColor = (tier: string) => {
    switch (tier) {
      case 'enterprise':
        return 'bg-purple-100 text-purple-800';
      case 'professional':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatLimit = (limit: number) => {
    return limit === -1 ? 'Unlimited' : limit.toString();
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600">Manage your GRC Platform settings</p>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('general')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'general'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            General
          </button>
          <button
            onClick={() => setActiveTab('license')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'license'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            License
          </button>
          <button
            onClick={() => setActiveTab('updates')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'updates'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            Updates
          </button>
        </nav>
      </div>

      {/* General Tab */}
      {activeTab === 'general' && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Account Information</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Email</label>
              <p className="mt-1 text-gray-900">{user?.email}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Name</label>
              <p className="mt-1 text-gray-900">{user?.full_name}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700">Role</label>
              <p className="mt-1">
                <span className="px-2 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800">
                  {user?.role}
                </span>
              </p>
            </div>
          </div>
        </div>
      )}

      {/* License Tab */}
      {activeTab === 'license' && (
        <div className="space-y-6">
          {/* Current License */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">Current License</h2>
            {license ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500">Organization</p>
                    <p className="font-medium">{license.organization}</p>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${getTierColor(license.tier)}`}>
                    {license.tier.charAt(0).toUpperCase() + license.tier.slice(1)}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-500">Status</p>
                    <p className={`font-medium ${license.is_valid ? 'text-green-600' : 'text-red-600'}`}>
                      {license.is_valid ? 'Active' : 'Expired'}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Days Remaining</p>
                    <p className={`font-medium ${license.days_remaining < 30 ? 'text-orange-600' : ''}`}>
                      {license.days_remaining}
                    </p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Issued</p>
                    <p className="font-medium">{new Date(license.issued_at).toLocaleDateString()}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Expires</p>
                    <p className="font-medium">{new Date(license.expires_at).toLocaleDateString()}</p>
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-gray-500">Loading license information...</p>
            )}
          </div>

          {/* Usage Stats */}
          {stats && (
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">Usage</h2>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>Assets</span>
                    <span>{stats.total_assets} / {formatLimit(stats.license_limits.max_assets)}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${
                        stats.license_limits.max_assets !== -1 &&
                        stats.total_assets >= stats.license_limits.max_assets
                          ? 'bg-red-600'
                          : 'bg-blue-600'
                      }`}
                      style={{
                        width: stats.license_limits.max_assets === -1
                          ? '10%'
                          : `${Math.min(100, (stats.total_assets / stats.license_limits.max_assets) * 100)}%`
                      }}
                    />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>Users</span>
                    <span>{stats.total_users} / {formatLimit(stats.license_limits.max_users)}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${
                        stats.license_limits.max_users !== -1 &&
                        stats.total_users >= stats.license_limits.max_users
                          ? 'bg-red-600'
                          : 'bg-green-600'
                      }`}
                      style={{
                        width: stats.license_limits.max_users === -1
                          ? '10%'
                          : `${Math.min(100, (stats.total_users / stats.license_limits.max_users) * 100)}%`
                      }}
                    />
                  </div>
                </div>

                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>Scans this month</span>
                    <span>{stats.scans_this_month} / {formatLimit(stats.license_limits.max_scans_per_month)}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${
                        stats.license_limits.max_scans_per_month !== -1 &&
                        stats.scans_this_month >= stats.license_limits.max_scans_per_month
                          ? 'bg-red-600'
                          : 'bg-purple-600'
                      }`}
                      style={{
                        width: stats.license_limits.max_scans_per_month === -1
                          ? '10%'
                          : `${Math.min(100, (stats.scans_this_month / stats.license_limits.max_scans_per_month) * 100)}%`
                      }}
                    />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Features */}
          {license && (
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">Features</h2>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {Object.entries(license.features).map(([key, value]) => {
                  if (typeof value === 'boolean') {
                    return (
                      <div key={key} className="flex items-center gap-2">
                        {value ? (
                          <svg className="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                          </svg>
                        ) : (
                          <svg className="w-5 h-5 text-gray-300" fill="currentColor" viewBox="0 0 20 20">
                            <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                          </svg>
                        )}
                        <span className={`text-sm ${value ? 'text-gray-900' : 'text-gray-400'}`}>
                          {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </span>
                      </div>
                    );
                  }
                  return null;
                })}
              </div>
            </div>
          )}

          {/* Activate License */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-4">Activate License</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  License Key
                </label>
                <input
                  type="text"
                  value={licenseKey}
                  onChange={(e) => setLicenseKey(e.target.value)}
                  placeholder="GRC-XXXX-XXXXXXXXXXXXX..."
                  className="w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              {error && <p className="text-red-600 text-sm">{error}</p>}
              {success && <p className="text-green-600 text-sm">{success}</p>}
              <button
                onClick={activateLicense}
                disabled={loading || !licenseKey}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Activating...' : 'Activate License'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Updates Tab */}
      {activeTab === 'updates' && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Software Updates</h2>
          {updateInfo ? (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-500">Current Version</p>
                  <p className="font-medium">{updateInfo.current_version}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Latest Version</p>
                  <p className="font-medium">{updateInfo.latest_version}</p>
                </div>
              </div>

              {updateInfo.update_available ? (
                <div className={`p-4 rounded-lg ${updateInfo.is_security_update ? 'bg-red-50 border border-red-200' : 'bg-blue-50 border border-blue-200'}`}>
                  <div className="flex items-center gap-2">
                    {updateInfo.is_security_update && (
                      <svg className="w-5 h-5 text-red-600" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                      </svg>
                    )}
                    <p className={`font-medium ${updateInfo.is_security_update ? 'text-red-800' : 'text-blue-800'}`}>
                      {updateInfo.is_security_update ? 'Security Update Available!' : 'Update Available'}
                    </p>
                  </div>
                  {updateInfo.release_notes && (
                    <p className="mt-2 text-sm text-gray-700">{updateInfo.release_notes}</p>
                  )}
                  <p className="mt-3 text-sm text-gray-600">
                    To update, run: <code className="bg-gray-100 px-2 py-1 rounded">grc update</code>
                  </p>
                </div>
              ) : (
                <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                  <div className="flex items-center gap-2">
                    <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                    <p className="font-medium text-green-800">You're up to date!</p>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <p className="text-gray-500">Checking for updates...</p>
          )}
        </div>
      )}
    </div>
  );
}
