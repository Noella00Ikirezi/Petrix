import { useState, useEffect } from 'react';
import { useAuthStore } from '@/stores/authStore';
import {
  Users,
  Plus,
  Search,
  Shield,
  ShieldCheck,
  ShieldAlert,
  Eye,
  Edit,
  Trash2,
  MoreVertical,
  UserCheck,
  UserX,
  Key,
  ChevronDown,
  X,
  Check,
  AlertTriangle,
} from 'lucide-react';
import toast from 'react-hot-toast';

interface User {
  id: string;
  email: string;
  first_name: string | null;
  last_name: string | null;
  role: string;
  is_active: boolean;
  last_login: string | null;
  created_at: string | null;
  permissions: string[];
}

interface Role {
  name: string;
  value: string;
  description: string;
  permissions: string[];
  user_count: number;
}

interface UserStats {
  total_users: number;
  active_users: number;
  inactive_users: number;
  users_by_role: Record<string, number>;
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const roleColors: Record<string, string> = {
  admin: 'bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-300',
  auditor: 'bg-purple-100 text-purple-800 dark:bg-purple-900/50 dark:text-purple-300',
  analyst: 'bg-blue-100 text-blue-800 dark:bg-blue-900/50 dark:text-blue-300',
  viewer: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
};

const roleIcons: Record<string, React.ReactNode> = {
  admin: <ShieldAlert className="h-4 w-4" />,
  auditor: <ShieldCheck className="h-4 w-4" />,
  analyst: <Shield className="h-4 w-4" />,
  viewer: <Eye className="h-4 w-4" />,
};

export default function UsersPage() {
  const { token, user: currentUser } = useAuthStore();
  const [users, setUsers] = useState<User[]>([]);
  const [roles, setRoles] = useState<Role[]>([]);
  const [stats, setStats] = useState<UserStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [roleFilter, setRoleFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showRoleModal, setShowRoleModal] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [showResetPasswordModal, setShowResetPasswordModal] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [openDropdown, setOpenDropdown] = useState<string | null>(null);

  const isAdmin = currentUser?.role === 'admin';

  // Fetch data
  useEffect(() => {
    fetchData();
  }, [token]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const headers = { Authorization: `Bearer ${token}` };

      const [usersRes, rolesRes, statsRes] = await Promise.all([
        fetch(`${API_URL}/api/v1/users/`, { headers }),
        fetch(`${API_URL}/api/v1/users/roles`, { headers }),
        fetch(`${API_URL}/api/v1/users/stats`, { headers }),
      ]);

      if (usersRes.ok) setUsers(await usersRes.json());
      if (rolesRes.ok) setRoles(await rolesRes.json());
      if (statsRes.ok) setStats(await statsRes.json());
    } catch (error) {
      toast.error('Failed to load users');
    } finally {
      setLoading(false);
    }
  };

  // Filter users
  const filteredUsers = users.filter((user) => {
    const matchesSearch =
      user.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (user.first_name?.toLowerCase() || '').includes(searchTerm.toLowerCase()) ||
      (user.last_name?.toLowerCase() || '').includes(searchTerm.toLowerCase());

    const matchesRole = !roleFilter || user.role === roleFilter;
    const matchesStatus =
      !statusFilter ||
      (statusFilter === 'active' && user.is_active) ||
      (statusFilter === 'inactive' && !user.is_active);

    return matchesSearch && matchesRole && matchesStatus;
  });

  // Actions
  const handleActivate = async (user: User) => {
    try {
      const res = await fetch(`${API_URL}/api/v1/users/${user.id}/activate`, {
        method: 'PATCH',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        toast.success('User activated');
        fetchData();
      } else {
        const data = await res.json();
        toast.error(data.detail || 'Failed to activate user');
      }
    } catch {
      toast.error('Failed to activate user');
    }
    setOpenDropdown(null);
  };

  const handleDeactivate = async (user: User) => {
    try {
      const res = await fetch(`${API_URL}/api/v1/users/${user.id}/deactivate`, {
        method: 'PATCH',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        toast.success('User deactivated');
        fetchData();
      } else {
        const data = await res.json();
        toast.error(data.detail || 'Failed to deactivate user');
      }
    } catch {
      toast.error('Failed to deactivate user');
    }
    setOpenDropdown(null);
  };

  const handleDelete = async () => {
    if (!selectedUser) return;
    try {
      const res = await fetch(`${API_URL}/api/v1/users/${selectedUser.id}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        toast.success('User deleted');
        fetchData();
        setShowDeleteModal(false);
        setSelectedUser(null);
      } else {
        const data = await res.json();
        toast.error(data.detail || 'Failed to delete user');
      }
    } catch {
      toast.error('Failed to delete user');
    }
  };

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary-600 border-t-transparent" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            User Management
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Manage users, roles, and permissions
          </p>
        </div>
        {isAdmin && (
          <button
            onClick={() => setShowCreateModal(true)}
            className="btn btn-primary btn-md flex items-center gap-2"
          >
            <Plus className="h-4 w-4" />
            Add User
          </button>
        )}
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <StatCard
            title="Total Users"
            value={stats.total_users}
            icon={<Users className="h-6 w-6 text-primary-600" />}
          />
          <StatCard
            title="Active Users"
            value={stats.active_users}
            icon={<UserCheck className="h-6 w-6 text-green-600" />}
            color="text-green-600"
          />
          <StatCard
            title="Inactive Users"
            value={stats.inactive_users}
            icon={<UserX className="h-6 w-6 text-red-600" />}
            color="text-red-600"
          />
          <StatCard
            title="Administrators"
            value={stats.users_by_role.admin || 0}
            icon={<ShieldAlert className="h-6 w-6 text-purple-600" />}
            color="text-purple-600"
          />
        </div>
      )}

      {/* Roles Overview */}
      <div className="card">
        <h2 className="mb-4 text-lg font-semibold text-gray-900 dark:text-white">
          Roles Overview
        </h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {roles.map((role) => (
            <div
              key={role.value}
              className="rounded-lg border border-gray-200 p-4 dark:border-gray-700"
            >
              <div className="flex items-center gap-2">
                <span className={`rounded-full p-2 ${roleColors[role.value]}`}>
                  {roleIcons[role.value]}
                </span>
                <div>
                  <h3 className="font-medium text-gray-900 dark:text-white capitalize">
                    {role.value}
                  </h3>
                  <p className="text-sm text-gray-500">{role.user_count} users</p>
                </div>
              </div>
              <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                {role.description}
              </p>
              <p className="mt-1 text-xs text-gray-400">
                {role.permissions.length} permissions
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="flex flex-wrap items-center gap-4">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Search users..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input pl-10"
            />
          </div>
          <select
            value={roleFilter}
            onChange={(e) => setRoleFilter(e.target.value)}
            className="input w-40"
          >
            <option value="">All Roles</option>
            {roles.map((role) => (
              <option key={role.value} value={role.value}>
                {role.name}
              </option>
            ))}
          </select>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="input w-40"
          >
            <option value="">All Status</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
          </select>
        </div>
      </div>

      {/* Users Table */}
      <div className="card overflow-hidden p-0">
        <table className="w-full">
          <thead className="bg-gray-50 dark:bg-gray-700">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-300">
                User
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-300">
                Role
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-300">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-300">
                Last Login
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium uppercase tracking-wider text-gray-500 dark:text-gray-300">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
            {filteredUsers.map((user) => (
              <tr key={user.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                <td className="whitespace-nowrap px-6 py-4">
                  <div className="flex items-center">
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary-100 dark:bg-primary-900">
                      <span className="text-sm font-medium text-primary-700 dark:text-primary-300">
                        {(user.first_name?.[0] || user.email[0]).toUpperCase()}
                      </span>
                    </div>
                    <div className="ml-4">
                      <div className="font-medium text-gray-900 dark:text-white">
                        {user.first_name} {user.last_name}
                      </div>
                      <div className="text-sm text-gray-500">{user.email}</div>
                    </div>
                  </div>
                </td>
                <td className="whitespace-nowrap px-6 py-4">
                  <span
                    className={`inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium ${
                      roleColors[user.role]
                    }`}
                  >
                    {roleIcons[user.role]}
                    <span className="capitalize">{user.role}</span>
                  </span>
                </td>
                <td className="whitespace-nowrap px-6 py-4">
                  <span
                    className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${
                      user.is_active
                        ? 'bg-green-100 text-green-800 dark:bg-green-900/50 dark:text-green-300'
                        : 'bg-red-100 text-red-800 dark:bg-red-900/50 dark:text-red-300'
                    }`}
                  >
                    {user.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-500">
                  {user.last_login
                    ? new Date(user.last_login).toLocaleDateString()
                    : 'Never'}
                </td>
                <td className="whitespace-nowrap px-6 py-4 text-right">
                  <div className="relative">
                    <button
                      onClick={() =>
                        setOpenDropdown(openDropdown === user.id ? null : user.id)
                      }
                      className="rounded p-1 hover:bg-gray-100 dark:hover:bg-gray-700"
                    >
                      <MoreVertical className="h-5 w-5 text-gray-500" />
                    </button>
                    {openDropdown === user.id && (
                      <div className="absolute right-0 z-10 mt-1 w-48 rounded-md border border-gray-200 bg-white py-1 shadow-lg dark:border-gray-700 dark:bg-gray-800">
                        <button
                          onClick={() => {
                            setSelectedUser(user);
                            setShowEditModal(true);
                            setOpenDropdown(null);
                          }}
                          className="flex w-full items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
                        >
                          <Edit className="h-4 w-4" />
                          Edit User
                        </button>
                        {isAdmin && (
                          <button
                            onClick={() => {
                              setSelectedUser(user);
                              setShowRoleModal(true);
                              setOpenDropdown(null);
                            }}
                            className="flex w-full items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
                          >
                            <Shield className="h-4 w-4" />
                            Change Role
                          </button>
                        )}
                        {isAdmin && (
                          <button
                            onClick={() => {
                              setSelectedUser(user);
                              setShowResetPasswordModal(true);
                              setOpenDropdown(null);
                            }}
                            className="flex w-full items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 dark:text-gray-300 dark:hover:bg-gray-700"
                          >
                            <Key className="h-4 w-4" />
                            Reset Password
                          </button>
                        )}
                        {user.is_active ? (
                          <button
                            onClick={() => handleDeactivate(user)}
                            className="flex w-full items-center gap-2 px-4 py-2 text-sm text-orange-600 hover:bg-gray-100 dark:hover:bg-gray-700"
                          >
                            <UserX className="h-4 w-4" />
                            Deactivate
                          </button>
                        ) : (
                          <button
                            onClick={() => handleActivate(user)}
                            className="flex w-full items-center gap-2 px-4 py-2 text-sm text-green-600 hover:bg-gray-100 dark:hover:bg-gray-700"
                          >
                            <UserCheck className="h-4 w-4" />
                            Activate
                          </button>
                        )}
                        {isAdmin && user.id !== currentUser?.id && (
                          <button
                            onClick={() => {
                              setSelectedUser(user);
                              setShowDeleteModal(true);
                              setOpenDropdown(null);
                            }}
                            className="flex w-full items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-gray-100 dark:hover:bg-gray-700"
                          >
                            <Trash2 className="h-4 w-4" />
                            Delete
                          </button>
                        )}
                      </div>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {filteredUsers.length === 0 && (
          <div className="py-12 text-center text-gray-500">No users found</div>
        )}
      </div>

      {/* Create User Modal */}
      {showCreateModal && (
        <CreateUserModal
          token={token!}
          roles={roles}
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => {
            setShowCreateModal(false);
            fetchData();
          }}
        />
      )}

      {/* Edit User Modal */}
      {showEditModal && selectedUser && (
        <EditUserModal
          token={token!}
          user={selectedUser}
          onClose={() => {
            setShowEditModal(false);
            setSelectedUser(null);
          }}
          onSuccess={() => {
            setShowEditModal(false);
            setSelectedUser(null);
            fetchData();
          }}
        />
      )}

      {/* Change Role Modal */}
      {showRoleModal && selectedUser && (
        <ChangeRoleModal
          token={token!}
          user={selectedUser}
          roles={roles}
          onClose={() => {
            setShowRoleModal(false);
            setSelectedUser(null);
          }}
          onSuccess={() => {
            setShowRoleModal(false);
            setSelectedUser(null);
            fetchData();
          }}
        />
      )}

      {/* Reset Password Modal */}
      {showResetPasswordModal && selectedUser && (
        <ResetPasswordModal
          token={token!}
          user={selectedUser}
          onClose={() => {
            setShowResetPasswordModal(false);
            setSelectedUser(null);
          }}
          onSuccess={() => {
            setShowResetPasswordModal(false);
            setSelectedUser(null);
          }}
        />
      )}

      {/* Delete Confirmation Modal */}
      {showDeleteModal && selectedUser && (
        <DeleteConfirmModal
          user={selectedUser}
          onClose={() => {
            setShowDeleteModal(false);
            setSelectedUser(null);
          }}
          onConfirm={handleDelete}
        />
      )}
    </div>
  );
}

// Stat Card Component
function StatCard({
  title,
  value,
  icon,
  color = 'text-gray-900',
}: {
  title: string;
  value: number;
  icon: React.ReactNode;
  color?: string;
}) {
  return (
    <div className="card flex items-center gap-4">
      <div className="rounded-lg bg-gray-100 p-3 dark:bg-gray-700">{icon}</div>
      <div>
        <p className="text-sm text-gray-500 dark:text-gray-400">{title}</p>
        <p className={`text-2xl font-bold ${color} dark:text-white`}>{value}</p>
      </div>
    </div>
  );
}

// Create User Modal
function CreateUserModal({
  token,
  roles,
  onClose,
  onSuccess,
}: {
  token: string;
  roles: Role[];
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    first_name: '',
    last_name: '',
    role: 'viewer',
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.password !== formData.confirmPassword) {
      toast.error('Passwords do not match');
      return;
    }
    if (formData.password.length < 12) {
      toast.error('Password must be at least 12 characters');
      return;
    }

    try {
      setLoading(true);
      const res = await fetch(`${API_URL}/api/v1/users/`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: formData.email,
          password: formData.password,
          first_name: formData.first_name || null,
          last_name: formData.last_name || null,
          role: formData.role,
        }),
      });

      if (res.ok) {
        toast.success('User created successfully');
        onSuccess();
      } else {
        const data = await res.json();
        toast.error(data.detail || 'Failed to create user');
      }
    } catch {
      toast.error('Failed to create user');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal title="Create New User" onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">First Name</label>
            <input
              type="text"
              value={formData.first_name}
              onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
              className="input mt-1"
            />
          </div>
          <div>
            <label className="label">Last Name</label>
            <input
              type="text"
              value={formData.last_name}
              onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
              className="input mt-1"
            />
          </div>
        </div>
        <div>
          <label className="label">Email *</label>
          <input
            type="email"
            value={formData.email}
            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
            className="input mt-1"
            required
          />
        </div>
        <div>
          <label className="label">Password *</label>
          <input
            type="password"
            value={formData.password}
            onChange={(e) => setFormData({ ...formData, password: e.target.value })}
            className="input mt-1"
            required
            minLength={12}
          />
          <p className="mt-1 text-xs text-gray-500">
            Min 12 chars with uppercase, lowercase, digit, and special character
          </p>
        </div>
        <div>
          <label className="label">Confirm Password *</label>
          <input
            type="password"
            value={formData.confirmPassword}
            onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
            className="input mt-1"
            required
          />
        </div>
        <div>
          <label className="label">Role *</label>
          <select
            value={formData.role}
            onChange={(e) => setFormData({ ...formData, role: e.target.value })}
            className="input mt-1"
          >
            {roles.map((role) => (
              <option key={role.value} value={role.value}>
                {role.name} - {role.description}
              </option>
            ))}
          </select>
        </div>
        <div className="flex justify-end gap-3 pt-4">
          <button type="button" onClick={onClose} className="btn btn-secondary btn-md">
            Cancel
          </button>
          <button type="submit" disabled={loading} className="btn btn-primary btn-md">
            {loading ? 'Creating...' : 'Create User'}
          </button>
        </div>
      </form>
    </Modal>
  );
}

// Edit User Modal
function EditUserModal({
  token,
  user,
  onClose,
  onSuccess,
}: {
  token: string;
  user: User;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [formData, setFormData] = useState({
    first_name: user.first_name || '',
    last_name: user.last_name || '',
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      const res = await fetch(`${API_URL}/api/v1/users/${user.id}`, {
        method: 'PATCH',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          first_name: formData.first_name || null,
          last_name: formData.last_name || null,
        }),
      });

      if (res.ok) {
        toast.success('User updated');
        onSuccess();
      } else {
        const data = await res.json();
        toast.error(data.detail || 'Failed to update user');
      }
    } catch {
      toast.error('Failed to update user');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal title="Edit User" onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="label">Email</label>
          <input type="email" value={user.email} className="input mt-1" disabled />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="label">First Name</label>
            <input
              type="text"
              value={formData.first_name}
              onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
              className="input mt-1"
            />
          </div>
          <div>
            <label className="label">Last Name</label>
            <input
              type="text"
              value={formData.last_name}
              onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
              className="input mt-1"
            />
          </div>
        </div>
        <div className="flex justify-end gap-3 pt-4">
          <button type="button" onClick={onClose} className="btn btn-secondary btn-md">
            Cancel
          </button>
          <button type="submit" disabled={loading} className="btn btn-primary btn-md">
            {loading ? 'Saving...' : 'Save Changes'}
          </button>
        </div>
      </form>
    </Modal>
  );
}

// Change Role Modal
function ChangeRoleModal({
  token,
  user,
  roles,
  onClose,
  onSuccess,
}: {
  token: string;
  user: User;
  roles: Role[];
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [selectedRole, setSelectedRole] = useState(user.role);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (selectedRole === user.role) {
      onClose();
      return;
    }

    try {
      setLoading(true);
      const res = await fetch(`${API_URL}/api/v1/users/${user.id}/role?role=${selectedRole}`, {
        method: 'PATCH',
        headers: { Authorization: `Bearer ${token}` },
      });

      if (res.ok) {
        toast.success('Role updated');
        onSuccess();
      } else {
        const data = await res.json();
        toast.error(data.detail || 'Failed to update role');
      }
    } catch {
      toast.error('Failed to update role');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal title="Change User Role" onClose={onClose}>
      <div className="space-y-4">
        <p className="text-gray-600 dark:text-gray-400">
          Changing role for: <strong>{user.email}</strong>
        </p>
        <div className="space-y-2">
          {roles.map((role) => (
            <button
              key={role.value}
              onClick={() => setSelectedRole(role.value)}
              className={`flex w-full items-center gap-3 rounded-lg border p-4 transition-colors ${
                selectedRole === role.value
                  ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                  : 'border-gray-200 hover:border-gray-300 dark:border-gray-700'
              }`}
            >
              <span className={`rounded-full p-2 ${roleColors[role.value]}`}>
                {roleIcons[role.value]}
              </span>
              <div className="text-left">
                <div className="font-medium text-gray-900 dark:text-white capitalize">
                  {role.value}
                </div>
                <div className="text-sm text-gray-500">{role.description}</div>
              </div>
              {selectedRole === role.value && (
                <Check className="ml-auto h-5 w-5 text-primary-600" />
              )}
            </button>
          ))}
        </div>
        <div className="flex justify-end gap-3 pt-4">
          <button onClick={onClose} className="btn btn-secondary btn-md">
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={loading}
            className="btn btn-primary btn-md"
          >
            {loading ? 'Updating...' : 'Update Role'}
          </button>
        </div>
      </div>
    </Modal>
  );
}

// Reset Password Modal
function ResetPasswordModal({
  token,
  user,
  onClose,
  onSuccess,
}: {
  token: string;
  user: User;
  onClose: () => void;
  onSuccess: () => void;
}) {
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      toast.error('Passwords do not match');
      return;
    }
    if (password.length < 12) {
      toast.error('Password must be at least 12 characters');
      return;
    }

    try {
      setLoading(true);
      const res = await fetch(`${API_URL}/api/v1/users/${user.id}/reset-password`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ new_password: password }),
      });

      if (res.ok) {
        toast.success('Password reset successfully');
        onSuccess();
      } else {
        const data = await res.json();
        toast.error(data.detail || 'Failed to reset password');
      }
    } catch {
      toast.error('Failed to reset password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal title="Reset User Password" onClose={onClose}>
      <form onSubmit={handleSubmit} className="space-y-4">
        <p className="text-gray-600 dark:text-gray-400">
          Resetting password for: <strong>{user.email}</strong>
        </p>
        <div>
          <label className="label">New Password *</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="input mt-1"
            required
            minLength={12}
          />
          <p className="mt-1 text-xs text-gray-500">
            Min 12 chars with uppercase, lowercase, digit, and special character
          </p>
        </div>
        <div>
          <label className="label">Confirm Password *</label>
          <input
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            className="input mt-1"
            required
          />
        </div>
        <div className="flex justify-end gap-3 pt-4">
          <button type="button" onClick={onClose} className="btn btn-secondary btn-md">
            Cancel
          </button>
          <button type="submit" disabled={loading} className="btn btn-primary btn-md">
            {loading ? 'Resetting...' : 'Reset Password'}
          </button>
        </div>
      </form>
    </Modal>
  );
}

// Delete Confirmation Modal
function DeleteConfirmModal({
  user,
  onClose,
  onConfirm,
}: {
  user: User;
  onClose: () => void;
  onConfirm: () => void;
}) {
  return (
    <Modal title="Delete User" onClose={onClose}>
      <div className="space-y-4">
        <div className="flex items-center gap-3 rounded-lg bg-red-50 p-4 dark:bg-red-900/20">
          <AlertTriangle className="h-6 w-6 text-red-600" />
          <p className="text-red-800 dark:text-red-200">
            This action cannot be undone. The user will be permanently deleted.
          </p>
        </div>
        <p className="text-gray-600 dark:text-gray-400">
          Are you sure you want to delete <strong>{user.email}</strong>?
        </p>
        <div className="flex justify-end gap-3 pt-4">
          <button onClick={onClose} className="btn btn-secondary btn-md">
            Cancel
          </button>
          <button
            onClick={onConfirm}
            className="btn btn-md bg-red-600 text-white hover:bg-red-700"
          >
            Delete User
          </button>
        </div>
      </div>
    </Modal>
  );
}

// Modal Wrapper Component
function Modal({
  title,
  children,
  onClose,
}: {
  title: string;
  children: React.ReactNode;
  onClose: () => void;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl dark:bg-gray-800">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">{title}</h2>
          <button
            onClick={onClose}
            className="rounded p-1 hover:bg-gray-100 dark:hover:bg-gray-700"
          >
            <X className="h-5 w-5 text-gray-500" />
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
