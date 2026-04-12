import { useState, useEffect } from 'react'
import { api } from '../api'

export function DashboardPage() {
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState(null)
  const [engineers, setEngineers] = useState([])
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10))

  const load = async () => {
    setLoading(true)
    try {
      const [s, e] = await Promise.all([
        api.getDashboard(date),
        api.getEngineers(date),
      ])
      setStats(s)
      setEngineers(e || [])
    } catch (err) {
      console.error('Dashboard load error:', err)
    }
    setLoading(false)
  }

  useEffect(() => { load() }, [date])

  const handleSync = async () => {
    try {
      await api.syncToday()
      await load()
    } catch (err) {
      alert('同步失败: ' + err.message)
    }
  }

  if (loading) return <div className="flex items-center justify-center h-64 text-gray-400">加载中...</div>

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">数据看板</h1>
        <div className="flex items-center gap-3">
          <input
            type="date"
            value={date}
            onChange={e => setDate(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm"
          />
          <button onClick={handleSync} className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm hover:bg-blue-700">
            同步今日数据
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-5 gap-4">
          <StatCard value={stats.total_engineers} label="在职工程师" icon="👤" color="bg-blue-50 text-blue-700" />
          <StatCard value={stats.sessions_today} label="今日会话" icon="📋" color="bg-indigo-50 text-indigo-700" />
          <StatCard value={stats.submitted_today} label="已回收" icon="✅" color="bg-green-50 text-green-700" />
          <StatCard value={`${stats.recovery_rate}%`} label="回收率" icon="📈" color={stats.recovery_rate >= 100 ? 'bg-green-50 text-green-700' : 'bg-yellow-50 text-yellow-700'} />
          <StatCard value={stats.pending_candidates} label="待审经验" icon="⏳" color="bg-purple-50 text-purple-700" />
        </div>
      )}

      {/* Engineer Status Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">工程师状态</h2>
        </div>
        <table className="w-full">
          <thead>
            <tr className="text-left text-sm text-gray-500 border-b border-gray-100">
              <th className="px-6 py-3 font-medium">工程师</th>
              <th className="px-6 py-3 font-medium">区域</th>
              <th className="px-6 py-3 font-medium">今日任务</th>
              <th className="px-6 py-3 font-medium">总执行次数</th>
              <th className="px-6 py-3 font-medium">失败次数</th>
              <th className="px-6 py-3 font-medium">会话状态</th>
            </tr>
          </thead>
          <tbody>
            {engineers.length === 0 && (
              <tr><td colSpan="6" className="px-6 py-8 text-center text-gray-400">暂无数据，请先同步今日数据</td></tr>
            )}
            {engineers.map((e, i) => (
              <tr key={e.engineer.id} className={`border-b border-gray-50 hover:bg-gray-50 ${i % 2 === 0 ? '' : 'bg-gray-25'}`}>
                <td className="px-6 py-3">
                  <span className="font-medium text-gray-900">{e.engineer.name}</span>
                  <span className="text-xs text-gray-400 ml-2">{e.engineer.role}</span>
                </td>
                <td className="px-6 py-3 text-sm text-gray-600">{e.engineer.region}</td>
                <td className="px-6 py-3 text-sm">{e.task_count}</td>
                <td className="px-6 py-3 text-sm">{e.total_exec}</td>
                <td className="px-6 py-3">
                  {e.failed_count > 0 ? (
                    <span className="text-red-600 font-medium">{e.failed_count}</span>
                  ) : (
                    <span className="text-gray-400">0</span>
                  )}
                </td>
                <td className="px-6 py-3">
                  <StatusBadge status={e.session_status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

function StatCard({ value, label, icon, color }) {
  return (
    <div className={`${color} rounded-xl p-4`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-2xl">{icon}</span>
      </div>
      <div className="text-2xl font-bold">{value}</div>
      <div className="text-sm opacity-80">{label}</div>
    </div>
  )
}

function StatusBadge({ status }) {
  const styles = {
    pending: 'bg-blue-100 text-blue-700',
    pushed: 'bg-yellow-100 text-yellow-700',
    submitted: 'bg-green-100 text-green-700',
    expired: 'bg-gray-100 text-gray-500',
  }
  const labels = {
    pending: '待填写',
    pushed: '已推送',
    submitted: '已回收',
    expired: '已过期',
  }
  if (!status) return <span className="text-gray-400 text-sm">无会话</span>
  return <span className={`px-2 py-1 rounded-full text-xs font-medium ${styles[status] || 'bg-gray-100 text-gray-500'}`}>{labels[status] || status}</span>
}
