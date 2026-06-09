import { useEffect, useState } from 'react'
import API from '../api/client'

const COLUMNS = ['pending', 'in_progress', 'done']
const COL_LABELS = { pending: 'Pending', in_progress: 'In Progress', done: 'Completed' }
const PRIORITY_COLORS = { 
  high: 'text-red-400 bg-red-500/10 border-red-500/20', 
  medium: 'text-amber-400 bg-amber-500/10 border-amber-500/20', 
  low: 'text-gray-400 bg-gray-500/10 border-gray-500/20' 
}

export default function TaskTracker() {
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(true)
  const [alertMsg, setAlertMsg] = useState('')

  function load() { 
    setLoading(true)
    API.get('/api/tasks/')
      .then(r => { setTasks(r.data.tasks || []); setLoading(false) })
      .catch(() => setLoading(false))
  }
  
  useEffect(load, [])

  async function updateStatus(id, newStatus) {
    try {
      await API.post(`/api/tasks/${id}/status`, { status: newStatus })
      load()
    } catch {
      alert("Failed to update task status.")
    }
  }

  async function triggerReminder(id) {
    try {
      const res = await API.post(`/api/tasks/${id}/remind`)
      setAlertMsg(res.data.message)
      setTimeout(() => setAlertMsg(''), 4000)
    } catch {
      alert("Failed to send task reminder.")
    }
  }

  if (loading) return <div className="flex items-center justify-center h-64 text-gray-500">Retrieving team action items…</div>

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-white">Action Items Tracker</h1>
          <p className="text-xs text-gray-400">Track and notify owners of key meeting takeaways</p>
        </div>
        <button onClick={load} className="text-xs bg-surface-raised border border-surface-border hover:bg-white/5 rounded-lg px-3 py-2 text-white font-semibold transition-colors">
          ↻ Refresh Board
        </button>
      </div>

      {/* Reminder Notification Banner */}
      {alertMsg && (
        <div className="bg-brand/10 border border-brand/20 text-brand-light rounded-xl p-4 text-xs transition-all animate-pulse">
          🔔 {alertMsg}
        </div>
      )}

      {/* Kanban Board Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {COLUMNS.map(col => {
          const colTasks = tasks.filter(t => t.status === col)
          return (
            <div key={col} className="bg-surface-raised border border-surface-border rounded-xl p-4 shadow-sm flex flex-col h-[600px]">
              <div className="flex items-center justify-between mb-4 border-b border-surface-border pb-2">
                <h2 className="text-sm font-semibold text-white">{COL_LABELS[col]}</h2>
                <span className="text-xs bg-surface border border-surface-border text-gray-400 rounded-full px-2 py-0.5 font-bold">
                  {colTasks.length}
                </span>
              </div>

              {/* Tasks List */}
              <div className="space-y-3 overflow-y-auto flex-1 scrollbar-thin pr-1">
                {colTasks.map(task => (
                  <div key={task.task_id} className="bg-surface border border-surface-border rounded-xl p-4 shadow-sm space-y-3 hover:border-brand/30 transition-all duration-200">
                    <p className="text-sm font-medium text-white leading-snug">{task.description}</p>
                    
                    <div className="flex justify-between items-center text-xs">
                      <div className="flex items-center gap-1.5 text-gray-400">
                        <div className="w-5 h-5 rounded-full bg-brand/10 text-[9px] text-brand-light font-bold flex items-center justify-center">
                          {task.owner_name?.[0] || 'U'}
                        </div>
                        <span className="truncate max-w-[100px]">{task.owner_name || 'Unassigned'}</span>
                      </div>
                      <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${PRIORITY_COLORS[task.priority] || ''}`}>
                        {task.priority?.toUpperCase()}
                      </span>
                    </div>

                    {task.deadline && (
                      <div className="text-[11px] text-gray-500 font-semibold flex items-center gap-1">
                        <span>📅</span> Due: {task.deadline}
                      </div>
                    )}

                    {/* Transition actions */}
                    <div className="pt-2 border-t border-surface-border flex gap-1.5 flex-wrap">
                      {col === 'pending' && (
                        <button onClick={() => updateStatus(task.task_id, 'in_progress')}
                          className="flex-1 text-[10px] py-1.5 rounded-md bg-brand/10 text-brand-light border border-brand/20 hover:bg-brand/20 transition-colors font-bold">
                          Start Task
                        </button>
                      )}
                      {col === 'in_progress' && (
                        <>
                          <button onClick={() => updateStatus(task.task_id, 'done')}
                            className="flex-1 text-[10px] py-1.5 rounded-md bg-green-500/10 text-green-400 border border-green-500/20 hover:bg-green-500/20 transition-colors font-bold">
                            Complete
                          </button>
                          <button onClick={() => updateStatus(task.task_id, 'pending')}
                            className="text-[10px] py-1.5 px-2 rounded-md bg-surface border border-surface-border hover:bg-white/5 text-gray-400 transition-colors font-semibold">
                            Reopen
                          </button>
                        </>
                      )}
                      {col === 'done' && (
                        <button onClick={() => updateStatus(task.task_id, 'in_progress')}
                          className="flex-1 text-[10px] py-1.5 rounded-md bg-surface border border-surface-border hover:bg-white/5 text-gray-400 transition-colors font-semibold">
                          Reopen Task
                        </button>
                      )}
                      
                      {/* Reminder Trigger (only for incomplete tasks) */}
                      {col !== 'done' && (
                        <button onClick={() => triggerReminder(task.task_id)} title="Send Email Reminder"
                          className="text-[10px] py-1.5 px-2.5 rounded-md bg-amber-500/10 text-amber-400 border border-amber-500/20 hover:bg-amber-500/20 transition-colors font-bold">
                          🔔 Notify
                        </button>
                      )}
                    </div>
                  </div>
                ))}

                {colTasks.length === 0 && (
                  <div className="flex flex-col items-center justify-center py-12 text-center text-gray-600">
                    <span className="text-xl mb-1">📋</span>
                    <p className="text-xs">No tasks in this state</p>
                  </div>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
