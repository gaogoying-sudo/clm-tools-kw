import { useState } from 'react'

export function InsightsPage() {
  const [filter, setFilter] = useState('all')

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
            {f.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center text-gray-400">
        提交回答后，经验候选将在这里显示
      </div>
    </div>
  )
}
