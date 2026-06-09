import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts'
import API from '../api/client'

const TABS = ['Summary', 'Action Items', 'Transcript', 'Speaker Analytics', 'Attendance']
const COLORS = ['#7c6fff', '#4ade80', '#60a5fa', '#fbbf24', '#fb7185', '#a78bfa']
const SENT_COLOR = { pos: '#4ade80', neu: '#9ca3af', neg: '#fb7185' }

export default function MeetingDetail() {
  const { id }     = useParams()
  const [tab, setTab] = useState('Summary')
  const [meeting, setMeeting] = useState(null)
  const [report,  setReport]  = useState(null)
  const [transcript, setTranscript] = useState([])
  const [chat, setChat] = useState([])
  const [question, setQ] = useState('')
  const [chatLoading, setCL] = useState(false)
  const [downloading, setDownloading] = useState({ pdf: false, excel: false, docx: false })

  useEffect(() => {
    API.get(`/api/meetings/${id}`).then(r => { 
      setMeeting(r.data)
      setReport(r.data.report) 
    })
    API.get(`/api/transcript/${id}`).then(r => setTranscript(r.data.transcript || []))
  }, [id])

  async function askAI() {
    if (!question.trim()) return
    const q = question; setQ(''); setCL(true)
    setChat(c => [...c, { role: 'user', text: q }])
    try {
      const r = await API.post('/api/ai/chat', { meeting_id: id, question: q })
      setChat(c => [...c, { role: 'ai', text: r.data.answer }])
    } catch { 
      setChat(c => [...c, { role: 'ai', text: 'Sorry, I encountered an issue querying the RAG transcript client.' }]) 
    } finally { 
      setCL(false) 
    }
  }

  // Programmatic file downloading with JWT verification headers via Axios
  async function downloadReportFile(fileType, mimeType, extension) {
    setDownloading(prev => ({ ...prev, [fileType]: true }))
    try {
      const endpoint = fileType === 'pdf' 
        ? `/api/reports/${id}/download` 
        : `/api/reports/${id}/${fileType}`
      
      const response = await API.get(endpoint, { responseType: 'blob' })
      const blob = new Blob([response.data], { type: mimeType })
      const downloadUrl = window.URL.createObjectURL(blob)
      
      const link = document.createElement('a')
      link.href = downloadUrl
      link.download = `SmartMeet_${meeting.title.replace(/\s+/g, '_')}_Report.${extension}`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    } catch (err) {
      alert(`Could not download ${fileType.toUpperCase()} file. Verify server environment variables.`)
    } finally {
      setDownloading(prev => ({ ...prev, [fileType]: false }))
    }
  }

  if (!meeting) return <div className="flex items-center justify-center h-64 text-gray-500">Loading meeting analytics…</div>

  const speakerData = report?.speaker_stats
    ? Object.entries(report.speaker_stats).map(([name, s]) => ({ name, value: s.participation_pct || 0 }))
    : []

  // Calculate sentiment percentages for progress bars
  const sb = report?.sentiment_breakdown || { positive: 0, neutral: 0, negative: 0 }
  const totalSent = (sb.positive + sb.neutral + sb.negative) || 1
  const sentPct = {
    pos: Math.round((sb.positive / totalSent) * 100),
    neu: Math.round((sb.neutral / totalSent) * 100),
    neg: Math.round((sb.negative / totalSent) * 100)
  }

  const dynamics = report?.dynamics || { agreement_score: 80, frustration_level: 10, engagement_level: 85, excitement_level: 40 }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header briefing */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between bg-surface-raised border border-surface-border rounded-xl p-5 shadow-sm gap-4">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-brand-light bg-brand/10 border border-brand/20 px-2.5 py-1 rounded-md mb-2 inline-block">
            {meeting.platform?.toUpperCase()} SESSION
          </span>
          <h1 className="text-2xl font-bold text-white tracking-tight">{meeting.title}</h1>
          <p className="text-xs text-gray-400 mt-1">
            Duration: {meeting.duration_mins} mins {meeting.started_at && ` · Commenced: ${new Date(meeting.started_at).toLocaleString()}`}
          </p>
        </div>

        {/* Programmatic export options */}
        {report && (
          <div className="flex flex-wrap gap-2">
            <button onClick={() => downloadReportFile('pdf', 'application/pdf', 'pdf')} disabled={downloading.pdf}
              className="text-xs bg-red-500/10 text-red-400 border border-red-500/20 rounded-lg px-3 py-2 hover:bg-red-500/20 transition-all font-semibold disabled:opacity-50">
              {downloading.pdf ? 'Compiling...' : '↓ Download PDF'}
            </button>
            <button onClick={() => downloadReportFile('excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'xlsx')} disabled={downloading.excel}
              className="text-xs bg-green-500/10 text-green-400 border border-green-500/20 rounded-lg px-3 py-2 hover:bg-green-500/20 transition-all font-semibold disabled:opacity-50">
              {downloading.excel ? 'Exporting...' : '↓ Export Excel'}
            </button>
            <button onClick={() => downloadReportFile('docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'docx')} disabled={downloading.docx}
              className="text-xs bg-blue-500/10 text-blue-400 border border-blue-500/20 rounded-lg px-3 py-2 hover:bg-blue-500/20 transition-all font-semibold disabled:opacity-50">
              {downloading.docx ? 'Formatting...' : '↓ Export Word'}
            </button>
          </div>
        )}
      </div>

      {/* Tabs list */}
      <div className="flex border-b border-surface-border">
        {TABS.map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-4 py-2.5 text-sm font-semibold border-b-2 -mb-px transition-colors ${tab === t ? 'border-brand text-brand-light' : 'border-transparent text-gray-400 hover:text-white'}`}>
            {t}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Details Panel */}
        <div className="lg:col-span-2 space-y-6">
          {tab === 'Summary' && (
            <div className="space-y-6">
              {/* Executive summary block */}
              <div className="bg-surface-raised border border-surface-border rounded-xl p-5 shadow-sm">
                <h3 className="text-sm font-semibold text-white mb-3">Executive Summary</h3>
                <p className="text-sm text-gray-300 leading-relaxed">{report?.summary || 'Transcript processing in progress. Metrics will populate shortly.'}</p>
              </div>

              {/* Detailed Summary block */}
              {report?.detailed_summary && (
                <div className="bg-surface-raised border border-surface-border rounded-xl p-5 shadow-sm">
                  <h3 className="text-sm font-semibold text-white mb-3">Detailed Discussions</h3>
                  <p className="text-sm text-gray-300 leading-relaxed whitespace-pre-line">{report.detailed_summary}</p>
                </div>
              )}

              {/* Decisions block */}
              {report?.key_decisions?.length > 0 && (
                <div className="bg-surface-raised border border-surface-border rounded-xl p-5 shadow-sm">
                  <h3 className="text-sm font-semibold text-white mb-3">Key Decisions Logged</h3>
                  <ul className="space-y-2.5">
                    {report.key_decisions.map((d, i) => (
                      <li key={i} className="flex gap-2.5 text-sm text-gray-300">
                        <span className="text-brand-light font-extrabold">•</span>
                        {d}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Risks block */}
              {report?.risks?.length > 0 && (
                <div className="bg-surface-raised border border-surface-border rounded-xl p-5 shadow-sm">
                  <h3 className="text-sm font-semibold text-white mb-3">Identified Risks & Concerns</h3>
                  <ul className="space-y-2.5">
                    {report.risks.map((r, i) => (
                      <li key={i} className="flex gap-2.5 text-sm text-amber-400 font-medium">
                        <span>⚠️</span>
                        {r}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {tab === 'Action Items' && (
            <div className="bg-surface-raised border border-surface-border rounded-xl overflow-hidden shadow-sm">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-surface-border bg-white/5">
                      {['Action Task Description', 'Assigned Owner', 'Target Deadline', 'Priority', 'Status'].map(h => (
                        <th key={h} className="text-left text-xs font-semibold text-gray-400 uppercase tracking-wider px-4 py-3.5">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-surface-border">
                    {(report?.tasks || []).map(t => (
                      <tr key={t.task_id} className="hover:bg-white/3 transition-colors">
                        <td className="px-4 py-3 text-sm font-medium text-gray-200">{t.description}</td>
                        <td className="px-4 py-3 text-sm text-gray-400">{t.owner_name || 'Unassigned'}</td>
                        <td className="px-4 py-3 text-sm text-gray-400">{t.deadline || '—'}</td>
                        <td className="px-4 py-3 text-xs">
                          <span className={`px-2 py-0.5 rounded-full font-semibold ${t.priority === 'high' ? 'bg-red-500/10 text-red-400 border border-red-500/20' : t.priority === 'medium' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' : 'bg-gray-500/10 text-gray-400 border border-gray-500/20'}`}>
                            {t.priority?.toUpperCase()}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-xs">
                          <span className={`px-2 py-0.5 rounded-full font-semibold ${t.status === 'done' ? 'bg-green-500/10 text-green-400 border border-green-500/20' : 'bg-surface border border-surface-border text-gray-400'}`}>
                            {t.status?.toUpperCase()}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {!report?.tasks?.length && <p className="text-center text-gray-500 text-sm py-12">No action items extracted from this meeting.</p>}
            </div>
          )}

          {tab === 'Transcript' && (
            <div className="bg-surface-raised border border-surface-border rounded-xl p-5 space-y-4 max-h-[600px] overflow-y-auto scrollbar-thin">
              {transcript.map((e, i) => (
                <div key={i} className="flex gap-3 items-start hover:bg-white/3 p-2 rounded-lg transition-colors">
                  <div className="flex-shrink-0 w-9 h-9 rounded-xl bg-brand/20 flex items-center justify-center text-xs text-brand-light font-bold">
                    {e.speaker?.[0] || '?'}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-bold text-white">{e.speaker}</span>
                      <span className="text-xs" style={{ color: SENT_COLOR[e.sentiment] || '#9ca3af' }}>●</span>
                      <span className="text-[10px] text-gray-500 font-semibold">{e.timestamp ? new Date(e.timestamp).toLocaleTimeString() : ''}</span>
                    </div>
                    <p className="text-sm text-gray-300 leading-relaxed">{e.text}</p>
                  </div>
                </div>
              ))}
              {!transcript.length && <p className="text-center text-gray-500 text-sm py-12">No meeting transcript log is available.</p>}
            </div>
          )}

          {tab === 'Speaker Analytics' && (
            <div className="bg-surface-raised border border-surface-border rounded-xl p-5 space-y-6">
              <h3 className="text-sm font-semibold text-white">Participation Breakdown</h3>
              {speakerData.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-center">
                  <div className="h-56">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie data={speakerData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} paddingAngle={3} dataKey="value">
                          {speakerData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                        </Pie>
                        <Tooltip formatter={(v) => `${v}%`} contentStyle={{ background: '#1a1a2e', border: '1px solid #2a2a40', borderRadius: '8px' }} />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                  <div className="space-y-3">
                    {Object.entries(report.speaker_stats || {}).map(([name, s], i) => (
                      <div key={name} className="flex items-center justify-between text-xs border-b border-surface-border pb-2">
                        <div className="flex items-center gap-2">
                          <div className="w-3 h-3 rounded-full" style={{ background: COLORS[i % COLORS.length] }}></div>
                          <span className="text-white font-semibold">{name}</span>
                        </div>
                        <div className="flex gap-4 text-gray-400">
                          <span>{s.messages} msgs</span>
                          <span>{s.words} words</span>
                          <span className="text-brand-light font-bold">{s.participation_pct}%</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : <p className="text-center text-gray-500 text-sm py-12">Speaker stats not yet parsed.</p>}
            </div>
          )}

          {tab === 'Attendance' && (
            <div className="bg-surface-raised border border-surface-border rounded-xl overflow-hidden shadow-sm">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-surface-border bg-white/5">
                    {['Attendee Name', 'Email Address', 'Joined At', 'Duration Present'].map(h => (
                      <th key={h} className="text-left text-xs font-semibold text-gray-400 uppercase tracking-wider px-4 py-3.5">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-surface-border">
                  {(report?.attendance || []).map((p, i) => (
                    <tr key={i} className="hover:bg-white/3 transition-colors">
                      <td className="px-4 py-3 font-semibold text-white">{p.name}</td>
                      <td className="px-4 py-3 text-gray-400">{p.email || '—'}</td>
                      <td className="px-4 py-3 text-gray-400">{p.joined_at ? new Date(p.joined_at).toLocaleTimeString() : '—'}</td>
                      <td className="px-4 py-3 text-brand-light font-semibold">{p.duration_mins} mins</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {!report?.attendance?.length && <p className="text-center text-gray-500 text-sm py-12">No attendee information logged.</p>}
            </div>
          )}
        </div>

        {/* Sidebar AI Chat & Analytics panel */}
        <div className="space-y-6 col-span-1">
          {/* Productivity & Sentiment Card */}
          {report && (
            <div className="bg-surface-raised border border-surface-border rounded-xl p-5 space-y-4 shadow-sm">
              <h3 className="text-sm font-semibold text-white">Sentiment & Engagement</h3>
              
              {/* Score bar */}
              <div>
                <div className="flex justify-between text-xs text-gray-400 mb-1">
                  <span>Productivity Score</span>
                  <span className="text-brand-light font-semibold">{report.productivity_score}/100</span>
                </div>
                <div className="w-full h-2 bg-surface border border-surface-border rounded-full overflow-hidden">
                  <div className="h-full bg-brand rounded-full" style={{ width: `${report.productivity_score}%` }}></div>
                </div>
              </div>

              {/* Sentiment Progress bar */}
              <div>
                <div className="flex justify-between text-xs text-gray-400 mb-1">
                  <span>Sentiment Breakdown</span>
                  <span className="text-green-400 font-semibold">{sentPct.pos}% Positive</span>
                </div>
                <div className="flex w-full h-2 bg-surface rounded-full overflow-hidden border border-surface-border">
                  <div className="bg-[#4ade80]" style={{ width: `${sentPct.pos}%` }}></div>
                  <div className="bg-[#9ca3af]" style={{ width: `${sentPct.neu}%` }}></div>
                  <div className="bg-[#fb7185]" style={{ width: `${sentPct.neg}%` }}></div>
                </div>
              </div>

              {/* Dynamics indicators */}
              <div className="grid grid-cols-2 gap-3 pt-2">
                <div className="bg-surface border border-surface-border rounded-lg p-2.5 text-center">
                  <div className="text-[10px] text-gray-500 font-semibold uppercase">Agreement</div>
                  <div className="text-lg font-bold text-blue-400">{dynamics.agreement_score}%</div>
                </div>
                <div className="bg-surface border border-surface-border rounded-lg p-2.5 text-center">
                  <div className="text-[10px] text-gray-500 font-semibold uppercase">Engagement</div>
                  <div className="text-lg font-bold text-green-400">{dynamics.engagement_level}%</div>
                </div>
                <div className="bg-surface border border-surface-border rounded-lg p-2.5 text-center">
                  <div className="text-[10px] text-gray-500 font-semibold uppercase">Frustration</div>
                  <div className="text-lg font-bold text-red-400">{dynamics.frustration_level}%</div>
                </div>
                <div className="bg-surface border border-surface-border rounded-lg p-2.5 text-center">
                  <div className="text-[10px] text-gray-500 font-semibold uppercase">Excitement</div>
                  <div className="text-lg font-bold text-amber-400">{dynamics.excitement_level}%</div>
                </div>
              </div>
            </div>
          )}

          {/* AI Chatbox Panel */}
          <div className="bg-surface-raised border border-surface-border rounded-xl p-5 shadow-sm flex flex-col h-[400px]">
            <h3 className="text-sm font-semibold text-white mb-1">AI Meeting Chatbot</h3>
            <p className="text-[11px] text-gray-500 mb-3 leading-tight">Ask questions about assignments, action points, and decisions.</p>

            <div className="flex-1 space-y-3 overflow-y-auto mb-3 scrollbar-thin max-h-60 pr-1">
              {chat.map((m, i) => (
                <div key={i} className={`p-2.5 rounded-lg text-xs leading-relaxed ${m.role === 'user' ? 'bg-brand/20 text-brand-light ml-4 border border-brand/20' : 'bg-surface text-gray-200 mr-4 border border-surface-border'}`}>
                  <strong>{m.role === 'user' ? 'You' : 'Assistant'}:</strong> {m.text}
                </div>
              ))}
              {chatLoading && (
                <div className="text-xs text-gray-500 italic flex items-center gap-1">
                  <span className="animate-pulse">●</span> Thinking…
                </div>
              )}
              {!chat.length && <p className="text-xs text-gray-600 text-center mt-12 italic">Ask: "What decisions were made?"</p>}
            </div>

            <div className="flex gap-1.5 mt-auto pt-2 border-t border-surface-border">
              <input value={question} onChange={e => setQ(e.target.value)} onKeyDown={e => e.key === 'Enter' && askAI()}
                placeholder="Ask meeting details..."
                className="flex-1 bg-surface border border-surface-border rounded-lg px-3 py-2 text-xs text-white outline-none focus:border-brand transition-colors" />
              <button onClick={askAI} className="bg-brand hover:bg-brand-dark text-white rounded-lg px-3 py-2 text-xs font-semibold transition-colors">Send</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
