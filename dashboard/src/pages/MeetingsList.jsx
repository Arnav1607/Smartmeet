import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import API from '../api/client'

export default function MeetingsList() {
  const [meetings, setMeetings] = useState([])
  const [search, setSearch]     = useState('')
  const [page, setPage]         = useState(1)
  const [total, setTotal]       = useState(0)

  function load() {
    API.get(`/api/meetings/?page=${page}&q=${search}`).then(r => {
      setMeetings(r.data.meetings); setTotal(r.data.total)
    })
  }

  useEffect(load, [page, search])

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold text-white">Meetings</h1>
        <input value={search} onChange={e => { setSearch(e.target.value); setPage(1) }}
          placeholder="Search meetings…"
          className="bg-surface-raised border border-surface-border rounded-lg px-3 py-2 text-sm text-white outline-none focus:border-brand w-56 transition-colors" />
      </div>

      <div className="bg-surface-raised border border-surface-border rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-surface-border">
              {['Title','Platform','Date','Duration','Report'].map(h => (
                <th key={h} className="text-left text-xs text-gray-500 uppercase tracking-wide px-4 py-3">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {meetings.map(m => (
              <tr key={m.meeting_id} className="border-b border-surface-border hover:bg-white/3 transition-colors">
                <td className="px-4 py-3">
                  <Link to={`/meetings/${m.meeting_id}`} className="text-white hover:text-brand-light transition-colors">{m.title}</Link>
                </td>
                <td className="px-4 py-3 text-gray-400 uppercase text-xs">{m.platform}</td>
                <td className="px-4 py-3 text-gray-400">{m.started_at ? new Date(m.started_at).toLocaleDateString() : '—'}</td>
                <td className="px-4 py-3 text-gray-400">{m.duration_mins}m</td>
                <td className="px-4 py-3">
                  <Link to={`/meetings/${m.meeting_id}`} className="text-xs text-brand-light hover:underline">View →</Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!meetings.length && <p className="text-center text-gray-500 text-sm py-12">No meetings found.</p>}
      </div>

      <div className="flex items-center justify-between mt-4 text-xs text-gray-500">
        <span>{total} total meetings</span>
        <div className="flex gap-2">
          <button disabled={page === 1} onClick={() => setPage(p => p-1)} className="px-3 py-1 rounded bg-surface-raised border border-surface-border disabled:opacity-30">Prev</button>
          <button onClick={() => setPage(p => p+1)} className="px-3 py-1 rounded bg-surface-raised border border-surface-border">Next</button>
        </div>
      </div>
    </div>
  )
}
