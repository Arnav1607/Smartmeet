import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

const links = [
  { to: '/',          label: 'Dashboard',  icon: '▦' },
  { to: '/meetings',  label: 'Meetings',   icon: '◷' },
  { to: '/tasks',     label: 'Tasks',      icon: '✓' },
]

export default function Sidebar() {
  const { logout, user } = useAuth()
  const navigate = useNavigate()

  // Render admin link only for admin users
  const activeLinks = [...links]
  if (user?.role === 'admin') {
    activeLinks.push({ to: '/admin', label: 'Admin Panel', icon: '⚙' })
  }

  return (
    <aside className="fixed left-0 top-0 h-screen w-56 bg-surface-raised border-r border-surface-border flex flex-col z-50">
      <div className="p-4 border-b border-surface-border">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-brand flex items-center justify-center text-white text-sm font-bold">⬡</div>
          <div>
            <div className="text-sm font-semibold text-white">SmartMeet AI</div>
            <div className="text-xs text-gray-500">Dashboard</div>
          </div>
        </div>
      </div>

      <nav className="flex-1 p-3 space-y-1">
        {activeLinks.map(l => (
          <NavLink key={l.to} to={l.to} end={l.to === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                isActive ? 'bg-brand/20 text-brand-light font-medium' : 'text-gray-400 hover:text-white hover:bg-white/5'
              }`
            }>
            <span className="text-base">{l.icon}</span>{l.label}
          </NavLink>
        ))}
      </nav>

      <div className="p-3 border-t border-surface-border">
        <div className="text-xs text-brand-light font-semibold mb-1 px-2 capitalize">{user?.role?.replace('_', ' ')} Account</div>
        <div className="text-[10px] text-gray-500 mb-2 px-2 truncate">{user?.email || 'User'}</div>
        <button onClick={() => { logout(); navigate('/login') }}
          className="w-full text-left px-3 py-2 rounded-lg text-sm text-gray-400 hover:text-red-400 hover:bg-red-400/10 transition-colors">
          Sign out
        </button>
      </div>
    </aside>
  )
}
