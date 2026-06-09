import { useEffect, useState } from 'react'
import API from '../api/client'

export default function AdminDashboard() {
  const [users, setUsers] = useState([])
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState({ totalMeetings: 0, storageUsed: '45.2 MB' })
  const [error, setError] = useState('')
  const [info, setInfo] = useState('')

  function loadUsers() {
    setLoading(true)
    API.get('/api/auth/admin/users')
      .then(res => {
        setUsers(res.data.users || [])
        setLoading(false)
      })
      .catch(err => {
        setError('Failed to load user directories. Access Restricted.')
        setLoading(false)
      })
  }

  useEffect(() => {
    loadUsers()
    // Mock general system statistics
    API.get('/api/dashboard/stats')
      .then(res => {
        setStats(prev => ({ 
          ...prev, 
          totalMeetings: res.data.total_meetings || 0 
        }))
      })
      .catch(() => {})
  }, [])

  async function handleRoleChange(userId, newRole) {
    setError(''); setInfo('')
    try {
      const res = await API.post(`/api/auth/admin/users/${userId}/role`, { role: newRole })
      setInfo(res.data.message)
      loadUsers()
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to update security role.')
    }
  }

  async function handleDeleteUser(userId) {
    if (!window.confirm("Are you sure you want to remove this user from the system?")) return
    setError(''); setInfo('')
    try {
      const res = await API.delete(`/api/auth/admin/users/${userId}`)
      setInfo(res.data.message)
      loadUsers()
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to purge user record.')
    }
  }

  if (loading) return <div className="flex items-center justify-center h-64 text-gray-500">Retrieving system registries…</div>

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">System Admin Control Center</h1>
        <p className="text-xs text-gray-400">Audit system users, update access policies, and inspect storage footprint</p>
      </div>

      {/* Notifications */}
      {error && <div className="bg-red-500/10 border border-red-500/20 text-red-400 rounded-lg p-3.5 text-xs">{error}</div>}
      {info && <div className="bg-green-500/10 border border-green-500/20 text-green-400 rounded-lg p-3.5 text-xs">{info}</div>}

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-surface-raised border border-surface-border rounded-xl p-5">
          <div className="text-xs text-gray-500 uppercase font-semibold mb-1">Total System Users</div>
          <div className="text-3xl font-extrabold text-white">{users.length}</div>
          <div className="text-[10px] text-gray-400 mt-1">Registries synchronized</div>
        </div>
        <div className="bg-surface-raised border border-surface-border rounded-xl p-5">
          <div className="text-xs text-gray-500 uppercase font-semibold mb-1">Total Recorded meetings</div>
          <div className="text-3xl font-extrabold text-brand-light">{stats.totalMeetings}</div>
          <div className="text-[10px] text-gray-400 mt-1">All user workspaces combined</div>
        </div>
        <div className="bg-surface-raised border border-surface-border rounded-xl p-5">
          <div className="text-xs text-gray-500 uppercase font-semibold mb-1">Storage Allocation</div>
          <div className="text-3xl font-extrabold text-indigo-400">{stats.storageUsed}</div>
          <div className="text-[10px] text-gray-400 mt-1">PDF & Reports local static store</div>
        </div>
      </div>

      {/* User Management Grid */}
      <div className="bg-surface-raised border border-surface-border rounded-xl overflow-hidden shadow-sm">
        <div className="p-4 border-b border-surface-border bg-white/3">
          <h2 className="text-sm font-semibold text-white">User Registry & Authorization Roles</h2>
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-surface-border bg-white/5">
              {['User Details', 'Access Role Policy', 'Created At Date', 'Administrative Actions'].map(h => (
                <th key={h} className="text-left text-xs font-semibold text-gray-400 uppercase tracking-wider px-4 py-3.5">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-surface-border">
            {users.map(u => (
              <tr key={u.user_id} className="hover:bg-white/3 transition-colors">
                <td className="px-4 py-3.5">
                  <div className="font-semibold text-white">{u.name}</div>
                  <div className="text-xs text-gray-500 mt-0.5">{u.email}</div>
                </td>
                <td className="px-4 py-3.5">
                  <select value={u.role} onChange={e => handleRoleChange(u.user_id, e.target.value)}
                    className="bg-surface border border-surface-border rounded-lg px-2.5 py-1 text-xs text-white outline-none cursor-pointer focus:border-brand">
                    <option value="student">Student Evaluator</option>
                    <option value="team_member">Team Member</option>
                    <option value="manager">Project Manager</option>
                    <option value="admin">Administrator</option>
                  </select>
                </td>
                <td className="px-4 py-3.5 text-xs text-gray-400">
                  {u.created_at ? new Date(u.created_at).toLocaleDateString() : '—'}
                </td>
                <td className="px-4 py-3.5">
                  <button onClick={() => handleDeleteUser(u.user_id)}
                    className="text-xs text-red-400 bg-red-500/10 border border-red-500/20 hover:bg-red-500/20 rounded-md px-2.5 py-1 font-semibold transition-colors">
                    Purge Account
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
