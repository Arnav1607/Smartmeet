import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './hooks/useAuth'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import MeetingsList from './pages/MeetingsList'
import MeetingDetail from './pages/MeetingDetail'
import TaskTracker from './pages/TaskTracker'
import AdminDashboard from './pages/AdminDashboard'
import Sidebar from './components/Sidebar'

function PrivateLayout({ children }) {
  return (
    <div className="flex min-h-screen bg-surface">
      <Sidebar />
      <main className="flex-1 ml-56 p-6">{children}</main>
    </div>
  )
}

function PrivateRoute({ children }) {
  const { token } = useAuth()
  return token ? <PrivateLayout>{children}</PrivateLayout> : <Navigate to="/login" />
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
        <Route path="/meetings" element={<PrivateRoute><MeetingsList /></PrivateRoute>} />
        <Route path="/meetings/:id" element={<PrivateRoute><MeetingDetail /></PrivateRoute>} />
        <Route path="/tasks" element={<PrivateRoute><TaskTracker /></PrivateRoute>} />
        <Route path="/admin" element={<PrivateRoute><AdminDashboard /></PrivateRoute>} />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    </BrowserRouter>
  )
}
