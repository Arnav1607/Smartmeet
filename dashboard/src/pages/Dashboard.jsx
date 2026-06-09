import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts'
import API from '../api/client'

const PLATFORM_COLOR = { gmeet: '#4ade80', zoom: '#60a5fa', teams: '#a78bfa', other: '#9ca3af' }
const PIE_COLORS = ['#7c6fff', '#4ade80', '#60a5fa', '#a78bfa', '#fb7185']

function StatCard({ label, value, sub, color = 'text-brand-light' }) {
  return (
    <div className="bg-surface-raised border border-surface-border rounded-xl p-5 shadow-sm transition-all hover:border-brand/40 duration-200">
      <div className="text-xs text-gray-500 uppercase tracking-wide mb-2">{label}</div>
      <div className={`text-3xl font-extrabold ${color}`}>{value}</div>
      {sub && <div className="text-xs text-gray-400 mt-1">{sub}</div>}
    </div>
  )
}

export default function Dashboard() {
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    API.get('/api/dashboard/stats')
      .then(r => { setStats(r.data); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  if (loading) return <div className="flex items-center justify-center h-64 text-gray-500">Retrieving system insights…</div>

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-white">Project Overview</h1>
          <p className="text-xs text-gray-400">SmartMeet AI Team Productivity & Meeting Analytics</p>
        </div>
        <div className="text-xs text-gray-500 bg-surface-raised border border-surface-border px-3 py-1.5 rounded-lg">
          Live Sync Status: <span className="text-green-400 font-semibold">Active</span>
        </div>
      </div>

      {/* Grid statistics metrics */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Total Meetings" value={stats?.total_meetings ?? 0} sub="recorded" />
        <StatCard label="Total Hours" value={stats?.total_hours ?? 0} sub="speaking duration" />
        <StatCard label="Avg Attendance" value={`${stats?.avg_attendance_rate ?? 0}%`} sub="participation score" color="text-green-400" />
        <StatCard label="AI Productivity Score" value={`${stats?.avg_productivity_score ?? 0}/100`} sub="meeting rating" color="text-brand-light" />
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Task Completion" value={`${stats?.task_completion_rate ?? 0}%`} sub="action items resolved" color="text-indigo-400" />
        <StatCard label="Pending Tasks" value={stats?.pending_tasks ?? 0} sub="awaiting action" color="text-amber-400" />
        <StatCard label="Meetings This Week" value={stats?.this_week ?? 0} sub="recorded" color="text-cyan-400" />
        <StatCard label="Connected Teams" value="1" sub="default workspace" color="text-gray-300" />
      </div>

      {/* Charts section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Weekly activity line chart */}
        <div className="lg:col-span-2 bg-surface-raised border border-surface-border rounded-xl p-5 shadow-sm">
          <h2 className="text-sm font-semibold text-white mb-4">Weekly Activity (Meetings Count)</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={stats?.weekly_activity || []}>
                <XAxis dataKey="name" stroke="#6b7280" fontSize={11} tickLine={false} />
                <YAxis stroke="#6b7280" fontSize={11} tickLine={false} allowDecimals={false} />
                <Tooltip contentStyle={{ background: '#1a1a2e', border: '1px solid #2a2a40', borderRadius: '8px', color: '#fff', fontSize: '12px' }} />
                <Line type="monotone" dataKey="Meetings" stroke="#7c6fff" strokeWidth={3} dot={{ fill: '#7c6fff', r: 4 }} activeDot={{ r: 6 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Platform breakdown pie chart */}
        <div className="bg-surface-raised border border-surface-border rounded-xl p-5 shadow-sm">
          <h2 className="text-sm font-semibold text-white mb-4">Meeting Platforms</h2>
          <div className="h-64 flex flex-col justify-center items-center">
            <ResponsiveContainer width="100%" height="80%">
              <PieChart>
                <Pie data={stats?.platform_breakdown || []} cx="50%" cy="50%" innerRadius={60} outerRadius={80} paddingAngle={4} dataKey="value">
                  {(stats?.platform_breakdown || []).map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={PIE_COLORS[index % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ background: '#1a1a2e', border: '1px solid #2a2a40', borderRadius: '8px', color: '#fff', fontSize: '11px' }} />
              </PieChart>
            </ResponsiveContainer>
            <div className="flex flex-wrap justify-center gap-3 mt-2">
              {(stats?.platform_breakdown || []).map((entry, index) => (
                <div key={entry.name} className="flex items-center gap-1.5 text-xs text-gray-400">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: PIE_COLORS[index % PIE_COLORS.length] }}></span>
                  {entry.name}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Recent Meetings Grid */}
      <div className="bg-surface-raised border border-surface-border rounded-xl p-5 shadow-sm">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-sm font-semibold text-white">Recent Meetings Sessions</h2>
          <Link to="/meetings" className="text-xs text-brand-light hover:underline font-semibold">View All Meetings →</Link>
        </div>
        <div className="space-y-2">
          {(stats?.recent_meetings || []).map(m => (
            <Link key={m.meeting_id} to={`/meetings/${m.meeting_id}`}
              className="flex items-center justify-between p-3 rounded-lg hover:bg-white/5 transition-all group border border-transparent hover:border-surface-border">
              <div className="flex items-center gap-3">
                <div className="w-3 h-3 rounded-full" style={{ background: PLATFORM_COLOR[m.platform] || '#9ca3af' }}></div>
                <div>
                  <div className="text-sm font-semibold text-white group-hover:text-brand-light transition-colors">{m.title}</div>
                  <div className="text-xs text-gray-500 mt-0.5">{m.platform?.toUpperCase()} Source · {m.duration_mins} min · {new Date(m.started_at).toLocaleString()}</div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                {m.has_report ? (
                  <span className="text-xs bg-green-500/10 text-green-400 border border-green-500/20 px-2 py-0.5 rounded-full">Report Analyzed</span>
                ) : (
                  <span className="text-xs bg-amber-500/10 text-amber-400 border border-amber-500/20 px-2 py-0.5 rounded-full">Recording Saved</span>
                )}
                <span className="text-xs text-gray-600">→</span>
              </div>
            </Link>
          ))}
          {!stats?.recent_meetings?.length && (
            <p className="text-sm text-gray-500 text-center py-8">No meetings recorded yet. Run a Google Meet, Zoom, or Teams call with the Chrome Extension active.</p>
          )}
        </div>
      </div>
    </div>
  )
}
