import { useState, useEffect } from 'react'
import { api } from '../api'

const catLabel = {
  experience: '经验', failure_case: '失败案例', tuning_record: '调优',
  customer_pref: '客户反馈', delivery_issue: '交付问题',
  rule_candidate: '规则', template_patch: '模板', daily_record: '日常',
}
const catColor = {
  failure_case: 'text-red-600 bg-red-50', experience: 'text-blue-600 bg-blue-50',
  rule_candidate: 'text-purple-600 bg-purple-50', tuning_record: 'text-cyan-600 bg-cyan-50',
  customer_pref: 'text-orange-600 bg-orange-50',
}

export function InsightsPage() {
  const [filter, setFilter] = useState('all')
  const [candidates, setCandidates] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [stats, setStats] = useState({ all: 0, draft: 0, pending_review: 0, verified: 0, invalid: 0 })

  const load = async () => {
    setLoading(true)
    try {
      const params = filter !== 'all' ? { status: filter } : {}
      const data = await api.getCandidates({ ...params, size: 100 })
      setCandidates(data.items || [])
      setTotal(data.total || 0)

      // Calculate stats
      const s = { all: 0, draft: 0, pending_review: 0, verified: 0, invalid: 0 }
      // We'd need a separate call for stats, use current data as approximation
      setStats({ ...s, all: data.total || 0 })
    } catch (err) {
      console.error('Insights error:', err)
    }
    setLoading(false)
  }

  useEffect(() => { load() }, [filter])

  const updateCandidate = async (id, status) => {
    try {
      await api.updateCandidate(id, { status, reviewed_by: '管理员' })
      await load()
    } catch (err) {
      alert('操作失败: ' + err.message)
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">经验沉淀</h1>

      {/* Filter tabs */}
      <div className="flex gap-2">
        {[
          { key: 'all', label: '全部' },
          { key: 'draft', label: '草稿' },
          { key: 'pending_review', label: '待审' },
          { key: 'verified', label: '已确认' },
          { key: 'invalid', label: '无效' },
        ].map(f => (
          <button key={f.key}
            onClick={() => setFilter(f.key)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${filter === f.key ? 'bg-blue-600 text-white' : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'}`}
          >
            {f.label} {f.key === 'all' && total > 0 ? `(${total})` : ''}
          </button>
        ))}
      </div>

      {/* Loading */}
      {loading && <div className="flex items-center justify-center h-32 text-gray-400">加载中...</div>}

      {/* Empty */}
      {!loading && candidates.length === 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center text-gray-400">
          提交回答后，经验候选将在这里显示
        </div>
      )}

      {/* Results */}
      {!loading && candidates.length > 0 && (
        <div className="space-y-3">
          {candidates.map(c => (
            <div key={c.id} className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <span className="font-medium text-gray-900">{c.engineer_name}</span>
                  <span className="text-sm text-gray-400">{c.session_date}</span>
                  <span className={`px-2 py-0.5 rounded text-xs font-medium ${catColor[c.category] || 'text-gray-600 bg-gray-50'}`}>
                    {catLabel[c.category] || c.category}
                  </span>
                </div>
                <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                  c.status === 'verified' ? 'bg-green-100 text-green-700' :
                  c.status === 'pending_review' ? 'bg-yellow-100 text-yellow-700' :
                  c.status === 'invalid' ? 'bg-red-100 text-red-700' :
                  'bg-gray-100 text-gray-600'
                }`}>
                  {c.status === 'draft' ? '草稿' : c.status === 'pending_review' ? '待审' : c.status === 'verified' ? '已确认' : '无效'}
                </span>
              </div>
              <div className="text-sm text-gray-700 mb-3">{c.summary || '无摘要'}</div>
              <div className="flex gap-2">
                {c.status === 'draft' && <>
                  <button onClick={() => updateCandidate(c.id, 'pending_review')}
                    className="px-3 py-1 text-xs border border-blue-300 text-blue-600 rounded hover:bg-blue-50">标记待审</button>
                  <button onClick={() => updateCandidate(c.id, 'invalid')}
                    className="px-3 py-1 text-xs border border-red-300 text-red-600 rounded hover:bg-red-50">无效</button>
                </>}
                {c.status === 'pending_review' && <>
                  <button onClick={() => updateCandidate(c.id, 'verified')}
                    className="px-3 py-1 text-xs border border-green-300 text-green-600 rounded hover:bg-green-50">确认有效</button>
                  <button onClick={() => updateCandidate(c.id, 'invalid')}
                    className="px-3 py-1 text-xs border border-red-300 text-red-600 rounded hover:bg-red-50">无效</button>
                </>}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
