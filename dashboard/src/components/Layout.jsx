// src/components/Layout.jsx
import { Outlet, NavLink, useNavigate } from 'react-router-dom';

const NAV = [
  { to: '/dashboard', icon: '⬡', label: 'Dashboard' },
  { to: '/meetings',  icon: '📋', label: 'Meetings'  },
  { to: '/tasks',     icon: '✅', label: 'Tasks'      },
];

export default function Layout() {
  const navigate = useNavigate();

  function logout() {
    localStorage.removeItem('smartmeet_token');
    navigate('/login');
  }

  return (
    <div className="flex h-screen bg-gray-950 text-gray-100 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-56 bg-gray-900 border-r border-gray-800 flex flex-col">
        <div className="p-4 border-b border-gray-800">
          <div className="text-purple-400 text-xl font-bold">⬡ SmartMeet</div>
          <div className="text-gray-500 text-xs mt-0.5">AI Meeting Intelligence</div>
        </div>
        <nav className="flex-1 p-3 space-y-1">
          {NAV.map(n => (
            <NavLink
              key={n.to} to={n.to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                  isActive
                    ? 'bg-purple-500/20 text-purple-300'
                    : 'text-gray-400 hover:bg-gray-800 hover:text-gray-200'
                }`}
            >
              <span>{n.icon}</span>{n.label}
            </NavLink>
          ))}
        </nav>
        <div className="p-3 border-t border-gray-800">
          <button
            onClick={logout}
            className="w-full px-3 py-2 text-xs text-gray-500 hover:text-gray-300 text-left rounded-lg hover:bg-gray-800 transition-colors"
          >
            Sign out
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  );
}
